from packaging.requirements import Requirement

from untangled_snakes import (
    Identifier,
    generate_lock,
)


def test_requests(load_case, resolver):
    inputs, expected_lock = load_case("requests-socks")
    requirements = [Requirement(r) for r in inputs.get("requirements")]
    result = resolver.resolve(requirements)
    assert Identifier("certifi") in result.mapping
    assert Identifier("PySocks") not in result.mapping

    assert expected_lock == generate_lock(result)


# def test_resolve_requests(resolver):
#    requirements = [Requirement("requests")]
#    result = resolver.resolve(requirements)
#    assert Identifier("certifi") in result.mapping
#    assert Identifier("PySocks") not in result.mapping
#
#
# def test_resolve_requests_extra(resolver):
#    requirements = [Requirement("requests[socks]")]
#    result = resolver.resolve(requirements)
#    assert Identifier("pysocks") in result.mapping
