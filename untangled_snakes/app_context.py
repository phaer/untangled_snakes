from pathlib import Path


class AppContext:
    def __init__(self, record_test_case=None, legacy_metadata=[]):
        self.record_test_case = record_test_case
        self.legacy_metadata = legacy_metadata

    @property
    def test_case_path(self):
        if self.record_test_case:
            return Path("tests/cases") / self.record_test_case
