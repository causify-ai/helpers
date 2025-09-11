#!/usr/bin/env bash
f="$1"
set -e
echo "=== Quick info ==="
ffprobe -v error -of json -show_streams -show_format "$f" | jq '.format | {format_name,duration,bit_rate,size}'

echo "=== Decode errors ==="
if ffmpeg -v error -xerror -i "$f" -f null - >/dev/null 2>errors.log; then
  echo "Decode OK"
else
  echo "Decode errors found. See errors.log"
fi

echo "=== VFR vs CFR ==="
ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate,r_frame_rate -of default=nw=1:nk=1 "$f"

echo "=== Interlace check (idet) ==="
ffmpeg -v error -i "$f" -vf idet -frames:v 500 -f null - 2>idet.log || true
grep -m1 "Multi frame detection" idet.log || true
