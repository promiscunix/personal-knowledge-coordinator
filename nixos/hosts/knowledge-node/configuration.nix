{ config, lib, pkgs, inputs, self, ... }:
{
  imports = [
    self.nixosModules.personal-knowledge-coordinator
    ./hardware-configuration.nix
  ];
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  networking.hostName = "knowledge-node";
  time.timeZone = lib.mkDefault "America/Toronto";

  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  services.openssh.enable = true;

  services.personal-knowledge-coordinator = {
    enable = true;
    stateDir = "/srv/personal-knowledge-coordinator";
    secretsFile = "/etc/pkc/hermes-env";
    databaseName = "pkc";
    databaseUser = "pkc";
    listenHost = "127.0.0.1";
    listenPort = 8765;
    # Change these in your target-machine overlay if desired.
    hermesModel = "gpt-5.5";
    hermesProvider = "openai-codex";
    # Point this at an age/sops-created EnvironmentFile on the target machine.
    # secretsFile = /run/secrets/hermes-env;
  };

  environment.systemPackages = with pkgs; [ git vim curl jq ];

  # Keep hardware/filesystem-specific decisions in hardware-configuration.nix on the target machine.
  system.stateVersion = "26.11";
}
