{
  description = "Basic Python wrapper for the D2LValence Brightspace API";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;
      in
      {
        packages.default = python.pkgs.buildPythonPackage {
          pname = "brightspace-api";
          version = "2.1.0";
          format = "pyproject";

          src = ./.;

          nativeBuildInputs = with python.pkgs; [
            setuptools
          ];

          propagatedBuildInputs = with python.pkgs; [
            requests
          ];

          pythonImportsCheck = [ "bsapi" ];

          meta = with pkgs.lib; {
            description = "Basic Python wrapper for the D2LValence Brightspace API";
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
          buildInputs = [
            (python.withPackages (ps: [
              self.packages.${system}.default
            ]))
          ];
        };
      });
}
