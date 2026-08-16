# Replace this file on the target computer with the output of:
#   sudo nixos-generate-config --show-hardware-config > nixos/hosts/knowledge-node/hardware-configuration.nix
#
# This placeholder exists so the flake evaluates before machine-specific hardware is known.
{ lib, ... }:
{
  boot.loader.systemd-boot.enable = lib.mkDefault true;
  boot.loader.efi.canTouchEfiVariables = lib.mkDefault true;

  # Target-machine filesystems belong here. The install guide explains how to replace this file.
  fileSystems."/" = lib.mkDefault {
    device = "/dev/disk/by-label/nixos";
    fsType = "ext4";
  };
}
