#!/bin/bash
# Export the Web build (Godot 4.7.2, no threads) and publish it to the gh-pages branch.
set -e
cd "$(dirname "$0")"
GODOT=${GODOT:-./tools/Godot_v4.7.2-stable_linux.x86_64}
mkdir -p build/web
(cd game && ../$GODOT --headless --export-release "Web" ../build/web/index.html)
D=/tmp/ghp
if [ ! -d $D/.git ]; then git clone -q --branch gh-pages --single-branch "$(git remote get-url origin)" $D; fi
cd $D && git pull -q --ff-only || true
find $D -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -r "$OLDPWD"/build/web/* $D/ && touch $D/.nojekyll
git add -A && git -c user.name=Loriens22 -c user.email=Loriens22@users.noreply.github.com commit -qm "Deploy web build $(date -u +%Y-%m-%dT%H:%MZ)" && git push -q origin gh-pages
du -sh "$OLDPWD"/build/web
