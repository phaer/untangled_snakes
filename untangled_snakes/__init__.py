import argparse
import logging
import json

import resolvelib
from packaging.requirements import Requirement

from .distribution import Distribution, UnsupportedFileType
from .metadata import fetch_metadata
from .providers import Identifier, PyPiProvider
from .finders import SimpleIndexFinder
from .app_context import AppContext
from .test_cases import start_test_case, finish_test_case
from .reporters import DebugReporter

__all__ = [
    "Identifier",
    "Distribution",
    "UnsupportedFileType",
    "PyPiProvider",
    "SimpleIndexFinder",
    "AppContext",
    "fetch_metadata",
    "main",
    "resolve",
]


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-r", "--requirements-list", action="append", default=[])
arg_parser.add_argument("--record-test-case")

logging.basicConfig(level=logging.INFO)


def generate_lock(result):
    target = dict()
    for package, dependency in result.graph.iter_edges():
        if dependency.name not in target:
            target[dependency.name] = []
        if package is None:
            # this edge is from None to a root package
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
        "targets": {"default": {k: sorted(v) for k, v in target.items()}},
    }


def resolve(app_context, requirements):
    finder = SimpleIndexFinder(app_context)
    provider = PyPiProvider(finder)
    reporter = DebugReporter()
    resolver = resolvelib.Resolver(provider, reporter)
    return resolver.resolve(requirements)


def main():
    args = arg_parser.parse_args()
    app_context = AppContext(args.record_test_case)
    requirements = [Requirement(r) for r in args.requirements_list]

    if app_context.record_test_case:
        start_test_case(app_context, requirements)

    result = resolve(app_context, requirements)
    lock = generate_lock(result)

    if app_context.record_test_case:
        finish_test_case(app_context, lock)
    else:
        print(json.dumps(lock, indent=2))


if __name__ == "__main__":
    main()
