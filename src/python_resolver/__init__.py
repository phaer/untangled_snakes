import argparse
import logging

import resolvelib
from packaging.requirements import Requirement

from .providers import PyPiProvider


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-r", "--requirements-list", action="append", default=[])

logging.basicConfig(level=logging.INFO)


def display_resolution(result):
    """Print pinned candidates and dependency graph to stdout."""
    print("\n--- Pinned Candidates ---")
    for name, candidate in result.mapping.items():
        print(f"{candidate.name}: {candidate.url}")

    for package, dependency in result.graph.iter_edges():
        print(f"{package} -> {dependency}")


def main():
    args = arg_parser.parse_args()
    requirements = [Requirement(r) for r in args.requirements_list]

    provider = PyPiProvider()
    reporter = resolvelib.BaseReporter()
    resolver = resolvelib.Resolver(provider, reporter)
    result = resolver.resolve(requirements)
    display_resolution(result)


if __name__ == "__main__":
    main()
