import logging
from email.parser import BytesParser
from io import BytesIO
from pathlib import Path
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import tarfile

import requests
from build.util import project_wheel_metadata
from build import BuildException

log = logging.getLogger(__name__)


class MetadataNotFound(Exception):
    pass


class MetadataPreparationFailed(Exception):
    def __init__(self, exc, candidate):
        super().__init__(f"Metadata preparation for {candidate.url} failed: {exc}")


def fetch_metadata(candidate):
    metadata = metadata_from_pep658(candidate)
    if metadata:
        log.debug(f"Found metadata for {candidate} via pep658")
        return metadata

    response = requests.get(candidate.url)
    response.raise_for_status()
    distribution_file = BytesIO(response.content)

    if candidate.is_wheel:
        where = "wheel"
        metadata = metadata_from_wheel(candidate, distribution_file)
    elif candidate.is_sdist:
        where = "sdist"
        metadata = metadata_from_sdist(candidate, distribution_file)
        if not metadata or candidate.name in candidate.app_context.legacy_metadata:
            logging.warn(
                f"acquiring metadata for {candidate} from "
                f"{candidate.distribution.filename}"
            )
            distribution_file.seek(0)
            with source_tree_from_sdist(candidate, distribution_file) as source_tree:
                try:
                    metadata = project_wheel_metadata(source_tree)
                except BuildException as e:
                    raise MetadataPreparationFailed(e, candidate)

    if metadata:
        log.debug(f"Found metadata for {candidate} in the {where} {candidate.url}")
        return metadata

    raise MetadataNotFound(f"No metadata found for {candidate} ({candidate.url})")


def parse_metadata(fp):
    # FIXME packaging.metadata.parse_email will be available in 23.1
    # this is wasteful, but i didn't get it to work with content.raw
    # and it should be replaced by packaging 23.1 soon
    return BytesParser().parse(fp, headersonly=True)


def metadata_from_pep658(candidate):
    content = BytesIO(requests.get(f"{candidate.url}.metadata").content)
    return parse_metadata(content)


def metadata_from_wheel(candidate, distribution_file):
    with ZipFile(distribution_file) as zip:
        try:
            return parse_metadata(zip.open(candidate.distribution.metadata_path))
        except KeyError:
            pass


def metadata_from_sdist(candidate, distribution_file):
    with tarfile.open(
        candidate.distribution.filename, fileobj=distribution_file
    ) as tar:
        try:
            return parse_metadata(tar.extractfile(candidate.distribution.metadata_path))
        except KeyError:
            pass


@contextmanager
def source_tree_from_sdist(candidate, distribution_file):
    filename = candidate.distribution.filename
    name_underscore = candidate.name.replace("-", "_")
    search_dirs = [
        f"{candidate.name}-{candidate.version}",
        f"{name_underscore}-{candidate.version}",
    ]
    distribution_file.seek(0)
    with tarfile.open(filename, fileobj=distribution_file) as tar, TemporaryDirectory(
        suffix=f"metadata-preparation-{filename}"
    ) as temp_dir:
        tar.extractall(temp_dir, filter="data")
        temp_dir = Path(temp_dir)

        for search_dir in search_dirs:
            if (temp_dir / search_dir).exists():
                temp_dir = temp_dir / search_dir

        yield temp_dir
