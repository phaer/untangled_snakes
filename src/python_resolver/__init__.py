import argparse
import logging
import json

import resolvelib
from packaging.requirements import Requirement

from .distribution import Distribution, UnsupportedFileType
from .metadata import fetch_metadata
from .providers import Identifier, PyPiProvider
from .finders import SimpleIndexFinder


__all__ = [Identifier, Distribution, UnsupportedFileType, PyPiProvider, SimpleIndexFinder, fetch_metadata]


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-r", "--requirements-list", action="append", default=[])

logging.basicConfig(level=logging.INFO)


def generate_lock(result):
    target = dict()
    for package, dependency in result.graph.iter_edges():
        if dependency.name not in target:
            target[dependency.name] = []
        if not package:
            # this edge is from None to a root package
            print("root found")
            continue
        target[package.name].append(dependency.name)

    return {
        "sources": {
            identifier.name: {
                "url": candidate.url,
                "sha256": candidate.sha256,
                "version": str(candidate.version),
            }
            for identifier, candidate in result.mapping.items()
        },
        "targets": {"default": target},
    }


def resolve(requirements):
    finder = SimpleIndexFinder()
    provider = PyPiProvider(finder)
    reporter = resolvelib.BaseReporter()
    resolver = resolvelib.Resolver(provider, reporter)
    return resolver.resolve(requirements)


def main():
    args = arg_parser.parse_args()
    requirements = [Requirement(r) for r in args.requirements_list]
    result = resolve(requirements)
    lock = generate_lock(result)
    print(json.dumps(lock, indent=2))


if __name__ == "__main__":
    main()
