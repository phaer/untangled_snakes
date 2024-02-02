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

    pdm2nix.url = "github:adisbladis/pdm2nix";
    pdm2nix.inputs.pyproject-nix.follows = "pyproject-nix";
    pdm2nix.inputs.nixpkgs.follows = "nixpkgs";

    python-nix.url = "github:tweag/python-nix";
    python-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs @ {
    nixpkgs,
    flake-parts,
    pyproject-nix,
    python-nix,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} ({self, ...}: {
      # Currently tested systems are Linux on x86_64 and macOS on arm.
      systems = ["x86_64-linux" "aarch64-darwin"];
      # treefmt allows us to do liniting with 'nix fmt' and to require it in
      # 'nix flake check', see perSystem.treefmt below for config
      imports = [
        inputs.treefmt-nix.flakeModule
      ];

      flake.lib = {
        # Re-exporting libraries here is useful during nix development,
        # as they can be quickly accessed in a 'nix repl', after ':lf .',
        # via 'lib' or 'outputs.lib'.
        nixpkgs = nixpkgs.lib;
        pyproject = pyproject-nix.lib;

        # We could use 'projectRoot = ./.;' here, but that would mean
        # that the input for our python environment would change every
        # time any file in our git repo changes, and trigger a rebuild.
        # So we filter the files using 'nixpkgs.lib.fileset' and
        # copy them to a dedicated storePath.
        projectRoot = let
          fs = nixpkgs.lib.fileset;
        in
          fs.toSource {
            root = ./.;
            fileset =
              # fs.traceVal  # remove the first '#' to get a trace
              # of the resulting store path and it's content
              fs.difference
              (fs.fromSource (nixpkgs.lib.sources.cleanSource ./.))
              (fs.unions [
                (fs.fileFilter (file: file.hasExt "nix") ./.)
                (fs.maybeMissing ./result)
                (fs.maybeMissing ./flake.lock)
                (fs.maybeMissing ./.gitignore)
                (fs.maybeMissing ./.envrc)
              ]);
          };

        # Load pyproject.toml metadata from the root directory of the
        # this flake, after copying that to the nix store.
        project = self.lib.pyproject.project.loadPyproject {
          inherit (self.lib) projectRoot;
        };

        nonMatchingDependencies = python:
          self.lib.pyproject.validators.validateChecks {
            inherit (self.lib) project;
            inherit python;
          };
      };

      perSystem = {
        self',
        lib,
        pkgs,
        system,
        ...
      }: let
        args = {
          # A python interpreter taken from our flake outputs, or straight from pkgs.python3.
          inherit (self'.packages) python;
          # Our project as represented by pyproject-nix and loaded above.
          inherit (self.lib) project;
        };
        withPackagesArgs =
          self.lib.pyproject.renderers.withPackages
          (args
            // {
              extras = ["dev"];
            });
        pythonEnv = args.python.withPackages withPackagesArgs;

        buildPythonPackageArgs =
          self.lib.project.renderers.buildPythonPackage args;
        pythonApp = args.python.pkgs.buildPythonPackage (lib.traceVal buildPythonPackageArgs);
      in {
        devShells.default = pkgs.mkShell {
          packages = [pythonEnv];
        };

        packages = {
          default = pythonApp;
          untangled_snakes = pythonApp;

          python = pkgs.python3.override {
            self = pkgs.python3;
            packageOverrides = self: _super: {
              # python-nix currently uses a bundled, unreleased branch of nix with a
              # stable external api. So we just include from its flake here.
              # It's only used for development and the CLI atm, you don't need
              # need the bundled nix to build a package.
              python-nix = python-nix.packages.${system}.default;
              # pdm is exposed as a toplevel package (pkgs.pdm) in nixpkgs,
              # but exposes all required python attributes, so we add it
              # to our package set here, as we need it for resolving.
              pdm = self.toPythonModule pkgs.pdm;
            };
          };
        };

        #checks = import ./checks.nix {
        #  inherit pkgs lib;
        #  inherit (self.lib) pyproject;
        #};

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
    });
}
