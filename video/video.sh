#!/usr/bin/env bash
# The styled-video skill's scripts/video.py, from wherever it lives here: the
# plugin's source checkout when there is one (it carries the newest version),
# else the newest installed copy of the plugin.
set -euo pipefail
for v in "${STYLED_VIDEO_PY:-}" "$HOME/projects/claude-plugin-personal/skills/styled-video/scripts/video.py" \
  $(ls -t "$HOME"/.claude/plugins/cache/ben/ben/*/skills/styled-video/scripts/video.py 2>/dev/null); do
  [ -n "$v" ] && [ -f "$v" ] && exec "$v" "$@"
done
echo "video.sh: no styled-video video.py found" >&2
exit 1
