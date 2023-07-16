from packaging.requirements import Requirement
from resolvelib import Resolver

from python_resolver import Identifier, PyPiProvider


def test_resolve_requests(reporter):
    requirements = [Requirement("requests")]
    provider = PyPiProvider()
    resolver = Resolver(provider, reporter)
    result = resolver.resolve(requirements)
    assert Identifier("certifi") in result.mapping
    assert Identifier("PySocks") not in result.mapping


def test_resolve_requests_extra(reporter):
    requirements = [Requirement("requests[socks]")]
    provider = PyPiProvider()
    resolver = Resolver(provider, reporter)
    result = resolver.resolve(requirements)
    assert Identifier("pysocks") in result.mapping
