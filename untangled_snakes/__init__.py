import argparse
import platform
import logging
from typing import Tuple
from pathlib import Path

import nix

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("flake")
logging.basicConfig(level=logging.INFO)


def parse_flake_ref(s: str) -> Tuple[str, str]:
    flake_ref = s
    if "#" not in flake_ref:
        flake_ref += "#"
    flake_path, flake_attr = flake_ref.split("#", 1)
    flake_path = Path(flake_path)
    if not flake_path.is_absolute():
        flake_path = flake_path.absolute()
    return flake_path, flake_attr


def normalize_flake_ref(s: str) -> str:
    return "{}#{}".format(*parse_flake_ref(s))


def get_platform() -> str:
    m = platform.machine()
    s = platform.system().lower()
    if m == "arm64":
        m = "aarch64"
    return f"{m}-{s}"


def main():
    args = arg_parser.parse_args()
    args.flake = normalize_flake_ref(args.flake)

    flake = nix.eval("builtins.getFlake")(args.flake)

    pyproject = flake["inputs"]["pyproject-nix"]["lib"]

    project = pyproject["project"]["loadPyproject"](
        {"projectRoot": Path(".").absolute()}
    )

    platform = get_platform()
    pkgs = flake["inputs"]["nixpkgs"]["legacyPackages"][platform]
    python = pkgs["python3"]

    # dependency_names = [
    #    d["name"].force() for d in project["dependencies"]["dependencies"]
    # ]
    validate_checks = pyproject["validators"]["validateChecks"](
        {"python": python, "project": project}
    )
    print(validate_checks.force())
    try:
        from IPython import embed

        embed()
    except ImportError:
        print("the repl depends on ipython (installed in the dev shell)")


if __name__ == "__main__":
    main()
