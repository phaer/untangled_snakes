import logging
from platform import python_version

import requests
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet

from .distribution import Distribution, UnsupportedFileType
from .candidate import Candidate
from .test_cases import record_index

PYTHON_VERSION = Version(python_version())
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class SimpleIndexFinder:
    def __init__(self, app_context, index_url="https://pypi.org/simple"):
        self.index_url = index_url
        self.session = requests.Session()
        self.cache = dict()
        self.app_context = app_context

    def find_candidates(self, identifier):
        """Return candidates created from the project name and extras."""
        if identifier in self.cache:
            log.debug(
                f"reusing cached candidates for {identifier} from {self.index_url}"
            )
            for candidate in self.cache[identifier]:
                yield candidate
            return

        self.cache[identifier] = []
        log.debug(f"gathering candidates for {identifier} from {self.index_url}")
        url = f"{self.index_url}/{identifier.name}"

        response = self.session.get(
            url, headers={"Accept": "application/vnd.pypi.simple.v1+json"}
        )
        response.raise_for_status()
        data = response.json()
        if self.app_context.record_test_case:
            record_index(self.app_context, identifier, data)

        for link in data.get("files", []):
            url = link["url"]
            sha256 = link.get("hashes", {}).get("sha256")
            try:
                distribution = Distribution(link["filename"])
            except UnsupportedFileType:
                logging.info(
                    f"skipping {link['filename']} as file format is not supported"
                )
                continue
            except InvalidVersion as e:
                logging.info(f"skipping {link['filename']} because of {e}")
                continue

            # Skip items that need a different Python version
            requires_python = link.get("requires-python")
            if requires_python:
                spec = SpecifierSet(requires_python)
                if PYTHON_VERSION not in spec:
                    continue

            candidate = Candidate(
                self.app_context,
                distribution,
                url=url,
                sha256=sha256,
                extras=identifier.extras,
            )
            self.cache[identifier].append(candidate)
            yield candidate
