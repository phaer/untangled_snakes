from packaging.utils import (
    parse_wheel_filename,
    parse_sdist_filename,
)


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
            name = self.name.replace("-", "_")
            return f"{name}-{self.version}.dist-info/METADATA"
        else:
            return f"{self.name}-{self.version}/PKG-INFO"
