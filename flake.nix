{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";

    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs @ {flake-parts, ...}:
    flake-parts.lib.mkFlake {inherit inputs;} {
      imports = [
        inputs.treefmt-nix.flakeModule
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
          inherit (config.packages) python;
        in
          python.pkgs.buildPythonPackage {
            name = "untangled_snakes";
            pyproject = true;
            src = pkgs.lib.cleanSource ./.;
            nativeBuildInputs = [
              python.pkgs.setuptools
            ];
            propagatedBuildInputs = [
              python.pkgs.requests
              python.pkgs.rich
            ];
          };
        packages.python = pkgs.python3;
        packages.devPython = config.packages.python.withPackages (
          ps:
            config.packages.default.propagatedBuildInputs
            ++ [
              ps.pytest
              ps.pytest-cov
              ps.ipython
              ps.python-lsp-server
            ]
        );

        treefmt = {
          projectRootFile = "flake.lock";

          # Shell
          programs.shellcheck.enable = true;

          # Nix
          programs.deadnix.enable = true;
          programs.statix.enable = true;
          programs.alejandra.enable = true;

          # Python
          programs.black.enable = true;
          programs.ruff.enable = true;
        };
      };
    };
}
