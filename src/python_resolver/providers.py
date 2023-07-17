from operator import attrgetter

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from resolvelib.providers import AbstractProvider

from .identifier import Identifier


class PyPiProvider(AbstractProvider):
    def __init__(self, finder):
        self.finder = finder

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
            for candidate in self.finder.find_candidates(identifier)
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
