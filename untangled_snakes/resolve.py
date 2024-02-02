import os
import logging
import json
import subprocess
import tarfile
from pathlib import Path
from base64 import b16decode, b64encode
from typing import Iterable

import tomli
from pdm.core import Core, Project
from pdm.environments import BaseEnvironment, PythonEnvironment
from pdm.cli.filters import GroupSelection
from pdm.cli.actions import resolve_candidates_from_lockfile
from pdm.models.requirements import Requirement


# https://github.com/pypa/packaging/blob/4d8534061364e3cbfee582192ab81a095ec2db51/src/packaging/utils.py#L146
# suggests this should be good enough in practice?
SDIST_SUFFIXES = [".tar.gz", ".zip"]


def main():
    logging.getLogger("unearth").setLevel(logging.INFO)

    pdm = Core()
    project_root = "./templates/app"  # TODO cli arg
    project: Project = pdm.create_project(project_root)
    environment = PythonEnvironment(
        project,
        # TODO pass python interpreter from nix
        python="/etc/profiles/per-user/phaer/bin/python",
    )

    candidates = resolve_sdists(project, environment)
    build_requirements = {}

    for candidate in candidates:
        # TODO check if in nixpkgs before fetching

        nix_hash = convert_python_hash(find_candidate_sdist_hash(candidate))
        nix_source = nix_prefetch(candidate.link.url, nix_hash)
        store_path = nix_source.get("storePath")
        build_requirements[candidate.name] = build_requirements_from_sdist(store_path)

    from pprint import pprint

    pprint(candidates)
    pprint(build_requirements)


def convert_python_hash(python_hash: str) -> str:
    "python encodes hashes in base16, while nix uses b64"
    typ, data = python_hash.split(":")
    nix_hash = b64encode(b16decode(data.upper())).decode("utf-8")
    return f"{typ}-{nix_hash}"


def find_candidate_sdist_hash(candidate):
    """
    Find the (sha256) hash of the given candiates sdist.
    """
    maybe_hashes = [
        h
        for h in candidate.hashes
        if any([h.get("url", "").endswith(suffix) for suffix in SDIST_SUFFIXES])
    ]
    assert (
        len(maybe_hashes) == 1
    ), f"Expected only one source distribution, but found {len(maybe_hashes)}"
    return maybe_hashes[0].get("hash")


def resolve_sdists(
    project: Project,
    environment: BaseEnvironment,
    extra_requirements: Iterable[Requirement] = [],
):
    """
    Resolve all dependencies of the given project, just as pdm to does, but
    force it to use sdists for everthing, as wheels typically do not include
    pyproject.toml.

    Also accepts extra_requirements to narrow dependency constraints
    """
    os.environ["PDM_NO_BINARY"] = ":all:"  # TODO: no config option for this?
    groups = GroupSelection(project)  # FIXME group selection via cli

    requirements = []
    groups.validate()
    for group in groups:
        requirements.extend(project.get_dependencies(group).values())
    requirements.extend(extra_requirements)

    candidates = resolve_candidates_from_lockfile(
        project, cross_platform=True, requirements=requirements
    )

    result = []
    for name, candidate in candidates.items():
        candidate.prepare(environment)
        candidate.prepared.obtain(unpack=False)
        result.append(candidate)
    return result


def nix_prefetch(url, expected_hash=None):
    """
    Let nix download the given url, write it to the nix store and
    compare the hashes, if given.
    """
    proc = subprocess.run(
        [
            "nix",
            "store",
            "prefetch-file",
            "--hash-type",
            "sha256",
            "--json",
            url,
        ],
        check=True,
        capture_output=True,
    )
    nix_out = json.loads(proc.stdout)
    nix_hash = nix_out.get("hash")
    if expected_hash:
        assert (
            expected_hash == nix_hash
        ), f"hash mismatch for {url}:\nfound: {nix_hash}\nexpected: {expected_hash}"
    return nix_out


def build_requirements_from_sdist(store_path: Path):
    """
    Extracts build-system.requires and .build-backend
    from pyproject.toml file, stored in a sdist, unpacked
    in the nix store.
    """
    with tarfile.open(store_path, "r") as tar:
        # Reuse name from the sdists filename, not candidate name
        # because the latter is normalized to lowercase.
        directory = store_path.split("-", 1)[1]
        for suffix in SDIST_SUFFIXES:
            directory = directory.removesuffix(suffix)
        filename = f"{directory}/pyproject.toml"
        if filename in tar.getnames():
            pyproject_toml = tar.extractfile(filename)
            pyproject = tomli.load(pyproject_toml)
            build_system = pyproject.get("build-system", {})
            if build_system.get("build-backend", None):
                return {
                    k: v
                    for k, v in build_system.items()
                    if k in ["requires", "build-backend"]
                }
        return {
            "build-system": {
                "requires": ["setuptools"],
                "build-backend": "setuptools.build_meta:__legacy__",
            }
        }


if __name__ == '__main__':
    main()
