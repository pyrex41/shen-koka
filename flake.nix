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
          shen-koka = pkgs.stdenv.mkDerivation {
            pname = "shen-koka";
            version = "0.0.1-experimental";
            src = ./.;
            nativeBuildInputs = [ pkgs.koka pkgs.python3 pkgs.makeWrapper ];
            dontConfigure = true;
            buildPhase = ''
              runHook preBuild
              bash scripts/build.sh
              runHook postBuild
            '';
            installPhase = ''
              runHook preInstall
              root="$out/share/shen-koka"
              mkdir -p "$root/.build" "$out/bin"
              cp .build/shen-koka .build/build.json "$root/.build/"
              cp -r bin src kernel compat third-party "$root/"
              mkdir -p "$root/scripts"
              cp scripts/build-slice.py scripts/native_build.py scripts/native_codegen.py "$root/scripts/"
              cp flake.lock "$root/"
              patchShebangs "$root/bin" "$root/scripts"
              makeWrapper "$root/bin/shen-koka" "$out/bin/shen-koka" \
                --prefix PATH : ${pkgs.lib.makeBinPath [ pkgs.python3 pkgs.koka pkgs.stdenv.cc ]}
              runHook postInstall
            '';
            # Fixup may strip the executable; record the installed bytes.
            postFixup = ''
              ${pkgs.python3}/bin/python3 -c 'import pathlib,sys,json,hashlib; p=pathlib.Path(sys.argv[1]); r=p/".build/build.json"; j=json.loads(r.read_text()); j["binary_sha256"]=hashlib.sha256((p/".build/shen-koka").read_bytes()).hexdigest(); r.write_text(json.dumps(j,indent=2)+"\n")' "$out/share/shen-koka"
            '';
            meta.description = "Experimental Koka-owned Shen runtime with pinned S42 kernel";
          };
        in {
          inherit toolchain shen-koka;
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
