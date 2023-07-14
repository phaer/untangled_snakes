import logging
from email.parser import BytesParser
from io import BytesIO
from zipfile import ZipFile
import tarfile

import requests

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class MetadataNotFound(Exception):
    pass


def fetch_metadata(candidate):
    metadata = metadata_from_pep658(candidate)
    if metadata:
        log.debug(f"Found metadata for {candidate} via pep658")
        return metadata

    distribution_file = BytesIO(requests.get(candidate.url).content)

    if candidate.is_wheel:
        metadata = metadata_from_wheel(candidate, distribution_file)
        where = "wheel"
    elif candidate.is_sdist:
        metadata = metadata_from_sdist(candidate, distribution_file)
        where = "sdist"

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
