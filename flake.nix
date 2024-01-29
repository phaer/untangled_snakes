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

    python-nix.url = "github:tweag/python-nix";
    python-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs @ {
    flake-parts,
    pyproject-nix,
    python-nix,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      imports = [
        inputs.treefmt-nix.flakeModule
      ];
      systems = ["x86_64-linux" "aarch64-darwin"];

      perSystem = {
        pkgs,
        system,
        ...
      }: let
        project = pyproject-nix.lib.project.loadPyproject {
          projectRoot = ./.;
        };
        python = let
          packageOverrides = _self: _super: {
            python-nix = python-nix.packages.${system}.default;
          };
        in
          pkgs.python3.override {
            inherit packageOverrides;
            self = python;
          };
      in {
        devShells.default = let
          arg = project.renderers.withPackages {inherit python;};
          pythonEnv = python.withPackages arg;
        in
          pkgs.mkShell {
            packages = [pythonEnv];
          };

        packages.default = let
          attrs = project.renderers.buildPythonPackage {inherit python;};
        in
          python.pkgs.buildPythonPackage (attrs
            // {
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
