from packaging.requirements import Requirement

from untangled_snakes import (
    Identifier,
    generate_lock,
)


def test_requests(load_case, resolver):
    inputs, expected_lock = load_case("requests-socks")
    requirements = [Requirement(r) for r in inputs.get("requirements")]
    result = resolver.resolve(requirements)
    assert Identifier("requests", ("socks",)) in result.mapping
    assert Identifier("pysocks") in result.mapping
    assert expected_lock == generate_lock(result)


def test_requests_without_socks(load_case, resolver):
    inputs, expected_lock = load_case("requests-socks")
    requirements = [Requirement("requests")]
    result = resolver.resolve(requirements)
    assert Identifier("requests") in result.mapping
    assert (
        Identifier(
            "requests",
            ("socks"),
        )
        not in result.mapping
    )
    assert Identifier("pysocks") not in result.mapping
