#!/bin/bash
# Fixed launcher: uses FULL client library classpath (from version jsons) instead of the
# server-only legacyClassPath from unix_args.txt, so org.lwjgl becomes visible to the game layer.
GAME="/Users/ludwigxu/Library/Application Support/minecraft"
NATIVES=/tmp/lzmx-natives
JAVA=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home/bin/java
cd "$GAME" || exit 1
CP=$(python3 "$(dirname "$0")/lzmx-classpath.py") || exit 1
ARGS=$(cat libraries/net/minecraftforge/forge/1.20.1-47.3.22/unix_args.txt \
  | sed "s|--launchTarget forgeserver|--launchTarget forgeclient|; s|-DlegacyClassPath=[^ ]*|-DlegacyClassPath=$CP|")
echo "$ARGS" > /tmp/fix-args-echo.txt
"$JAVA" -Xms1G -Xmx4G \
  -XstartOnFirstThread \
  -Dfml.earlyprogresswindow=false \
  -Djava.library.path="$NATIVES" \
  -Dorg.lwjgl.util.DebugLoader=true \
  $ARGS \
  --version 1.20.1-forge-47.3.22 \
  --gameDir "$GAME" \
  --assetsDir "$GAME/assets" \
  --assetIndex 5 \
  --uuid 00000000-0000-0000-0000-000000000000 \
  --username ludwigxu \
  --accessToken 0 \
  --userType legacy > /tmp/lzmx-fixed.log 2>&1
echo "EXIT=$?" >> /tmp/lzmx-fixed.log
