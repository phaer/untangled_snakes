from packaging.requirements import Requirement
from .metadata import fetch_metadata
from .test_cases import record_metadata


class Candidate:
    def __init__(self, settings, distribution, url=None, sha256=None, extras=None):
        self.settings = settings
        self.distribution = distribution
        self.url = url
        self.sha256 = sha256
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
            if self.settings.record_test_case:
                record_metadata(
                    self.settings, self.distribution.filename, self._metadata
                )
        return self._metadata

    @property
    def requires_python(self):
        return self.metadata.get("Requires-Python")

    def _get_dependencies(self):
        deps = self.metadata.get_all("Requires-Dist", [])
        extras = self.extras if self.extras else [""]
        for d in deps:
            r = Requirement(d.replace("\n", " "))
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
