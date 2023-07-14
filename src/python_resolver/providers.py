import sys
import logging
from operator import attrgetter
from platform import python_version
from urllib.parse import urlparse, urldefrag
from collections import namedtuple

import requests
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name, parse_wheel_filename, parse_sdist_filename
from packaging.version import InvalidVersion, Version

from resolvelib import BaseReporter, Resolver
from resolvelib.providers import AbstractProvider


PYTHON_VERSION = Version(python_version())


class Candidate:
    def __init__(self, name, version, url=None, hash=None, extras=None):
        self.name = canonicalize_name(name)
        self.version = version
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
    def metadata(self):
        if self._metadata is None:
            # FIXME packaging.metadata.parse_email will be available in 23.1
            from email.parser import BytesParser
            from io import BytesIO
            response = requests.get(f"{self.url}.metadata")
            self._metadata = BytesParser().parse(BytesIO(response.content), headersonly=True)
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
    logging.info(f'gathering candidates for {identifier}')
    url = "https://pypi.org/simple/{}".format(identifier.name)

    data = requests.get(url, headers={'Accept': "application/vnd.pypi.simple.v1+json"}).json()

    for link in data.get("files", []):
        url = link["url"]
        filename = link["filename"]

#        metadata_hash = link.get('core-metadata')
#        if not metadata_hash:
#            logging.debug(f"skipping {filename}, as there's no pep-658 metadata available")
#            continue

        if filename.endswith(".whl"):
            name, version, _build, _tags = parse_wheel_filename(filename)
        elif filename.endswith(".zip") or filename.endswith(".tar.gz"):
            name, version = parse_sdist_filename(filename)
        else:
            logging.debug(f"skipping {filename}, as it seems to be neither a wheel nor an sdist")
            continue

        # Skip items that need a different Python version
        requires_python = link.get("data-requires-python")
        if requires_python:
            spec = SpecifierSet(requires_python)
            if PYTHON_VERSION not in spec:
                continue

        yield Candidate(name, version, url=url, hash=hash, extras=identifier.extras)


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

    def get_preference(self, identifier, resolutions, candidates, information, backtrack_causes):
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
#        if requirement.extras not in candidate.extras:
#            return False
        return candidate.version in requirement.specifier

    def get_dependencies(self, candidate):
        deps = candidate.dependencies
        #if candidate.extras:
        #    req = self.get_base_requirement(candidate)
        #    deps.append(req)
        return deps
