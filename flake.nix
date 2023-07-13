{
  outputs = { self, nixpkgs }: let
    system = "aarch64-darwin";
    lib = nixpkgs.lib;
    pkgs = nixpkgs.legacyPackages.${system};
    python = let
      packageOverrides = self: super: {
        unearth = super.unearth.overridePythonAttrs(old: rec {
          version = "0.0.0";
          src = pkgs.fetchFromGitHub {
            owner = "frostming";
            repo = "unearth";
            rev = "992e637e9a67dfbc8706fc98a51833b588310da8";
            hash = "sha256-yenCjwhGUA70IrfT80ptkWvlMknWA90bL4g6ds374Z8=";
          };
          nativeBuildInputs = [python.pkgs.pdm-backend];
        });
      };
    in pkgs.python3.override {inherit packageOverrides; self = pkgs.python3;};

    package = python.pkgs.buildPythonPackage {
      name = "resolver_test";
      format = "pyproject";
      src = ./src;
      nativeBuildInputs = [
        python.pkgs.setuptools
        #python.pkgs.pytestCheckHook
      ];
      propagatedBuildInputs = [
        python.pkgs.packaging
        python.pkgs.unearth
      ];
    };

    devPython = python.withPackages (
      ps:
      package.propagatedBuildInputs
      ++ [
        ps.black
        ps.pytest
        ps.pytest-cov
        ps.ipython
        ps.unearth
      ]
    );
    devShell = pkgs.mkShell {
      packages = [
       devPython
      ];
    };
  in {
    packages.${system}.default = package;
    devShells.${system}.default = devShell;
  };
}
