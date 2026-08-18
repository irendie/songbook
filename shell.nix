# Non-flake entry point: `nix-shell` works out of the box (no experimental features).
{ pkgs ? import <nixpkgs> { } }:
import ./nix/shell.nix { inherit pkgs; }
