from packaging.utils import canonicalize_name


class Identifier:
    def __init__(self, name, extras=()):
        self.name = name
        self.extras = extras

    @classmethod
    def from_requirement(cls, requirement_or_candidate):
        return cls(
            canonicalize_name(requirement_or_candidate.name),
            tuple(sorted(requirement_or_candidate.extras)) or tuple(),
        )

    def __eq__(self, other):
        return self.name == other.name and self.extras == other.extras

    def __hash__(self):
        return hash((self.name, self.extras))

    def __repr__(self):
        e = ",".join(self.extras)
        return f"{self.name}[{e}]"
