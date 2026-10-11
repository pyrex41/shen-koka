{
  description = "Shen on Koka development and comparison toolchains";

  # The sibling ports' lock packages Koka 3.2.3 including its C runtime.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { nixpkgs, ... }:
    let
      systems = [ "aarch64-darwin" "aarch64-linux" "x86_64-linux" ];
      eachSystem = f: nixpkgs.lib.genAttrs systems
        (system: f nixpkgs.legacyPackages.${system});
      nativeTools = pkgs: [
        pkgs.koka
        pkgs.stdenv.cc
        pkgs.cmake
        pkgs.gnumake
        pkgs.git
        pkgs.python3
        pkgs.jq
        pkgs.ripgrep
      ];
      comparisonTools = pkgs: nativeTools pkgs ++ [
        pkgs.go_1_27
        pkgs.luajit
      ];
    in {
      packages = eachSystem (pkgs:
        let
          toolchain = pkgs.buildEnv {
            name = "shen-koka-toolchain";
            paths = nativeTools pkgs;
          };
        in {
          inherit toolchain;
          default = toolchain;
          koka = pkgs.koka;
          comparison-toolchain = pkgs.buildEnv {
            name = "shen-koka-comparison-toolchain";
            paths = comparisonTools pkgs;
          };
        });

      devShells = eachSystem (pkgs: {
        default = pkgs.mkShell {
          packages = nativeTools pkgs;
        };
        comparison = pkgs.mkShell {
          packages = comparisonTools pkgs;
          # Avoid automatic downloads overriding the pinned Go compiler.
          env.GOTOOLCHAIN = "local";
        };
      });
    };
}
