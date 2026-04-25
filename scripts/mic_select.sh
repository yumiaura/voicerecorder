#!/usr/bin/env bash
# -*- shell -*-
# List PulseAudio sources, pick one, and run a short record+playback test.
set -euo pipefail

if ! command -v pactl &>/dev/null; then
  echo "pactl not found. Install: sudo apt install pulseaudio-utils" >&2
  exit 1
fi

mapfile -t LINES < <(pactl list short sources | awk '{print $2}' | sed '/^$/d' || true)
if [ "${#LINES[@]}" -eq 0 ]; then
  echo "No PulseAudio sources found. Is the sound server running?" >&2
  exit 1
fi

echo "Available sources (name for PULSE_SOURCE / ffmpeg -f pulse -i <name>):"
i=0
for s in "${LINES[@]}"; do
  echo "  $i) $s"
  i=$((i+1))
done
read -r -p "Enter number (empty = 0): " PICK
PICK="${PICK:-0}"
if ! [[ "$PICK" =~ ^[0-9]+$ ]] || [ "$PICK" -ge "$i" ]; then
  echo "Invalid index: $PICK" >&2
  exit 1
fi
CHOSEN="${LINES[$PICK]}"
export PULSE_SOURCE="${CHOSEN:-default}"
echo
echo "PULSE_SOURCE=$PULSE_SOURCE"
echo "Add to .env:  PULSE_SOURCE=$PULSE_SOURCE"
echo

TMP="${TMPDIR:-/tmp}/voicerec_mictest_$$.ogg"
echo "Recording 3 seconds to $TMP (speak into the mic)..."
if ! ffmpeg -y -f pulse -i "$PULSE_SOURCE" -t 3 -c:a libvorbis -q:a 5 -ar 48000 "$TMP" 2>/tmp/voicerec_mictest_ffmpeg.log; then
  cat /tmp/voicerec_mictest_ffmpeg.log >&2 || true
  echo "ffmpeg record failed" >&2
  exit 1
fi
echo "Playing back..."
if command -v ffplay &>/dev/null; then
  ffplay -nodisp -autoexit -loglevel quiet "$TMP" || true
else
  echo "ffplay not in PATH. Install: sudo apt install ffmpeg" >&2
  echo "Ogg file saved, play manually: $TMP" >&2
fi
echo "Test done. Ogg: $TMP"
