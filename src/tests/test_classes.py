import pytest

from packaging.requirements import Requirement
from packaging.version import Version, InvalidVersion
from packaging.utils import InvalidWheelFilename
from untangled_snakes import Identifier, Distribution, UnsupportedFileType

identifier_expectations = [
    ("pytest", ("pytest", ())),
    ("pytest[dev]", ("pytest", ("dev",))),
    ("PySocks", ("pysocks", ())),
    ("baz_pkg[foo,bar]", ("baz-pkg", ("bar", "foo"))),
]


@pytest.mark.parametrize("requirement,expected", identifier_expectations)
def test_identifier(requirement, expected):
    identifier = Identifier.from_requirement(Requirement(requirement))
    assert (identifier.name, identifier.extras) == expected


def test_distribution_wheel():
    dist = Distribution("PySocks-1.7.1-py27-none-any.whl")
    assert dist.name == "pysocks"
    assert dist.version == Version("1.7.1")
    assert dist.is_wheel is True
    assert dist.is_sdist is False
    assert dist.metadata_path == "PySocks-1.7.1.dist-info/METADATA"
    assert dist.build == ()
    assert len(dist.tags) == 1
    tag = set(dist.tags).pop()
    assert tag.interpreter == "py27"
    assert tag.abi == "none"
    assert tag.platform == "any"


def test_distribution_sdist():
    dist = Distribution("charset-normalizer-3.2.0.tar.gz")
    assert dist.name == "charset-normalizer"
    assert dist.version == Version("3.2.0")
    assert dist.is_wheel is False
    assert dist.is_sdist is True
    assert dist.metadata_path == "charset-normalizer-3.2.0/PKG-INFO"


def test_broken_and_unsupported():
    with pytest.raises(UnsupportedFileType):
        Distribution("")
    with pytest.raises(UnsupportedFileType):
        Distribution("setuptools-50.0.0.zip")
    with pytest.raises(InvalidWheelFilename):
        Distribution("broken.whl")
    with pytest.raises(InvalidVersion):
        Distribution("html5lib-1.0-reupload.tar.gz")
