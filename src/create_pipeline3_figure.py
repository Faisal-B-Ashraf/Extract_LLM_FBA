#!/usr/bin/env python3
"""
Create comprehensive figure for Pipeline 3 results similar to Figure 5.

Figure components:
(a) Individual variable accuracy across 12 attributes
(b) Comparison: Simple vs Sophisticated extraction for minimum flow
(c) Processing efficiency with examples
(d) Failure mode analysis with examples
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")

def load_data():
    """Load validation results and timing data."""
    summary = pd.read_csv('pipeline3_validation_summary.csv', index_col=0)
    detailed = pd.read_csv('pipeline3_validation_detailed.csv')
    timing_simple = pd.read_csv('multi_variable_simple_timing.csv')
    timing_complex = pd.read_csv('min_flow_timing_results.csv')
    
    return summary, detailed, timing_simple, timing_complex

def plot_variable_accuracy(ax, summary):
    """Panel (a): Individual variable accuracy across 12 attributes."""
    
    # Variable names and their accuracies
    variables = [
        'project_name', 'location_combined', 'generation_capacity', 
        'owner_operator', 'plant_type', 'minimum_flow',
        'migratory_fish_species', 'project_costs',
        'licensing_dates', 'key_stakeholders'
    ]
    
    labels = [
        'Project Name', 'Location', 'Generation\nCapacity', 
        'Owner/\nOperator', 'Plant Type', 'Minimum\nFlow',
        'Fish Species', 'Project\nCosts', 
        'Licensing\nDates', 'Key\nStakeholders'
    ]
    
    correct = []
    partial = []
    wrong = []
    
    for var in variables:
        if var in summary.index:
            correct.append(summary.loc[var, 'Correct'])
            partial.append(summary.loc[var, 'Partial'])
            wrong.append(summary.loc[var, 'Wrong'])
        else:
            correct.append(0)
            partial.append(0)
            wrong.append(0)
    
    total = np.array(correct) + np.array(partial) + np.array(wrong)
    correct_pct = (np.array(correct) / total * 100)
    partial_pct = (np.array(partial) / total * 100)
    wrong_pct = (np.array(wrong) / total * 100)
    
    x = np.arange(len(labels))
    width = 0.7
    
    # Stacked bars
    p1 = ax.bar(x, correct_pct, width, label='Correct', color='#2ecc71', edgecolor='black', linewidth=0.5)
    p2 = ax.bar(x, partial_pct, width, bottom=correct_pct, label='Partial', color='#f39c12', edgecolor='black', linewidth=0.5)
    p3 = ax.bar(x, wrong_pct, width, bottom=correct_pct+partial_pct, label='Wrong', color='#e74c3c', edgecolor='black', linewidth=0.5)
    
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=14)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', frameon=True, fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    # Add percentage labels on bars for correct values
    for i, (c_pct, p, w) in enumerate(zip(correct_pct, partial_pct, wrong_pct)):
        if c_pct > 15:
            ax.text(i, c_pct/2, f'{c_pct:.0f}%', ha='center', va='center', 
                   fontweight='bold', fontsize=11, color='white')
    
    # Add panel label inside top left
    ax.text(0.02, 0.98, '(a)', transform=ax.transAxes, fontsize=16, 
            fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='black', linewidth=1))

def plot_timing_comparison(ax, timing_simple, timing_complex):
    """Panel (b): Timing comparison for minimum flow extraction between simple and complex pipelines (both 70B)."""
    
    # Compare ONLY minimum flow extraction time
    # Simple pipeline: minimum_flow_time column
    simple_minflow_time = timing_simple['minimum_flow_time'].mean()
    
    # Complex pipeline: processing_time_seconds (entire pipeline is for min flow only)
    complex_minflow_time = timing_complex['processing_time_seconds'].mean()
    
    pipelines = ['Simple Extraction', 
                 'Targeted Extraction']
    times = [simple_minflow_time, complex_minflow_time]
    colors = ['#2ecc71', '#e74c3c']
    
    bars = ax.bar(pipelines, times, color=colors, width=0.6, 
                  edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Processing Time (seconds/document)', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', labelsize=14)
    ax.set_ylim(0, max(times) * 1.15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bar, time in zip(bars, times):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{time:.1f}s', ha='center', va='bottom', 
                fontweight='bold', fontsize=14)
    
    # Add panel label inside top left
    ax.text(0.02, 0.98, '(c)', transform=ax.transAxes, fontsize=16, 
            fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='black', linewidth=1))

def plot_error_classification(ax):
    """Panel (c): Error classification pie chart with examples."""
    
    # Error categories and counts (from 70B model analysis)
    categories = ['False Positive\nExtraction', 'Wrong Numeric\nValue', 'Other\nErrors']
    counts = [6, 4, 2]
    colors = ['#e74c3c', '#f39c12', '#3498db']
    
    # Create pie chart without labels (will use legend instead)
    wedges, texts, autotexts = ax.pie(counts, labels=None, autopct='%1.1f%%',
                                        colors=colors, startangle=90,
                                        textprops={'fontsize': 12, 'fontweight':'bold'},
                                        center=(-2.1, 0), radius=0.85)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(13)
    
    # Add legend for pie chart (moved with pie chart)
    ax.legend(wedges, categories, loc='upper left', bbox_to_anchor=(0.15, 0.9),
              fontsize=11, frameon=True, fancybox=True, shadow=True)
    
    # Add example annotations to the right of pie chart
    examples = [
        "Examples:",
        "",
        "• False Positive: P12379",
        "  'No min flow' → extracted '40 cfs'",
        "",
        "• Wrong Value: P1773", 
        "  '35/20 cfs seasonal' → extracted '10 cfs'",
        "",
        "• Other: P2566",
        "  'Run-of-river' → extracted fishway flow"
    ]
    
    ax.text(0.58, 0.9, '\n'.join(examples), 
            transform=ax.transAxes,
            fontsize=16, verticalalignment='top', horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.3))
    
    # Add panel label inside top left (positioned over pie chart)
    ax.text(0.10, 0.98, '(d)', transform=ax.transAxes, fontsize=16, 
            fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='black', linewidth=1))
    
    # Set axis limits for balanced layout
    ax.set_xlim(-1.5, 1.5)
    
    # Turn on axis and add rectangular border
    ax.axis('on')
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(0.8)
        spine.set_visible(True)
    ax.set_xticks([])
    ax.set_yticks([])
def plot_failure_analysis(ax, detailed):
    """Panel (d): Failure mode analysis with examples."""
    
    # Analyze minimum flow failures
    minflow_results = detailed[['filename', 'minimum_flow', 'minimum_flow_explanation']]
    
    # Categorize failures
    correct = sum(minflow_results['minimum_flow'] == 'Correct')
    wrong = sum(minflow_results['minimum_flow'] == 'Wrong')
    partial = sum(minflow_results['minimum_flow'] == 'Partial')
    
    categories = ['Correct\nExtraction', 'Failed to\nExtract', 'Incorrect\nValue']
    counts = [correct, wrong, partial]
    colors = ['#2ecc71', '#e74c3c', '#f39c12']
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(counts, labels=categories, autopct='%1.1f%%',
                                        colors=colors, startangle=90,
                                        textprops={'fontsize': 13, 'fontweight': 'bold'})
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(14)
    
    # Add example annotations
    examples = [
        f"✓ Correct (n={correct})",
        f"✗ Failed (n={wrong})",
        f"⚠ Partial (n={partial})"
    ]
    
    ax.text(1.4, 0.5, '\n\n'.join(examples), 
            transform=ax.transData,
            fontsize=12, verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.3))

def plot_minflow_accuracy_comparison(ax, summary):
    """Panel (b): Minimum flow accuracy comparison between Simple and Targeted extraction."""
    
    # Get minimum flow accuracy from summary
    if 'minimum_flow' in summary.index:
        simple_correct = summary.loc['minimum_flow', 'Correct']
        simple_partial = summary.loc['minimum_flow', 'Partial']
        simple_wrong = summary.loc['minimum_flow', 'Wrong']
    else:
        simple_correct = 0
        simple_partial = 0
        simple_wrong = 0
    
    simple_total = simple_correct + simple_partial + simple_wrong
    simple_correct_pct = (simple_correct / simple_total * 100) if simple_total > 0 else 0
    simple_wrong_pct = ((simple_partial + simple_wrong) / simple_total * 100) if simple_total > 0 else 0
    
    # Targeted extraction (70B model from manual validation)
    targeted_correct_pct = 76.0  # 38 out of 50
    targeted_wrong_pct = 24.0    # 12 out of 50
    
    methods = ['Simple\nExtraction', 'Targeted\nExtraction']
    x = np.arange(len(methods))
    width = 0.6
    
    # Stacked bars
    p1 = ax.bar(x, [simple_correct_pct, targeted_correct_pct], width, 
                label='Correct', color='#2ecc71', edgecolor='black', linewidth=1.5)
    p2 = ax.bar(x, [simple_wrong_pct, targeted_wrong_pct], width, 
                bottom=[simple_correct_pct, targeted_correct_pct],
                label='Wrong', color='#e74c3c', edgecolor='black', linewidth=1.5)
    
    ax.set_ylabel('Accuracy (%)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=14)
    ax.set_ylim(0, 105)
    ax.legend(loc='upper right', frameon=True, fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_title('Minimum Flow Variable', fontsize=14, fontweight='bold', pad=10)
    
    # Add percentage labels on bars
    for i, (correct, wrong) in enumerate(zip([simple_correct_pct, targeted_correct_pct], 
                                             [simple_wrong_pct, targeted_wrong_pct])):
        if correct > 15:
            ax.text(i, correct/2, f'{correct:.0f}%', ha='center', va='center', 
                   fontweight='bold', fontsize=13, color='white')
        if wrong > 10:
            ax.text(i, correct + wrong/2, f'{wrong:.0f}%', ha='center', va='center', 
                   fontweight='bold', fontsize=11, color='white')
    
    # Add panel label inside top left
    ax.text(0.02, 0.98, '(b)', transform=ax.transAxes, fontsize=16, 
            fontweight='bold', va='top', ha='left',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='black', linewidth=1))

def create_figure():
    """Create comprehensive 4-panel figure."""
    
    # Load data
    summary, detailed, timing_simple, timing_complex = load_data()
    
    # Create figure with 2x2 layout
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3, 
                          left=0.08, right=0.95, top=0.95, bottom=0.07)
    
    ax1 = fig.add_subplot(gs[0, 0])  # Top left
    ax2 = fig.add_subplot(gs[0, 1])  # Top right
    ax3 = fig.add_subplot(gs[1, 0])  # Bottom left
    ax4 = fig.add_subplot(gs[1, 1])  # Bottom right
    
    # Create plots
    plot_variable_accuracy(ax1, summary)
    plot_minflow_accuracy_comparison(ax2, summary)
    plot_timing_comparison(ax3, timing_simple, timing_complex)
    plot_error_classification(ax4)
    
    # Update panel labels for timing and error classification
    # (they were (b) and (c), now they're (c) and (d))
    
    # Save figure
    plt.savefig('Pipeline3_Performance_Analysis.png', dpi=300, bbox_inches='tight')
    plt.savefig('Pipeline3_Performance_Analysis.pdf', bbox_inches='tight')
    print(f"\n✅ Figure saved: Pipeline3_Performance_Analysis.png")
    print(f"✅ Figure saved: Pipeline3_Performance_Analysis.pdf")
    
    return fig

if __name__ == "__main__":
    print("="*80)
    print("CREATING PIPELINE 3 PERFORMANCE ANALYSIS FIGURE")
    print("="*80)
    
    fig = create_figure()
    
    print("\n" + "="*80)
    print("FIGURE COMPONENTS:")
    print("="*80)
    print("(a) Individual variable accuracy across 12 attributes")
    print("(b) Simple vs Sophisticated comparison for minimum flow")
    print("(c) Processing efficiency distribution")
    print("(d) Failure mode analysis")
    print("="*80)
