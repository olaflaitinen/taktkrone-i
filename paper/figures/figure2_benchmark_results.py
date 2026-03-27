#!/usr/bin/env python3
"""
Figure 2: Benchmark Performance Comparison
For IEEE OJ-ITS metroLM/TAKTKRONE-I Paper

Generates a grouped bar chart comparing TAKTKRONE-I against baselines
and ablations with 95% confidence intervals.
"""

import matplotlib.pyplot as plt
import numpy as np

# IEEE-style formatting
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 10,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 7,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05
})

# Methods (consistent with Table V in paper)
methods = [
    'Generic\nLLM',
    'RAG-\nGeneric',
    'Rules-\nBased',
    'T-I w/o\nRetrieval',
    'T-I w/o\nSynth',
    'T-I w/o\nUncert.',
    'TAKTKRONE-I\n(full)'
]

# Metrics from Table V (main results)
# ROUGE-L scores
rouge_l = np.array([0.412, 0.487, 0.298, 0.589, 0.456, 0.671, 0.678])
rouge_l_err = np.array([0.028, 0.031, 0.019, 0.024, 0.032, 0.021, 0.019])

# nDCG@5 scores
ndcg5 = np.array([0.534, 0.612, 0.478, 0.723, 0.601, 0.798, 0.812])
ndcg5_err = np.array([0.035, 0.029, 0.033, 0.026, 0.031, 0.022, 0.018])

# ECE (lower is better, we'll invert for visualization or handle separately)
ece = np.array([0.183, 0.156, np.nan, 0.098, 0.134, 0.142, 0.067])
ece_err = np.array([0.021, 0.018, np.nan, 0.012, 0.016, 0.014, 0.009])

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3.2))

x = np.arange(len(methods))
width = 0.35

# Grayscale colors
color1 = '#444444'
color2 = '#888888'

# Left subplot: ROUGE-L and nDCG@5
bars1 = ax1.bar(x - width/2, rouge_l, width, yerr=rouge_l_err,
                label='ROUGE-L', color=color1, edgecolor='black',
                linewidth=0.5, capsize=2)
bars2 = ax1.bar(x + width/2, ndcg5, width, yerr=ndcg5_err,
                label='nDCG@5', color=color2, edgecolor='black',
                linewidth=0.5, capsize=2)

ax1.set_xlabel('Method')
ax1.set_ylabel('Score')
ax1.set_title('(a) Summarization and Ranking Quality')
ax1.set_xticks(x)
ax1.set_xticklabels(methods, rotation=45, ha='right')
ax1.legend(loc='upper left')
ax1.set_ylim(0, 1.0)
ax1.yaxis.grid(True, linestyle='--', alpha=0.7)
ax1.set_axisbelow(True)

# Highlight best method
ax1.axvspan(len(methods)-1.5, len(methods)-0.5, alpha=0.15, color='green')

# Right subplot: ECE (lower is better)
# Filter out NaN for rules-based
valid_idx = ~np.isnan(ece)
x_valid = x[valid_idx]
ece_valid = ece[valid_idx]
ece_err_valid = ece_err[valid_idx]
methods_valid = [methods[i] for i in range(len(methods)) if valid_idx[i]]

bars3 = ax2.bar(range(len(ece_valid)), ece_valid, width=0.6,
                yerr=ece_err_valid, color='#666666', edgecolor='black',
                linewidth=0.5, capsize=2)

ax2.set_xlabel('Method')
ax2.set_ylabel('Expected Calibration Error')
ax2.set_title('(b) Calibration (lower is better)')
ax2.set_xticks(range(len(methods_valid)))
ax2.set_xticklabels(methods_valid, rotation=45, ha='right')
ax2.set_ylim(0, 0.25)
ax2.yaxis.grid(True, linestyle='--', alpha=0.7)
ax2.set_axisbelow(True)

# Highlight best method (last one)
ax2.axvspan(len(ece_valid)-1.5, len(ece_valid)-0.5, alpha=0.15, color='green')

# Add value labels for ECE
for i, (val, err) in enumerate(zip(ece_valid, ece_err_valid)):
    ax2.annotate(f'{val:.3f}',
                xy=(i, val + err + 0.01),
                ha='center', va='bottom', fontsize=7)

plt.tight_layout()

# Save in both formats
plt.savefig('figure2_benchmark_results.pdf', format='pdf')
plt.savefig('figure2_benchmark_results.png', format='png')
print("Figure 2 saved successfully.")

plt.show()
