import logging
from platform import python_version

import requests
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from .distribution import Distribution, UnsupportedFileType
from .candidate import Candidate

PYTHON_VERSION = Version(python_version())
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class SimpleIndexFinder:
    def __init__(self, index_url="https://pypi.org/simple"):
        self.index_url = index_url
        self.session = requests.Session()

    def find_candidates(self, identifier):
        """Return candidates created from the project name and extras."""
        log.debug(f"gathering candidates for {identifier} from {self.index_url}")
        url = "/".join([self.index_url, identifier.name])

        response = self.session.get(
            url, headers={"Accept": "application/vnd.pypi.simple.v1+json"}
        )
        response.raise_for_status()
        data = response.json()

        for link in data.get("files", []):
            url = link["url"]
            sha256 = link.get("hashes", {}).get("sha256")
            try:
                distribution = Distribution(link["filename"])
            except UnsupportedFileType as e:
                logging.debug(f"skipping {e.filename} as file format is not supported")
                continue

            # Skip items that need a different Python version
            requires_python = link.get("requires-python")
            if requires_python:
                spec = SpecifierSet(requires_python)
                if PYTHON_VERSION not in spec:
                    continue

            yield Candidate(
                distribution,
                url=url,
                sha256=sha256,
                extras=identifier.extras,
            )
