# Shared dev shell definition, used by both flake.nix and ../shell.nix.
{ pkgs }:
let
  tex = pkgs.texlive.withPackages (ps: with ps; [
    scheme-small        # lualatex, fontspec, luaotfload, geometry, hyperref, babel, ...
    luainputenc
    bookmark
    songs               # songs package (chorded songbooks)
    songidx             # song index generator used between LuaLaTeX passes
    cm-unicode          # CMU Serif/Sans/Typewriter fonts (latin + cyrillic)
    babel-czech
    babel-english
    babel-russian
    babel-latin
    babel-croatian
    babel-slovak
    hyphen-czech
    hyphen-english
    hyphen-russian
    hyphen-latin
    hyphen-croatian
    hyphen-slovak
  ]);
in
pkgs.mkShell {
  packages = [
    tex
    pkgs.python3 # sort_index.py (--custom-sort)
  ] ++ pkgs.lib.optionals pkgs.stdenv.isLinux [
    pkgs.glibcLocales # cs_CZ.UTF-8 for songidx and sort_index.py
  ];

  shellHook = pkgs.lib.optionalString pkgs.stdenv.isLinux ''
    export LOCALE_ARCHIVE=${pkgs.glibcLocales}/lib/locale/locale-archive
  '' + ''
    echo "Songbook dev shell — run: ./script/build.sh <a4|a5|all|clean> [options]"
  '';
}
