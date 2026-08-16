{
  description = "Pull-and-run NixOS config for a Hermes-centered personal knowledge coordinator";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    hermes-agent = {
      url = "github:NousResearch/hermes-agent";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, hermes-agent, ... } @ inputs:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      pkcPython = pkgs.python312.withPackages (ps: with ps; [ pytest psycopg ]);
      pkcEnv = ''
        export PYTHONPATH=${self}/src:$PYTHONPATH
      '';
    in
    {
      packages.${system} = {
        pkc-cli = pkgs.writeShellApplication {
          name = "pkc";
          runtimeInputs = [ pkcPython ];
          text = ''
            ${pkcEnv}
            exec python -m pkc.cli "$@"
          '';
        };
        pkc-server = pkgs.writeShellApplication {
          name = "pkc-server";
          runtimeInputs = [ pkcPython ];
          text = ''
            ${pkcEnv}
            exec python -m pkc.server "$@"
          '';
        };
        default = self.packages.${system}.pkc-cli;
      };

      apps.${system} = {
        pkc = {
          type = "app";
          program = "${self.packages.${system}.pkc-cli}/bin/pkc";
        };
        pkc-server = {
          type = "app";
          program = "${self.packages.${system}.pkc-server}/bin/pkc-server";
        };
        default = self.apps.${system}.pkc;
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [ pkcPython pkgs.postgresql_16 pkgs.sqlite pkgs.ruff pkgs.nixpkgs-fmt pkgs.gh ];
        shellHook = ''
          export PYTHONPATH="$PWD/src:$PYTHONPATH"
        '';
      };

      checks.${system} = {
        unit-tests = pkgs.runCommand "pkc-unit-tests" { nativeBuildInputs = [ pkcPython ]; } ''
          cp -R ${self} src
          chmod -R u+w src
          cd src
          export PYTHONPATH=$PWD/src
          python -m pytest -q
          touch $out
        '';
        nix-format = pkgs.runCommand "pkc-nix-format" { nativeBuildInputs = [ pkgs.nixpkgs-fmt ]; } ''
          cd ${self}
          nixpkgs-fmt --check flake.nix nixos
          touch $out
        '';
      };

      nixosModules.personal-knowledge-coordinator = import ./nixos/modules/personal-knowledge-coordinator.nix { inherit self inputs; };

      nixosConfigurations.knowledge-node = nixpkgs.lib.nixosSystem {
        inherit system;
        specialArgs = { inherit inputs self; };
        modules = [
          ./nixos/hosts/knowledge-node/configuration.nix
        ];
      };
    };
}
