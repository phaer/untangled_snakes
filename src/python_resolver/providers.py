import logging
from operator import attrgetter
from platform import python_version

import requests
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

from resolvelib.providers import AbstractProvider

from .distribution import Distribution, UnsupportedFileType
from .candidate import Candidate
from .identifier import Identifier

PYTHON_VERSION = Version(python_version())
log = logging.getLogger(__name__)


def get_project_from_pypi(identifier):
    """Return candidates created from the project name and extras."""
    log.debug(f"gathering candidates for {identifier}")
    url = "https://pypi.org/simple/{}".format(identifier.name)

    response = requests.get(
        url, headers={"Accept": "application/vnd.pypi.simple.v1+json"}
    )
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


class PyPiProvider(AbstractProvider):
    def identify(self, requirement_or_candidate):
        return Identifier.from_requirement(requirement_or_candidate)

    def get_base_requirement(self, candidate):
        return Requirement("{}=={}".format(candidate.name, candidate.version))

    def get_preference(
        self, identifier, resolutions, candidates, information, backtrack_causes
    ):
        return sum(1 for _ in candidates[identifier])

    def find_matches(self, identifier, requirements, incompatibilities):
        requirements = list(requirements[identifier])
        bad_versions = {c.version for c in incompatibilities[identifier]}
        candidates = (
            candidate
            for candidate in get_project_from_pypi(identifier)
            if candidate.version not in bad_versions
            and all(candidate.version in r.specifier for r in requirements)
        )
        return sorted(candidates, key=attrgetter("version"), reverse=True)

    def is_satisfied_by(self, requirement, candidate):
        if canonicalize_name(requirement.name) != candidate.name:
            return False
        # if requirement.extras not in candidate.extras:
        #    return False
        return candidate.version in requirement.specifier

    def get_dependencies(self, candidate):
        deps = candidate.dependencies
        # if candidate.extras:
        #    req = self.get_base_requirement(candidate)
        #    deps.append(req)
        return deps
