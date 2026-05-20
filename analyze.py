from __future__ import annotations

import logging
import os
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sns.set_style("whitegrid")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
OUT_DIR  = Path("analysis")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIGNERS = sorted(d.name for d in DATA_DIR.iterdir() if d.is_dir())
WORDS   = ["aku", "apel", "ayah", "besok", "buku", "dia", "dua", "hari ini",
           "ibu", "kamu", "kuning", "maaf", "merah", "nama", "pisang",
           "salam", "satu", "teman", "terima kasih", "tiga"]
VARIANTS = ["orig", "fast", "slow", "hflip", "shift_left", "shift_right",
            "hflip_fast", "hflip_slow", "hflip_shift_left", "hflip_shift_right"]

# ---------------------------------------------------------------------------
# 1. Collect all metadata
# ---------------------------------------------------------------------------
records = []

for signer in SIGNERS:
    for word in WORDS:
        wd = DATA_DIR / signer / word
        if not wd.is_dir():
            continue
        for var in VARIANTS:
            fname = f"{word}_{var}.npz"
            fpath = wd / fname
            if not fpath.exists():
                continue
            data = np.load(fpath)
            pose = data["pose"]   # [T, 9, 4]
            hands = data["hands"] # [T, 2, 21, 3]
            T = pose.shape[0]

            pose_nan = np.isnan(pose[..., :3]).mean()
            hands_nan = np.isnan(hands).mean()
            hand0_nan = np.isnan(hands[:, 0]).mean()
            hand1_nan = np.isnan(hands[:, 1]).mean()
            pose_vis_mean = pose[..., 3][~np.isnan(pose[..., 3])].mean() if (~np.isnan(pose[..., 3])).any() else 0.0

            records.append({
                "signer": signer,
                "word": word,
                "variant": var,
                "frames": T,
                "pose_nan": pose_nan,
                "hands_nan": hands_nan,
                "hand0_nan": hand0_nan,
                "hand1_nan": hand1_nan,
                "pose_vis_mean": pose_vis_mean,
            })

n_total = len(records)
logger.info("Total records: %d", n_total)

# ---------------------------------------------------------------------------
# 2. Summary statistics
# ---------------------------------------------------------------------------
frames_arr = np.array([r["frames"] for r in records])
pose_nan_arr = np.array([r["pose_nan"] for r in records])
hands_nan_arr = np.array([r["hands_nan"] for r in records])
hand0_nan_arr = np.array([r["hand0_nan"] for r in records])
hand1_nan_arr = np.array([r["hand1_nan"] for r in records])

# ---------------------------------------------------------------------------
# 3. Visualizations
# ---------------------------------------------------------------------------
FIG_W = 10
FIG_H = 5

fig, axes = plt.subplots(1, 3, figsize=(FIG_W * 3, FIG_H))

ax = axes[0]
ax.hist(frames_arr, bins=40, color="steelblue", edgecolor="white")
ax.set_xlabel("Frames per sample")
ax.set_ylabel("Count")
ax.set_title("Frame Length Distribution")

ax = axes[1]
ax.hist(pose_nan_arr * 100, bins=40, color="seagreen", edgecolor="white")
ax.set_xlabel("Pose NaN %")
ax.set_ylabel("Count")
ax.set_title("Pose Landmark Missing %")

ax = axes[2]
ax.hist(hands_nan_arr * 100, bins=40, color="coral", edgecolor="white")
ax.set_xlabel("Hands NaN %")
ax.set_ylabel("Count")
ax.set_title("Hand Landmark Missing %")

fig.tight_layout()
fig.savefig(OUT_DIR / "distributions.png", dpi=150)
logger.info("Saved distributions.png")
plt.close(fig)

# -- Per-signer NaN heatmap --
signer_word_nan = defaultdict(lambda: defaultdict(list))
for r in records:
    signer_word_nan[r["signer"]][r["word"]].append(r["hands_nan"])

signer_word_mean = {
    s: {w: np.mean(v) for w, v in wd.items()}
    for s, wd in signer_word_nan.items()
}

data_matrix = np.zeros((len(SIGNERS), len(WORDS)))
for i, s in enumerate(SIGNERS):
    for j, w in enumerate(WORDS):
        data_matrix[i, j] = signer_word_mean.get(s, {}).get(w, 1.0)

fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(data_matrix * 100, annot=True, fmt=".0f", cmap="RdYlGn_r",
            xticklabels=WORDS, yticklabels=SIGNERS, ax=ax, vmin=0, vmax=100)
ax.set_title("Hand Landmark NaN % per Signer × Word (orig only)")
ax.set_xlabel("Word")
ax.set_ylabel("Signer")
fig.tight_layout()
fig.savefig(OUT_DIR / "heatmap_signer_word.png", dpi=150)
logger.info("Saved heatmap_signer_word.png")
plt.close(fig)

# -- Per-variant NaN --
var_nan = defaultdict(list)
for r in records:
    var_nan[r["variant"]].append(r["hands_nan"])
var_means = {v: np.mean(ns) * 100 for v, ns in sorted(var_nan.items())}

fig, ax = plt.subplots(figsize=(12, 4))
colors = ["#2ecc71" if v == "orig" else "#3498db" for v in var_means]
ax.bar(list(var_means.keys()), list(var_means.values()), color=colors, edgecolor="white")
ax.set_ylabel("Hand NaN %")
ax.set_title("Hand Landmark Missing % by Augmentation Variant")
ax.tick_params(axis="x", rotation=30)
for i, (k, v) in enumerate(var_means.items()):
    ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=8)
fig.tight_layout()
fig.savefig(OUT_DIR / "variant_nan.png", dpi=150)
logger.info("Saved variant_nan.png")
plt.close(fig)

# -- Left vs Right hand NaN --
hand_nan_by_signer = defaultdict(lambda: [[], []])
for r in records:
    hand_nan_by_signer[r["signer"]][0].append(r["hand0_nan"])
    hand_nan_by_signer[r["signer"]][1].append(r["hand1_nan"])

fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(len(SIGNERS))
w = 0.35
h0_means = [np.mean(hand_nan_by_signer[s][0]) * 100 for s in SIGNERS]
h1_means = [np.mean(hand_nan_by_signer[s][1]) * 100 for s in SIGNERS]
ax.bar(x - w/2, h0_means, w, label="Hand 0 (maybe right)", color="tomato")
ax.bar(x + w/2, h1_means, w, label="Hand 1 (maybe left)", color="skyblue")
ax.set_xticks(x)
ax.set_xticklabels(SIGNERS)
ax.set_ylabel("NaN %")
ax.set_title("Left vs Right Hand Detection Rate by Signer")
ax.legend()
fig.tight_layout()
fig.savefig(OUT_DIR / "hand_lr_nan.png", dpi=150)
logger.info("Saved hand_lr_nan.png")
plt.close(fig)

# -- Per-signer frame length boxplot --
signer_frames = {s: [] for s in SIGNERS}
for r in records:
    signer_frames[r["signer"]].append(r["frames"])

fig, ax = plt.subplots(figsize=(10, 5))
bp_data = [signer_frames[s] for s in SIGNERS]
bp = ax.boxplot(bp_data, labels=SIGNERS, patch_artist=True)
for patch, color in zip(bp["boxes"], plt.cm.viridis(np.linspace(0.2, 0.8, len(SIGNERS)))):
    patch.set_facecolor(color)
ax.set_ylabel("Frames")
ax.set_title("Frame Length Distribution per Signer")
fig.tight_layout()
fig.savefig(OUT_DIR / "frames_per_signer.png", dpi=150)
logger.info("Saved frames_per_signer.png")
plt.close(fig)

# -- Per-word frame length boxplot --
word_frames = {w: [] for w in WORDS}
for r in records:
    word_frames[r["word"]].append(r["frames"])

fig, ax = plt.subplots(figsize=(14, 5))
bp_data = [word_frames[w] for w in WORDS]
bp = ax.boxplot(bp_data, labels=WORDS, patch_artist=True)
for patch, color in zip(bp["boxes"], plt.cm.plasma(np.linspace(0.2, 0.8, len(WORDS)))):
    patch.set_facecolor(color)
ax.set_ylabel("Frames")
ax.set_title("Frame Length Distribution per Word")
ax.tick_params(axis="x", rotation=30)
fig.tight_layout()
fig.savefig(OUT_DIR / "frames_per_word.png", dpi=150)
logger.info("Saved frames_per_word.png")
plt.close(fig)

# -- Pose visibility scores --
fig, ax = plt.subplots(figsize=(10, 5))
vis_means = [r["pose_vis_mean"] for r in records if r["variant"] == "orig"]
ax.hist(vis_means, bins=40, color="purple", edgecolor="white")
ax.set_xlabel("Mean Pose Visibility Score")
ax.set_ylabel("Count")
ax.set_title("Pose Detection Confidence (visibility) Distribution")
fig.tight_layout()
fig.savefig(OUT_DIR / "pose_visibility.png", dpi=150)
logger.info("Saved pose_visibility.png")
plt.close(fig)

# -- Correlation: frames vs NaN --
fig, ax = plt.subplots(figsize=(8, 5))
sc = ax.scatter(frames_arr, hands_nan_arr * 100, c=pose_nan_arr * 100,
                alpha=0.4, s=8, cmap="viridis")
ax.set_xlabel("Frames")
ax.set_ylabel("Hands NaN %")
ax.set_title("Frames vs Hand NaN % (colored by Pose NaN %)")
plt.colorbar(sc, ax=ax, label="Pose NaN %")
fig.tight_layout()
fig.savefig(OUT_DIR / "frames_vs_nan.png", dpi=150)
logger.info("Saved frames_vs_nan.png")
plt.close(fig)

# ---------------------------------------------------------------------------
# 4. Generate markdown report
# ---------------------------------------------------------------------------
report_lines = []
report_lines.append("# Dataset Analytics Report")
report_lines.append("")
report_lines.append(f"**Generated:** automated")
report_lines.append("")
report_lines.append("## 1. Dataset Overview")
report_lines.append("")
report_lines.append(f"| Metric | Value |")
report_lines.append(f"|--------|-------|")
report_lines.append(f"| Total `.npz` samples | `{n_total}` |")
report_lines.append(f"| Signers | `{len(SIGNERS)}` — {', '.join(SIGNERS)} |")
report_lines.append(f"| Word classes | `{len(WORDS)}` |")
report_lines.append(f"| Augmentation variants | `{len(VARIANTS)}` per sample |")

orig_count = sum(1 for r in records if r["variant"] == "orig")
report_lines.append(f"| Original (unaugmented) samples | `{orig_count}` |")
report_lines.append(f"| Augmented samples | `{n_total - orig_count}` |")
report_lines.append("")
report_lines.append("## 2. Frame Length Statistics")
report_lines.append("")
report_lines.append(f"| Statistic | Frames |")
report_lines.append(f"|-----------|--------|")
report_lines.append(f"| Mean | `{frames_arr.mean():.1f}` |")
report_lines.append(f"| Median | `{np.median(frames_arr):.0f}` |")
report_lines.append(f"| Std Dev | `{frames_arr.std():.1f}` |")
report_lines.append(f"| Min | `{frames_arr.min()}` |")
report_lines.append(f"| Max | `{frames_arr.max()}` |")
report_lines.append(f"| Q1 | `{np.percentile(frames_arr, 25):.0f}` |")
report_lines.append(f"| Q3 | `{np.percentile(frames_arr, 75):.0f}` |")
report_lines.append("")
report_lines.append("## 3. Landmark Missingness (NaN %)")
report_lines.append("")
report_lines.append("| Modality | Mean NaN % | Median NaN % | Std NaN % |")
report_lines.append("|----------|-----------|-------------|----------|")
report_lines.append(f"| Pose (x,y,z) | `{pose_nan_arr.mean()*100:.2f}%` | `{np.median(pose_nan_arr)*100:.2f}%` | `{pose_nan_arr.std()*100:.2f}%` |")
report_lines.append(f"| Hands (combined) | `{hands_nan_arr.mean()*100:.2f}%` | `{np.median(hands_nan_arr)*100:.2f}%` | `{hands_nan_arr.std()*100:.2f}%` |")
report_lines.append(f"| Hand 0 | `{hand0_nan_arr.mean()*100:.2f}%` | `{np.median(hand0_nan_arr)*100:.2f}%` | `{hand0_nan_arr.std()*100:.2f}%` |")
report_lines.append(f"| Hand 1 | `{hand1_nan_arr.mean()*100:.2f}%` | `{np.median(hand1_nan_arr)*100:.2f}%` | `{hand1_nan_arr.std()*100:.2f}%` |")
report_lines.append("")
report_lines.append("## 4. Per-Signer Hand NaN %")
report_lines.append("")
report_lines.append("| Signer | Hand NaN % |")
report_lines.append("|--------|-----------|")
for s in SIGNERS:
    sn = [r["hands_nan"] for r in records if r["signer"] == s]
    report_lines.append(f"| {s} | `{np.mean(sn)*100:.1f}%` |")
report_lines.append("")
report_lines.append("## 5. Per-Word Hand NaN %")
report_lines.append("")
report_lines.append("| Word | Hand NaN % |")
report_lines.append("|------|-----------|")
for w in WORDS:
    wn = [r["hands_nan"] for r in records if r["word"] == w]
    report_lines.append(f"| {w} | `{np.mean(wn)*100:.1f}%` |")
report_lines.append("")
report_lines.append("## 6. Augmentation Variant Hand NaN %")
report_lines.append("")
report_lines.append("| Variant | Hand NaN % |")
report_lines.append("|---------|-----------|")
for v in sorted(var_nan):
    report_lines.append(f"| {v} | `{np.mean(var_nan[v])*100:.1f}%` |")
report_lines.append("")
report_lines.append("## 7. Pose Visibility Scores")
report_lines.append("")
vis_all = [r["pose_vis_mean"] for r in records]
report_lines.append(f"| Statistic | Value |")
report_lines.append(f"|-----------|-------|")
report_lines.append(f"| Mean | `{np.mean(vis_all):.3f}` |")
report_lines.append(f"| Median | `{np.median(vis_all):.3f}` |")
report_lines.append(f"| Min | `{np.min(vis_all):.3f}` |")
report_lines.append(f"| Max | `{np.max(vis_all):.3f}` |")
report_lines.append("")
report_lines.append("## 8. Visualizations")
report_lines.append("")
report_lines.append("| Figure | Description |")
report_lines.append("|--------|-------------|")
report_lines.append("| `distributions.png` | Frame length, pose NaN %, hands NaN % histograms |")
report_lines.append("| `heatmap_signer_word.png` | Hand NaN % heatmap across signers × words (orig only) |")
report_lines.append("| `variant_nan.png` | Hand NaN % by augmentation variant |")
report_lines.append("| `hand_lr_nan.png` | Left vs right hand detection rate by signer |")
report_lines.append("| `frames_per_signer.png` | Frame length distribution per signer |")
report_lines.append("| `frames_per_word.png` | Frame length distribution per word |")
report_lines.append("| `pose_visibility.png` | Pose detection confidence distribution |")
report_lines.append("| `frames_vs_nan.png` | Frames vs hand NaN% scatter (colored by pose NaN%) |")

report = "\n".join(report_lines)

(OUT_DIR / "REPORT.md").write_text(report)
logger.info("Saved REPORT.md")

print(f"\nAnalysis complete. {n_total} files analyzed.")
print(f"Report:  {OUT_DIR / 'REPORT.md'}")
print(f"Plots:   {OUT_DIR / '*.png'}")
