import re

from packaging.utils import (
    parse_wheel_filename,
    InvalidSdistFilename,
    canonicalize_name,
)
from packaging.version import Version

PACKAGE_VERSION_RE = re.compile(r"(?P<name>.*)-(?P<version>\d+\..*)")


# FIXME: We temporarily implement this ourselves, because upstreams
# version is too naive atm, see https://github.com/pypa/packaging/issues/703
# As long as name and version are separated by "-" and the name does not
# include a ".", the regex above should work
def parse_sdist_filename(filename):
    if not filename.endswith(".tar.gz"):
        raise InvalidSdistFilename(
            f"Invalid sdist filename (extension must be '.tar.gz' or '.zip'):"
            f" {filename}"
        )
    filename = filename.removesuffix(".tar.gz")
    match = PACKAGE_VERSION_RE.match(filename)
    if not match:
        raise InvalidSdistFilename(f"Invalid sdist filename: {filename}")
    name = canonicalize_name(match.group("name"))
    version = Version(match.group("version"))
    return name, version


class InvalidDistribution(Exception):
    pass


class UnsupportedFileType(InvalidDistribution):
    def __init__(self, filename):
        self.filename = filename
        super().__init__(f"Unsupported package file: {self.filename}")


class Distribution:
    def __init__(self, filename):
        self.filename = filename

        if self.is_wheel:
            self.name, self.version, self.build, self.tags = parse_wheel_filename(
                filename
            )
        elif self.is_sdist:
            self.name, self.version = parse_sdist_filename(filename)
        else:
            raise UnsupportedFileType(self.filename)

    @property
    def is_wheel(self):
        return self.filename.endswith(".whl")

    @property
    def is_sdist(self):
        return self.filename.endswith(".tar.gz")

    @property
    def metadata_path(self):
        if self.is_wheel:
            distribution = self.filename.split("-")[0]
            return f"{distribution}-{self.version}.dist-info/METADATA"
        else:
            return f"{self.name}-{self.version}/PKG-INFO"
