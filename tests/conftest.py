import json
import gzip
from pathlib import Path

import pytest
from resolvelib import Resolver, BaseReporter

from untangled_snakes import (
    PyPiProvider,
    SimpleIndexFinder,
    Settings,
)


class TestReporter(BaseReporter):
    def __init__(self):
        self._indent = 0

    def rejecting_candidate(self, criterion, candidate):
        self._indent -= 1
        print(" " * self._indent, "Reject ", candidate, sep="")

    def pinning(self, candidate):
        print(" " * self._indent, "Pin  ", candidate, sep="")
        self._indent += 1


@pytest.fixture(scope="session")
def reporter_cls():
    return TestReporter


@pytest.fixture()
def reporter(reporter_cls):
    return reporter_cls()


@pytest.fixture
def resolver(reporter):
    settings = Settings()
    finder = SimpleIndexFinder(settings)
    provider = PyPiProvider(finder)
    resolver = Resolver(provider, reporter)
    return resolver


@pytest.fixture
def load_case(requests_mock):
    cases_path = Path("tests/cases")

    def _load_case(name, index_url="https://pypi.org/simple"):
        case_path = cases_path / name

        with open(case_path / "inputs.json", "r") as f:
            inputs = json.load(f)

        with open(case_path / "lock.json", "r") as f:
            lock = json.load(f)

        urls_by_filename = dict()
        for path in case_path.glob("index/*.json.gz"):
            name = path.name.removesuffix("".join(path.suffixes))
            with gzip.open(path, "rt") as f:
                data = json.load(f)
            requests_mock.get(f"{index_url}/{name}", json=data)
            for item in data["files"]:
                urls_by_filename[item["filename"]] = item["url"]

        for path in case_path.glob("metadata/*.metadata.gz"):
            filename = path.name.removesuffix(".metadata.gz")
            with gzip.open(path, "rt") as f:
                data = f.read()
            url = urls_by_filename[filename]
            requests_mock.get(f"{url}.metadata", text=data)

        return (inputs, lock)

    return _load_case
