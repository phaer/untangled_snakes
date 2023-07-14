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
from .metadata import fetch_metadata


PYTHON_VERSION = Version(python_version())
log = logging.getLogger(__name__)


class Candidate:
    def __init__(self, distribution, url=None, hash=None, extras=None):
        self.distribution = distribution
        self.url = url
        self.hash = hash
        self.extras = extras

        self._metadata = None
        self._dependencies = None

    def __repr__(self):
        if not self.extras:
            return f"<{self.name}=={self.version}>"
        return f"<{self.name}[{','.join(self.extras)}]=={self.version}>"

    @property
    def name(self):
        return self.distribution.name

    @property
    def version(self):
        return self.distribution.version

    @property
    def is_wheel(self):
        return self.distribution.is_wheel

    @property
    def is_sdist(self):
        return self.distribution.is_sdist

    @property
    def metadata(self):
        if self._metadata is None:
            self._metadata = fetch_metadata(self)
        return self._metadata

    @property
    def requires_python(self):
        return self.metadata.get("Requires-Python")

    def _get_dependencies(self):
        deps = self.metadata.get_all("Requires-Dist", [])
        extras = self.extras if self.extras else [""]
        for d in deps:
            r = Requirement(d)
            if r.marker is None:
                yield r
            else:
                for e in extras:
                    if r.marker.evaluate({"extra": e}):
                        yield r

    @property
    def dependencies(self):
        if self._dependencies is None:
            self._dependencies = list(self._get_dependencies())
        return self._dependencies


def get_project_from_pypi(identifier):
    """Return candidates created from the project name and extras."""
    log.info(f"gathering candidates for {identifier}")
    url = "https://pypi.org/simple/{}".format(identifier.name)

    response = requests.get(
        url, headers={"Accept": "application/vnd.pypi.simple.v1+json"}
    )
    data = response.json()

    for link in data.get("files", []):
        url = link["url"]
        try:
            distribution = Distribution(link["filename"])
        except UnsupportedFileType as e:
            # silently ignore some uninteresting files
            ext = e.filename.split(".")[-1]
            if ext not in ["egg", "msi", "exe"]:
                logging.info(f"skipping {e.filename} as its format is not supported")
            continue

        # Skip items that need a different Python version
        requires_python = link.get("data-requires-python")
        if requires_python:
            spec = SpecifierSet(requires_python)
            if PYTHON_VERSION not in spec:
                continue

        yield Candidate(
            distribution,
            url=url,
            hash=None,
            extras=identifier.extras,
        )


class Identifier:
    def __init__(self, requirement_or_candidate):
        self.name = canonicalize_name(requirement_or_candidate.name)
        self.extras = tuple(sorted(requirement_or_candidate.extras)) or tuple()

    def __repr__(self):
        e = ",".join(self.extras)
        return f"{self.name}[{e}]"


class PyPiProvider(AbstractProvider):
    def identify(self, requirement_or_candidate):
        return Identifier(requirement_or_candidate)

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
        #if requirement.extras not in candidate.extras:
        #    return False
        return candidate.version in requirement.specifier

    def get_dependencies(self, candidate):
        deps = candidate.dependencies
        #if candidate.extras:
        #    req = self.get_base_requirement(candidate)
        #    deps.append(req)
        return deps
