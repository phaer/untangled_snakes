{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
  };

  outputs = inputs @ {flake-parts, ...}:
    flake-parts.lib.mkFlake {inherit inputs;} {
      imports = [
        inputs.devenv.flakeModule
      ];
      systems = ["x86_64-linux" "aarch64-darwin"];

      perSystem = {
        config,
        self',
        inputs',
        pkgs,
        system,
        ...
      }: {
        packages.default = config.packages.untangled_snakes;
        packages.untangled_snakes = let
          python = config.packages.python;
        in
          python.pkgs.buildPythonPackage {
            name = "untangled_snakes";
            format = "pyproject";
            src = ./src;
            nativeBuildInputs = [
              python.pkgs.setuptools
              python.pkgs.pytestCheckHook
            ];
            propagatedBuildInputs = [
              python.pkgs.packaging
              python.pkgs.resolvelib
              python.pkgs.requests
              python.pkgs.requests-mock
            ];
          };
        packages.python = let
          packageOverrides = self: super: {
            resolvelib = super.resolvelib.overridePythonAttrs (old: rec {
              version = "1.0.1";
              doCheck = false;
              src = super.fetchPypi {
                pname = "resolvelib";
                inherit version;
                hash = "sha256-BM52y9Y/3tIHjOIkeF2m7NQrlWSxOQeT9k3ey+mXswk=";
              };
            });
            # FIXME: just wait for https://github.com/NixOS/nixpkgs/pull/243349
            # and use parse_metadata then
            #packaging = super.packaging.overridePythonAttrs(old: rec {
            #  version = "23.1";
            #  src = super.fetchPypi {
            #    pname = "packaging";
            #    inherit version;
            #    hash = "sha256-o5KYDSts/6ZEQxiYvlSwBFFRMZ0efsNPDP7Uh2fdM08=";
            #  };
            #});
          };
        in
          pkgs.python3.override {
            inherit packageOverrides;
            self = pkgs.python3;
          };

        packages.devPython = config.packages.python.withPackages (
          ps:
            config.packages.default.propagatedBuildInputs
            ++ [
              ps.black
              ps.pytest
              ps.pytest-cov
              ps.ipython
              ps.python-lsp-server
            ]
        );

        devenv.shells.default = {
          # https://devenv.sh/reference/options/
          languages.python = {
            enable = true;
            package = config.packages.devPython;
          };

          pre-commit.hooks = {
            black.enable = true;
            ruff.enable = true;
            alejandra.enable = true;
          };

          packages = [
            pkgs.ruff
          ];
          enterShell = ''
          '';
        };
      };
    };
}
