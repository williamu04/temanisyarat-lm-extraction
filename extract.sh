#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

venv="$1"

# Modify based on signer folders
SIGNER=(willi farras ivan ian hani mutia fredi saidah)

for s in "${SIGNER[@]}"; do
  INPUT_DIR="./augmented/$s"
  OUTPUT_NPZ_DIR="./data/$s"
  OUTPUT_VIDEO_DIR="./landmarked/$s"

  mkdir -p "$OUTPUT_NPZ_DIR"
  mkdir -p "$OUTPUT_VIDEO_DIR"

  for LABEL_PATH in "$INPUT_DIR"/*/; do
    LABEL=$(basename "$LABEL_PATH")

    mkdir -p "$OUTPUT_NPZ_DIR/$LABEL"
    mkdir -p "$OUTPUT_VIDEO_DIR/$LABEL"

    echo "Processing videos in $LABEL_PATH..."

    "$venv" /bin/python main.py batch "$LABEL_PATH" --out-npy-dir "$OUTPUT_NPZ_DIR/$LABEL" --out-video-dir "$OUTPUT_VIDEO_DIR/$LABEL"
  done
done

echo "All signer subdirectories processed."
