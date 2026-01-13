"""
Create 4-model comparison figure showing complex pipeline performance across model sizes.
Shows extraction rate (stacked bars) and processing time (line) for 3B, 8B, 20B, and 70B models.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Model data from actual results
models = ['3B Llama 3.2', '8B Llama 3', '20B GPT-OSS', '70B Llama 3.3']
model_labels = ['3B<br>Llama 3.2', '8B<br>Llama 3', '20B<br>GPT-OSS', '70B<br>Llama 3.3']

# Accuracy from manual validation (Observed_LLM_comparison.csv)
correct_rates = [28.0, 26.0, 36.0, 76.0]  # From manual validation
wrong_rates = [72.0, 74.0, 64.0, 24.0]  # Complement to 100%

# Processing times (seconds per document)
processing_times = [71.4, 49.6, 138.2, 249.7]  # From timing files

# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add accuracy bars (stacked: correct + wrong)
fig.add_trace(
    go.Bar(
        name='Correct',
        x=model_labels,
        y=correct_rates,
        marker_color='#2ecc71',
        text=[f'{v:.0f}%' for v in correct_rates],
        textposition='inside',
        textfont=dict(size=14, color='white', family='Arial'),
        hovertemplate='<b>%{x}</b><br>Correct: %{y:.1f}%<extra></extra>'
    ),
    secondary_y=False
)

fig.add_trace(
    go.Bar(
        name='Wrong',
        x=model_labels,
        y=wrong_rates,
        marker_color='#e74c3c',
        text=[f'{v:.0f}%' for v in wrong_rates],
        textposition='inside',
        textfont=dict(size=14, color='white', family='Arial'),
        hovertemplate='<b>%{x}</b><br>Wrong: %{y:.1f}%<extra></extra>'
    ),
    secondary_y=False
)

# Add processing time line
fig.add_trace(
    go.Scatter(
        name='Processing Time',
        x=model_labels,
        y=processing_times,
        mode='lines+markers',
        line=dict(color='#c0392b', width=3),
        marker=dict(size=10, color='#c0392b', symbol='circle'),
        text=[f'{t:.1f}s' for t in processing_times],
        textposition='top center',
        textfont=dict(size=12, color='#c0392b', family='Arial'),
        hovertemplate='<b>%{x}</b><br>Time: %{y:.1f}s per document<extra></extra>'
    ),
    secondary_y=True
)

# Update layout
fig.update_xaxes(
    title_text="Model",
    title_font=dict(size=16, family='Arial'),
    tickfont=dict(size=14, family='Arial')
)

fig.update_yaxes(
    title_text="Accuracy (%)",
    title_font=dict(size=16, family='Arial'),
    tickfont=dict(size=14, family='Arial'),
    range=[0, 105],
    secondary_y=False
)

fig.update_yaxes(
    title_text="Processing Time (s/document)",
    title_font=dict(size=16, family='Arial'),
    tickfont=dict(size=14, family='Arial'),
    range=[0, max(processing_times) * 1.2],
    secondary_y=True
)

fig.update_layout(
    barmode='stack',
    width=1000,
    height=600,
    font=dict(size=14, family='Arial'),
    legend=dict(
        x=0.02,
        y=0.98,
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='rgba(0,0,0,0.2)',
        borderwidth=1,
        font=dict(size=14, family='Arial')
    ),
    plot_bgcolor='white',
    margin=dict(l=80, r=80, t=40, b=80),
    hovermode='x unified'
)

# Add grid
fig.update_xaxes(showgrid=False, showline=True, linewidth=2, linecolor='black', mirror=True)
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)', 
                 showline=True, linewidth=2, linecolor='black', mirror=True, secondary_y=False)
fig.update_yaxes(showgrid=False, showline=True, linewidth=2, linecolor='black', mirror=True, secondary_y=True)

# Save figure
fig.write_html('/home/fbg/Extract_LLM_FBA/figures/model_comparison.html')
fig.write_image('/home/fbg/Extract_LLM_FBA/figures/model_comparison.png', width=1000, height=600, scale=2)

print("✅ Figure saved:")
print("   - /home/fbg/Extract_LLM_FBA/figures/model_comparison.html")
print("   - /home/fbg/Extract_LLM_FBA/figures/model_comparison.png")
print("\nKey findings (manual validation):")
print(f"   • 70B model: {correct_rates[3]:.0f}% correct ({correct_rates[3]:.0f}/50), {processing_times[3]:.1f}s/doc")
print(f"   • 20B model: {correct_rates[2]:.0f}% correct ({correct_rates[2]*50/100:.0f}/50), {processing_times[2]:.1f}s/doc")
print(f"   • 8B model: {correct_rates[1]:.0f}% correct ({correct_rates[1]*50/100:.0f}/50), {processing_times[1]:.1f}s/doc")
print(f"   • 3B model: {correct_rates[0]:.0f}% correct ({correct_rates[0]*50/100:.0f}/50), {processing_times[0]:.1f}s/doc")
print("\n📊 Only 70B model achieves high accuracy (76%) with complex pipeline!")
