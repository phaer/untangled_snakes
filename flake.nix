{
  outputs = { self, nixpkgs }: let
    system = "aarch64-darwin";
    lib = nixpkgs.lib;
    pkgs = nixpkgs.legacyPackages.${system};
    python = let
      packageOverrides = self: super: {
        resolvelib = super.resolvelib.overridePythonAttrs(old: rec {
          version = "1.0.1";
          doCheck = false;
          src = super.fetchPypi {
            pname = "resolvelib";
            inherit version;
            hash = "sha256-BM52y9Y/3tIHjOIkeF2m7NQrlWSxOQeT9k3ey+mXswk=";
          };
        });
        #packaging = super.packaging.overridePythonAttrs(old: rec {
        #  version = "23.1";
        #  src = super.fetchPypi {
        #    pname = "packaging";
        #    inherit version;
        #    hash = "sha256-o5KYDSts/6ZEQxiYvlSwBFFRMZ0efsNPDP7Uh2fdM08=";
        #  };
        #});
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
        python.pkgs.resolvelib
        python.pkgs.requests
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
        ps.python-lsp-server
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
