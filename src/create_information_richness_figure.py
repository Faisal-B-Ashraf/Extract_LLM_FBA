#!/usr/bin/env python3
"""
Create Sankey diagram showing information richness of minimum flow extractions.
Shows flow from: Document Type → Extraction Pattern → Completeness
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.sankey import Sankey
import numpy as np

# Load categorized data
df = pd.read_csv('min_flow_information_richness.csv')

print("="*80)
print("CREATING INFORMATION RICHNESS SANKEY DIAGRAM")
print("="*80)

# Count flows
doc_types = df['doc_type'].value_counts()
patterns = df['pattern'].value_counts()
completeness = df['completeness'].value_counts()

print(f"\nDocument Types: {dict(doc_types)}")
print(f"Patterns: {dict(patterns)}")
print(f"Completeness: {dict(completeness)}")

# Create figure
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(1, 1, 1)

# Define positions for nodes
doc_x = 0.1
pattern_x = 0.5
complete_x = 0.9

# Node y-positions
usace_y = 0.7
ferc_y = 0.3

constant_y = 0.75
seasonal_y = 0.55
conditional_y = 0.35
multiloc_y = 0.15

full_y = 0.7
partial_y = 0.5
valueonly_y = 0.3

# Manually draw the flows using patches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, PathPatch
from matplotlib.path import Path
import matplotlib.patches as mpatches

# Define colors
colors = {
    'USACE manual': '#8B4513',
    'FERC license': '#4682B4',
    'Constant': '#90EE90',
    'Seasonal': '#FFD700',
    'Conditional': '#FFA500',
    'Multi-location': '#FF6347',
    'Full': '#228B22',
    'Partial': '#DAA520',
    'Value-only': '#DC143C'
}

# Calculate flows between doc types and patterns
flows_doc_pattern = df.groupby(['doc_type', 'pattern']).size().reset_index(name='count')
flows_pattern_complete = df.groupby(['pattern', 'completeness']).size().reset_index(name='count')

print("\nFlows Doc→Pattern:")
print(flows_doc_pattern)
print("\nFlows Pattern→Complete:")
print(flows_pattern_complete)

# Use a library for Sankey - plotly
try:
    import plotly.graph_objects as go
    
    # Define node labels
    labels = ['USACE manual', 'FERC license',  # 0, 1
              'Constant', 'Seasonal', 'Conditional', 'Multi-location',  # 2, 3, 4, 5
              'Full', 'Partial', 'Value-only', 'Wrong']  # 6, 7, 8, 9
    
    # Define connections (source, target, value)
    sources = []
    targets = []
    values = []
    link_colors = []
    
    # Map labels to indices
    label_to_idx = {label: idx for idx, label in enumerate(labels)}
    
    # Doc Type → Pattern flows
    for _, row in flows_doc_pattern.iterrows():
        sources.append(label_to_idx[row['doc_type']])
        targets.append(label_to_idx[row['pattern']])
        values.append(row['count'])
        link_colors.append('rgba(0,0,0,0.2)')
    
    # Pattern → Completeness flows
    for _, row in flows_pattern_complete.iterrows():
        sources.append(label_to_idx[row['pattern']])
        targets.append(label_to_idx[row['completeness']])
        values.append(row['count'])
        link_colors.append('rgba(0,0,0,0.2)')
    
    # Create Sankey diagram
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=[f"{label}<br>(n={len(df[df['doc_type']==label]) if label in df['doc_type'].values else len(df[df['pattern']==label]) if label in df['pattern'].values else len(df[df['completeness']==label])})" 
                   for label in labels],
            color=['#8B4513', '#4682B4', '#90EE90', '#FFD700', '#FFA500', '#FF6347', '#228B22', '#DAA520', '#DC143C', '#808080']
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors
        )
    )])
    
    fig_sankey.update_layout(
        font=dict(size=16, family='Arial'),
        height=600,
        width=1200,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    
    fig_sankey.write_html('min_flow_information_richness_sankey.html')
    fig_sankey.write_image('min_flow_information_richness_sankey.png', width=1200, height=600)
    
    print("\n✅ Created: min_flow_information_richness_sankey.html")
    print("✅ Created: min_flow_information_richness_sankey.png")
    
except ImportError:
    print("\n⚠️  plotly not available, creating matplotlib version instead")
    
    # Create simplified matplotlib visualization
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Draw bars for each stage
    stage1_y = [0.75, 0.25]
    stage1_heights = [doc_types.get('USACE manual', 0), doc_types.get('FERC license', 0)]
    stage1_labels = [f"USACE manual\n(n={doc_types.get('USACE manual', 0)})", 
                     f"FERC license\n(n={doc_types.get('FERC license', 0)})"]
    
    stage2_y = [0.80, 0.60, 0.40, 0.20]
    stage2_heights = [patterns.get('Constant', 0), patterns.get('Seasonal', 0), 
                      patterns.get('Conditional', 0), patterns.get('Multi-location', 0)]
    stage2_labels = [f"Constant\n(n={patterns.get('Constant', 0)})", 
                     f"Seasonal\n(n={patterns.get('Seasonal', 0)})",
                     f"Conditional\n(n={patterns.get('Conditional', 0)})", 
                     f"Multi-location\n(n={patterns.get('Multi-location', 0)})"]
    
    stage3_y = [0.70, 0.45, 0.20]
    stage3_heights = [completeness.get('Full', 0), completeness.get('Partial', 0), 
                      completeness.get('Value-only', 0)]
    stage3_labels = [f"Full\n(n={completeness.get('Full', 0)})", 
                     f"Partial\n(n={completeness.get('Partial', 0)})", 
                     f"Value-only\n(n={completeness.get('Value-only', 0)})"]
    
    # Draw boxes
    box_width = 0.15
    for i, (y, h, l) in enumerate(zip(stage1_y, stage1_heights, stage1_labels)):
        ax.add_patch(plt.Rectangle((0.1, y-0.08), box_width, 0.16, 
                                   facecolor='lightblue', edgecolor='black', linewidth=2))
        ax.text(0.1 + box_width/2, y, l, ha='center', va='center', fontsize=10, fontweight='bold')
    
    for i, (y, h, l) in enumerate(zip(stage2_y, stage2_heights, stage2_labels)):
        ax.add_patch(plt.Rectangle((0.45, y-0.08), box_width, 0.16, 
                                   facecolor='lightyellow', edgecolor='black', linewidth=2))
        ax.text(0.45 + box_width/2, y, l, ha='center', va='center', fontsize=10, fontweight='bold')
    
    for i, (y, h, l) in enumerate(zip(stage3_y, stage3_heights, stage3_labels)):
        ax.add_patch(plt.Rectangle((0.8, y-0.08), box_width, 0.16, 
                                   facecolor='lightgreen', edgecolor='black', linewidth=2))
        ax.text(0.8 + box_width/2, y, l, ha='center', va='center', fontsize=10, fontweight='bold')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('Complex Pipeline: Minimum Flow Extraction Information Richness\n(Correct extractions only, n=38)', 
                 fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('min_flow_information_richness_diagram.png', dpi=300, bbox_inches='tight')
    print("\n✅ Created: min_flow_information_richness_diagram.png")

print("="*80)
