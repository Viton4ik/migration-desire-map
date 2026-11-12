#!/bin/bash
# Render one region as global frames [N0, N1) with the matching voice samples, no music, no effects.
# usage: render/render_region.sh <region_id> <N0> <N1> [workers]
# Video parts are joined silent (concat demuxer, stream copy) and ONE audio slice is muxed on top,
# so seams never get per-part AAC priming. Audio slice = samples [N0*SR/FPS, N1*SR/FPS) of the source WAV.
set -euo pipefail
cd "$(dirname "$0")/.."
RID=$1; N0=$2; N1=$3; W=${4:-4}; FPS=30
# the edited timeline (source + inserted silences, built by tools/audio_edit.py)
SRC=audio/voice_en_edited.wav
SR=$(ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate -of csv=p=0 "$SRC")
OUT=export/$RID; mkdir -p "$OUT/parts"
TOTAL=$((N1-N0)); STEP=$(( (TOTAL + W - 1) / W ))
pids=()
for ((k=0; k<W; k++)); do
  a=$((N0 + k*STEP)); b=$((a + STEP)); [ $b -gt $N1 ] && b=$N1; [ $a -ge $b ] && continue
  node render/render.js chunk "$OUT/parts/p$k.mp4" $a $b > "$OUT/parts/p$k.log" 2>&1 & pids+=($!)
done
for p in "${pids[@]}"; do wait $p; done
ls "$OUT"/parts/p*.mp4 | sort -V | sed "s|^$OUT/parts/|file '|; s|$|'|" > "$OUT/parts/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$OUT/parts/list.txt" -c copy "$OUT/video_silent.mp4"
S0=$(( N0 * SR / FPS )); S1=$(( N1 * SR / FPS ))
ffmpeg -v error -y -i "$SRC" -af "atrim=start_sample=$S0:end_sample=$S1,asetpts=PTS-STARTPTS" -c:a pcm_s16le "$OUT/voice_${RID}.wav"
ffmpeg -v error -y -i "$OUT/video_silent.mp4" -i "$OUT/voice_${RID}.wav" -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -movflags +faststart "$OUT/${RID}.mp4"
echo "{\"region\":\"$RID\",\"n0\":$N0,\"n1\":$N1,\"s0\":$S0,\"s1\":$S1,\"sr\":$SR}" > "$OUT/interval.json"
cat "$OUT/interval.json"
