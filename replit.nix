{pkgs}: {
  deps = [
    pkgs.libsndfile
    pkgs.portaudio
    pkgs.glibcLocales
    pkgs.zlib
    pkgs.xcodebuild
    pkgs.postgresql
  ];
}
