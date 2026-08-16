{
  description = "Personal knowledge coordinator prototype for Hermes Agent";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      python = pkgs.python312.withPackages (ps: with ps; [ pytest ]);
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = [ python pkgs.postgresql_16 pkgs.sqlite pkgs.ruff ];
        shellHook = ''
          export PYTHONPATH="$PWD/src:$PYTHONPATH"
        '';
      };
    };
}
