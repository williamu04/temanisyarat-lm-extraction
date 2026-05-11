#!/bin/bash

shopt -s nullglob
# Modify based on signer folders
SIGNER=(willi farras ivan ian hani mutia fredi saidah)

for S in "${SIGNER[@]}"; do
  INPUT_DIR="./videoset/$S"
  OUTPUT_DIR="./augmented/$S"

  mkdir -p "$OUTPUT_DIR"

  for LABEL_PATH in "$INPUT_DIR"/*/; do
    LABEL=$(basename "$LABEL_PATH")

    mkdir -p "$OUTPUT_DIR/$LABEL"

    # 9 augmentations per video:
    #   1. Slow down 20%
    #   2. Speed up 20%
    #   3. Shift left 10%
    #   4. Shift right 10%
    #   5. Horizontal Flip
    #   6. HFlip + Slow
    #   7. HFlip + Fast
    #   8. HFlip + Shift left
    #   9. HFlip + Shift right

    for VIDEO in "$LABEL_PATH"*.mp4; do
      BASENAME=$(basename "$VIDEO" .mp4)

      echo "Processing $VIDEO..."

      # 0. Copy original video
      cp "$VIDEO" "$OUTPUT_DIR/$LABEL/${BASENAME}_orig.mp4"

      # 1. Slow down 20%
      ffmpeg -y -i "$VIDEO" \
        -vf "setpts=1.2*PTS" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_slow.mp4"

      # 2. Speed up 20%
      ffmpeg -y -i "$VIDEO" \
        -vf "setpts=0.8*PTS" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_fast.mp4"

      # 3. shift left (no stretch)
      ffmpeg -y -i "$VIDEO" \
        -vf "pad='2*round(iw*1.1/2)':ih:0:0,crop=iw:ih:'2*round(iw*1.1/2)-iw':0" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_shift_left.mp4"

      # 4. shift right (no stretch)
      ffmpeg -y -i "$VIDEO" \
        -vf "pad='2*round(iw*1.1/2)':ih:'2*round(iw*1.1/2)-iw':0,crop=iw:ih:0:0" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_shift_right.mp4"

      # 5. Horizontal Flip
      ffmpeg -y -i "$VIDEO" \
        -vf "hflip" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_hflip.mp4"

      # 6. Horizontal Flip + Slow down
      ffmpeg -y -i "$VIDEO" \
        -vf "hflip,setpts=1.2*PTS" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_hflip_slow.mp4"

      # 7. Horizontal Flip + Speed up
      ffmpeg -y -i "$VIDEO" \
        -vf "hflip,setpts=0.8*PTS" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_hflip_fast.mp4"

      # 8. Hflip + shift left (no stretch)
      ffmpeg -y -i "$VIDEO" \
        -vf "hflip,pad='2*round(iw*1.1/2)':ih:0:0,crop=iw:ih:'2*round(iw*1.1/2)-iw':0" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_hflip_shift_left.mp4"

      # 9. Hflip + shift right (no stretch)
      ffmpeg -y -i "$VIDEO" \
        -vf "hflip,pad='2*round(iw*1.1/2)':ih:'2*round(iw*1.1/2)-iw':0,crop=iw:ih:0:0" \
        "$OUTPUT_DIR/$LABEL/${BASENAME}_hflip_shift_right.mp4"
    done
  done
done

echo "Augmentasi selesai."
