#!/usr/bin/env bash
# Builds this repository's website for GitHub Pages into ./_site
# (run automatically by .github/workflows/pages.yml on every change).
set -euo pipefail
REPO="${GITHUB_REPOSITORY#*/}"
OWNER_URL="https://github.com/${GITHUB_REPOSITORY}"
WORK="$(mktemp -d)"
rm -rf _site

unpack() {  # unpack <zip file or release asset URL>
  local src="$1"
  if [[ "$src" == http* ]]; then
    curl -fsSL --retry 3 -o "$WORK/pkg.zip" "$src"
  else
    cp "$src" "$WORK/pkg.zip"
  fi
  mkdir -p "$WORK/pkg"
  unzip -q "$WORK/pkg.zip" -d "$WORK/pkg"
}

case "$REPO" in
  Cyberwave-Homesite)
    unpack Cyberwave-Homesite-selfhost-tested.zip
    cp -r "$WORK/pkg" _site; KIND=plain ;;
  The-Order-of-the-Threadseers)
    unpack "$OWNER_URL/releases/download/self-hosting-handoff-2026-10-05/Threadseers-static-tested.zip"
    cp -r "$WORK/pkg" _site; KIND=threadseers ;;
  TimeLeapCountdown)
    unpack "$OWNER_URL/releases/download/replit-handoff-2026-10-05/TimeLeapCountdown-static-tested-v2.zip"
    cp -r "$WORK/pkg" _site; KIND=timeleap ;;
  BeatfoxDrift)
    unpack "$OWNER_URL/releases/download/open-access-handoff-2026-10-05/BeatfoxDrift-open-access-source-and-build.zip"
    cp -r "$WORK/pkg/dist/public" _site; KIND=drift ;;
  BeatfoxSequencer)
    unpack "$OWNER_URL/releases/download/replit-handoff-2026-10-05/BeatfoxSequencer-source-and-build.zip"
    cp -r "$WORK/pkg/dist/public" _site; KIND=sequencer ;;
  Continuum-Reader)
    unpack ContinuumReader-open-access-source-and-assets.zip
    cp -r "$WORK/pkg/artifacts/continuum-reader/dist/public" _site; KIND=reader ;;
  GravitonTuner)
    mkdir _site
    cp -r index.html main.js style.css sw.js manifest.json worklet-wt.js lib _site/
    find . -maxdepth 1 -type f \( -name '*.png' -o -name '*.wav' -o -name '*.ico' -o -name '*.svg' -o -name '*.webp' -o -name '*.jpg' \) -exec cp {} _site/ \;
    KIND=graviton ;;
  *)
    echo "No build recipe for $REPO"; exit 1 ;;
esac

# drop any stray site files that were inside the packages but are not web content
rm -f _site/SELF-HOSTING.md
python3 -I site-patch.py _site "$REPO" "$KIND" "$WORK/pkg"
echo "Built $(du -sh _site | cut -f1) for https://${GITHUB_REPOSITORY_OWNER}.github.io/${REPO}/"
