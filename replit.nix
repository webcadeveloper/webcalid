{pkgs}: {
  deps = [
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
