#!/bin/bash

shopt -s nullglob
# Modify based on signer folders
SIGNER=(willi farras ivan ian hani mutia fredi saidah)

for S in "${SIGNER[@]}"; do
  INPUT_DIR="./landmarked/$S"
  OUTPUT_DIR="./reformated/$S"

  mkdir -p "$OUTPUT_DIR"

  for LABEL_PATH in "$INPUT_DIR"/*/; do
    LABEL=$(basename "$LABEL_PATH")

    mkdir -p "$OUTPUT_DIR/$LABEL"

    for VIDEO in "$LABEL_PATH"*.mp4; do
      BASENAME=$(basename "$VIDEO" .mp4)

      echo "Processing $VIDEO..."

      ffmpeg -y -i "$VIDEO" \
        -c:v libx264 \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_reformated.mp4"
    done
  done
done

echo "Reformat selesai."
