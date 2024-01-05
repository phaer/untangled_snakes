{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";

    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";

    pyproject-nix.url = "github:nix-community/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";
    pyproject-nix.inputs.flake-parts.follows = "flake-parts";
    pyproject-nix.inputs.treefmt-nix.follows = "treefmt-nix";
  };

  outputs = inputs @ {flake-parts, pyproject-nix, ...}:
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
      }: let
        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };
        python = pkgs.python3;

      in {

        devShells.default =
          let
            arg = project.renderers.withPackages { inherit python; };
            pythonEnv = python.withPackages arg;
          in
            pkgs.mkShell {
              packages = [ pythonEnv ];
            };

        packages.default =
          let
            attrs = project.renderers.buildPythonPackage { inherit python; };
          in
            python.pkgs.buildPythonPackage (attrs // {
              version = "1.0";
            });

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
