`untangled_snakes` is a python library and command-line utility to resolve a set of python requirements such as `requests[dev]` into a JSON object, representing the dependency tree as well as a list of sdists, wheels and their hashes. Built on [resolvelib](https://github.com/sarugaku/resolvelib) and [packaging](https://packaging.pypa.io/).

As of time of writing, it resolves basic packages and can print a lock-file compatible with [dream2nix's](https://github.com/nix-community/dream2nix/) `fetchPipMetadata`, but does **not yet** handle [platform compatibility markers](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/) correctly and only supports locking for the platform it runs on.

# Motivation

The main reason to write this is that [`pip`](https://pip.pypa.io/) doesn't provide an API. But in order to automatically build python packages in [dream2nix](https://github.com/nix-community/dream2nix/), we need to have a full picture of the dependency tree before we start building.

`pip` recently introduced an optional [installation report](https://pip.pypa.io/en/stable/reference/installation-report/) which we currently use in dream2nix's [`fetchPipMetadata`](https://github.com/nix-community/dream2nix/tree/main/pkgs/fetchPipMetadata) to do the locking. 

While we also need to evaluate extras & platform compatibility there ourselves it works well as long as we stay on one platform. 
But we did not manage to get cross-platform locking, i.e. generating a lock file for `x86_64-linux` on a `aarch64-darwin` machine with this approach. 

# Disclaimer

Still too early to tell whether this experiment will be successful and/or easier than hacking cross-platform dry-run installs
into `pip` in the end. And - as stated above - not ready for general usage yet.

