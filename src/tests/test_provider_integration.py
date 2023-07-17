import pytest
from packaging.requirements import Requirement
from resolvelib import Resolver

from untangled_snakes import Identifier, PyPiProvider, SimpleIndexFinder


@pytest.fixture
def resolver(reporter):
    finder = SimpleIndexFinder()
    provider = PyPiProvider(finder)
    resolver = Resolver(provider, reporter)
    return resolver


def test_resolve_requests(resolver):
    requirements = [Requirement("requests")]
    result = resolver.resolve(requirements)
    assert Identifier("certifi") in result.mapping
    assert Identifier("PySocks") not in result.mapping


def test_resolve_requests_extra(resolver):
    requirements = [Requirement("requests[socks]")]
    result = resolver.resolve(requirements)
    assert Identifier("pysocks") in result.mapping
