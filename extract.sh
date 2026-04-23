#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# Modify based on signer folders
SIGNER=(signer1 signer2 signer3 siger4 signer5 signer6 signer7 signer8)

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

        for VIDEO in "$LABEL_PATH"*.mp4; do
            BASENAME=$(basename "$VIDEO" .mp4)

            echo "Processing $VIDEO..."

            python main.py batch "$VIDEO" --out-npy-dir "$OUTPUT_NPZ_DIR/$LABEL/${BASENAME}" --out-video-dir "$OUTPUT_VIDEO_DIR/$LABEL/${BASENAME}"
        done
    done
done

echo "All signer subdirectories processed."
