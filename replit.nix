{pkgs}: {
  deps = [
    pkgs.playwright-driver
    pkgs.gitFull
    pkgs.sqlite-interactive
    pkgs.nano
    pkgs.docker
    pkgs.geckodriver
    pkgs.alsa-utils
    pkgs.alsa-lib
    pkgs.libsndfile
    pkgs.portaudio
    pkgs.glibcLocales
    pkgs.zlib
    pkgs.xcodebuild
    pkgs.postgresql
  ];
}
