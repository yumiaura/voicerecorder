#!/usr/bin/env bash
# -*- shell -*-
# Pick microphone source (ALSA or Pulse) and run a short test.
set -euo pipefail

if ! command -v ffmpeg &>/dev/null; then
  echo "ffmpeg not found. Install: sudo apt install ffmpeg" >&2
  exit 1
fi

echo "Choose capture backend:"
echo "  1) ALSA (recommended for Docker worker)"
echo "  2) PulseAudio/PipeWire source name"
read -r -p "Enter number (default = 1): " MODE
MODE="${MODE:-1}"

RECORDER_INPUT=""
ALSA_DEVICE=""
PULSE_SOURCE=""

if [ "$MODE" = "1" ]; then
  if ! command -v arecord &>/dev/null; then
    echo "arecord not found. Install: sudo apt install alsa-utils" >&2
    exit 1
  fi

  mapfile -t DEVICES < <(arecord -l 2>/dev/null | awk '
    /^card [0-9]+: / {
      card=$2; gsub(":", "", card)
      device=$5; gsub(":", "", device)
      name=$0
      sub(/^card [0-9]+: /, "", name)
      print "plughw:" card "," device "|" name
    }')

  if [ "${#DEVICES[@]}" -eq 0 ]; then
    echo "No ALSA capture devices found." >&2
    exit 1
  fi

  echo "Available ALSA capture devices:"
  i=0
  for d in "${DEVICES[@]}"; do
    echo "  $i) ${d#*|} -> ${d%%|*}"
    i=$((i+1))
  done
  read -r -p "Enter number (default = 0): " PICK
  PICK="${PICK:-0}"
  if ! [[ "$PICK" =~ ^[0-9]+$ ]] || [ "$PICK" -ge "$i" ]; then
    echo "Invalid index: $PICK" >&2
    exit 1
  fi
  ALSA_DEVICE="${DEVICES[$PICK]%%|*}"
  RECORDER_INPUT="alsa"

  TMP="${TMPDIR:-/tmp}/voicerec_mictest_$$.ogg"
  echo "Recording 3 seconds from $ALSA_DEVICE to $TMP ..."
  if ! ffmpeg -y -f alsa -ac 1 -i "$ALSA_DEVICE" -t 3 -c:a libvorbis -q:a 5 -ar 48000 "$TMP" >/tmp/voicerec_mictest_ffmpeg.log 2>&1; then
    sed -n '1,120p' /tmp/voicerec_mictest_ffmpeg.log >&2 || true
    echo "ffmpeg ALSA test failed" >&2
    exit 1
  fi
else
  if ! command -v pactl &>/dev/null; then
    echo "pactl not found. Install: sudo apt install pulseaudio-utils" >&2
    exit 1
  fi
  mapfile -t SOURCES < <(pactl list short sources | awk '{print $2}' | sed '/^$/d' || true)
  if [ "${#SOURCES[@]}" -eq 0 ]; then
    echo "No Pulse sources found. Is Pulse/PipeWire running?" >&2
    exit 1
  fi
  echo "Available Pulse sources:"
  i=0
  for s in "${SOURCES[@]}"; do
    echo "  $i) $s"
    i=$((i+1))
  done
  read -r -p "Enter number (default = 0): " PICK
  PICK="${PICK:-0}"
  if ! [[ "$PICK" =~ ^[0-9]+$ ]] || [ "$PICK" -ge "$i" ]; then
    echo "Invalid index: $PICK" >&2
    exit 1
  fi
  PULSE_SOURCE="${SOURCES[$PICK]}"
  RECORDER_INPUT="pulse"

  TMP="${TMPDIR:-/tmp}/voicerec_mictest_$$.ogg"
  echo "Recording 3 seconds from $PULSE_SOURCE to $TMP ..."
  if ! ffmpeg -y -f pulse -i "$PULSE_SOURCE" -t 3 -c:a libvorbis -q:a 5 -ar 48000 "$TMP" >/tmp/voicerec_mictest_ffmpeg.log 2>&1; then
    sed -n '1,120p' /tmp/voicerec_mictest_ffmpeg.log >&2 || true
    echo "ffmpeg Pulse test failed" >&2
    exit 1
  fi
fi

echo "Playing back..."
if command -v ffplay &>/dev/null; then
  ffplay -nodisp -autoexit -loglevel quiet "$TMP" || true
else
  echo "Ogg file saved, play manually: $TMP" >&2
fi

echo
echo "Test done. Ogg: $TMP"
echo "Add to .env:"
echo "  RECORDER_INPUT=$RECORDER_INPUT"
if [ "$RECORDER_INPUT" = "alsa" ]; then
  echo "  ALSA_DEVICE=$ALSA_DEVICE"
  echo "  RECORDER_CHANNELS=1"
  echo "  PULSE_SOURCE="
else
  echo "  PULSE_SOURCE=$PULSE_SOURCE"
fi
