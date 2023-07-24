from rich.console import Console
from rich.table import Table
from resolvelib import BaseReporter


class DebugReporter(BaseReporter):
    console = Console()

    def _log(self, *args, **kwargs):
        self.console.log(*args, **kwargs)

    def starting(self):
        self._log("starting resolution")

    def starting_round(self, index):
        self.console.rule(f"[yellow]Started [bold]Round {index}", align="left")

    def ending_round(self, index, state):
        table = Table(title=f"State after Round [bold]#{index}[/]")

        table.add_column("Status")
        table.add_column("Title")
        table.add_column("Type")
        table.add_column("Version")
        table.add_column("Requested By")

        for identifier, criterion in state.criteria.items():
            if identifier in state.mapping:
                candidate = state.mapping[identifier]
                status = ":white_check_mark:"
                if candidate.is_wheel:
                    typ = ":package: wheel"
                else:
                    typ = ":open_file_folder: sdist"
                version = str(candidate.version)
            else:
                status = ":hourglass_not_done:"
                typ = "?"
                version = "?"
            requested_by = ", ".join([p.name for p in criterion.iter_parent() if p])
            table.add_row(status, str(identifier), typ, version, requested_by)

        self._log(table)

    def adding_requirement(self, requirement, parent):
        self._log("add requirement", requirement, "via", parent)

    def resolving_conflicts(self, causes):
        self._log("resolving conflicts:", causes)

    def rejecting_candidate(self, criterion, candidate):
        self._log("rejecting", candidate, "because", criterion)

    def pinning(self, candidate):
        self._log("pinning candidate:", candidate)
