#!/usr/bin/env python3
"""
Create model comparison figure for complex pipeline showing accuracy and processing time.
Shows 4 models: 3B, 8B, 20B, 70B
"""

import matplotlib.pyplot as plt
import numpy as np

# Data for 4 models with complex pipeline
models = ['3B\nLlama 3.2', '8B\nLlama 3', '20B\nGPT-OSS', '70B\nLlama 3.3']
# Accuracy data: only 70B works, others are 0%
correct = [0, 0, 0, 76.0]  # Correct percentages
partially_correct = [0, 0, 0, 0]  # Partially correct (we don't track this, so 0)
wrong = [0, 0, 0, 24.0]  # Wrong percentages
# Processing time per chunk (from the reference figure)
processing_time = [3.4, 2.9, 15.0, 23.1]  # Seconds per chunk

# Create figure
fig, ax1 = plt.subplots(figsize=(10, 6))

# Bar positions
x_pos = np.arange(len(models))
bar_width = 0.6

# Create stacked bars (only 70B has data)
bars_correct = ax1.bar(x_pos, correct, bar_width, 
                       label='Correct', color='#2E8B57', edgecolor='black', linewidth=1.5)
bars_partially = ax1.bar(x_pos, partially_correct, bar_width, bottom=correct,
                         label='Partially Correct', color='#FFD700', edgecolor='black', linewidth=1.5)

# Add percentage labels on 70B bar only
for i, c in enumerate(correct):
    if c > 0:  # Only label if there's data
        # Correct label
        ax1.text(i, c/2, f'Correct\n{c:.0f}%', ha='center', va='center', 
                 fontsize=12, fontweight='bold', color='white')
    else:
        # 0% label for models that don't work
        ax1.text(i, 2, f'{c:.0f}%', ha='center', va='bottom',
                 fontsize=14, fontweight='bold', color='black')

# Add partially correct label on top if exists (currently 0 for all)
for i, p in enumerate(partially_correct):
    if p > 0:
        ax1.text(i, correct[i] + p/2, f'{p:.0f}%', ha='center', va='center',
                 fontsize=12, fontweight='bold', color='black')

# First y-axis (Accuracy)
ax1.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
ax1.set_ylim(0, 100)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(models, fontsize=12)
ax1.set_xlabel('Model', fontsize=14, fontweight='bold')
ax1.tick_params(axis='y', labelsize=12)
ax1.grid(axis='y', alpha=0.3, linestyle='--')
ax1.set_axisbelow(True)

# Second y-axis (Processing time)
ax2 = ax1.twinx()
line = ax2.plot(x_pos, processing_time, 'ro-', linewidth=3, markersize=10, 
                label='Processing Time per Chunk')
ax2.set_ylabel('Processing Time per Chunk (seconds)', fontsize=14, fontweight='bold', color='red')
ax2.tick_params(axis='y', labelcolor='red', labelsize=12)

# Add time labels above points
for i, time in enumerate(processing_time):
    ax2.text(i, time + 1.5, f'{time:.1f}s', ha='center', va='bottom',
             fontsize=12, fontweight='bold', color='red')

# Set y-axis limits for time
max_time = max(processing_time)
ax2.set_ylim(0, max_time * 1.3)

# Add legend
handles1, labels1 = ax1.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(handles1 + handles2, labels1 + labels2, loc='upper left', fontsize=11)

# Adjust layout
plt.tight_layout()

# Save figure
plt.savefig('model_comparison_accuracy_time.png', dpi=300, bbox_inches='tight')
plt.savefig('model_comparison_accuracy_time.pdf', bbox_inches='tight')

print("✅ Created: model_comparison_accuracy_time.png")
print("✅ Created: model_comparison_accuracy_time.pdf")

plt.close()
