{ pkgs }:

let
  tex = pkgs.texlive.withPackages (ps: with ps; [
    scheme-small
    luainputenc
    bookmark
    songs
    cm-unicode

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

  czechLocale = pkgs.callPackage
    "${pkgs.path}/pkgs/development/libraries/glibc/locales.nix"
    {
      allLocales = false;
      locales = [ "cs_CZ.UTF-8/UTF-8" ];
    };
in
pkgs.mkShell {
  packages = [
    tex
    pkgs.python3
    czechLocale
  ];

  shellHook = ''
    unset SOURCE_DATE_EPOCH
    unset LOCALE_ARCHIVE_2_27

    export LOCALE_ARCHIVE=${czechLocale}/lib/locale/locale-archive

    # Don't inherit the host's individual LC_* settings.
    unset LC_ADDRESS
    unset LC_IDENTIFICATION
    unset LC_MEASUREMENT
    unset LC_MONETARY
    unset LC_NAME
    unset LC_PAPER
    unset LC_TELEPHONE
    unset LC_TIME
    unset LC_NUMERIC
    unset LC_COLLATE
    unset LC_MESSAGES
    unset LC_CTYPE
    unset LANGUAGE

    export LANG=C.UTF-8
    export LC_ALL=C.UTF-8

    echo "Songbook dev shell — run: ./script/build.sh <a4|a5|all|clean> [options]"
  '';
}
