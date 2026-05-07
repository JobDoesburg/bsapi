{
  description = "Basic Python wrapper for the D2LValence Brightspace API";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;
        pyproject = pkgs.lib.fromTOML (builtins.readFile ./pyproject.toml);
      in
      {
        packages.default = python.pkgs.buildPythonPackage {
          pname = pyproject.project.name;
          version = pyproject.project.version;
          format = "pyproject";

          src = self;

          nativeBuildInputs = with python.pkgs; [
            setuptools
          ];

          propagatedBuildInputs = with python.pkgs; [
            requests
          ];

          pythonImportsCheck = [ "bsapi" ];

          meta = with pkgs.lib; {
            description = pyproject.project.description;
            homepage = "https://pypi.org/project/brightspace-api/";
            license = licenses.mit;
            maintainers = [
              {
                name = "Mark Boute";
                github = "mark-boute";
                email = "mark.boute@ru.nl";
              }
            ];
          };
        };

        devShells.default = pkgs.mkShell {

          inputsFrom = [ self.packages.${system}.default ];

          buildInputs = [
            (python.withPackages (ps: [
              ps.black
            ]))
          ];
        };
      }
    );
}
