import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os

# Load the data
data = pd.read_csv("MASTER.csv")

# Create plots directory if it doesn't exist
os.makedirs("plots", exist_ok=True)

# Define columns to exclude from radar chart
exclude_columns = ["work_load_type", "run_number", "seeds", "work_load_size", "prefix_frequency", "trie_type"]

# Get the metrics columns for the radar chart
metrics_columns = [col for col in data.columns if col not in exclude_columns]

# Calculate average values for each trie type
standard_trie_data = data[data['trie_type'] == 'Standard Trie'][metrics_columns].mean()
compressed_trie_data = data[data['trie_type'] == 'Compressed Trie'][metrics_columns].mean()

print("Standard Trie Data:")
print(standard_trie_data)
print("\nCompressed Trie Data:")
print(compressed_trie_data)

# Create a better normalization that shows relative performance
def normalize_for_radar(std_val, comp_val, lower_is_better=True):
    """Normalize two values to show relative performance on a 0-1 scale"""
    if lower_is_better:
        # For lower-is-better metrics, calculate performance ratio
        # Better performance gets closer to 1.0
        if std_val == 0 and comp_val == 0:
            return 0.5, 0.5
        elif std_val == 0:
            return 1.0, 0.0
        elif comp_val == 0:
            return 0.0, 1.0
        else:
            # Use ratio-based normalization
            std_perf = comp_val / std_val  # How much better comp is than std
            comp_perf = std_val / comp_val  # How much better std is than comp
            
            # Normalize to 0-1 scale
            total_perf = std_perf + comp_perf
            std_norm = comp_perf / total_perf
            comp_norm = std_perf / total_perf
    else:
        # For higher-is-better metrics
        if std_val == 0 and comp_val == 0:
            return 0.5, 0.5
        elif std_val == 0:
            return 0.0, 1.0
        elif comp_val == 0:
            return 1.0, 0.0
        else:
            # Use ratio-based normalization
            std_perf = std_val / comp_val  # How much better std is than comp
            comp_perf = comp_val / std_val  # How much better comp is than std
            
            # Normalize to 0-1 scale
            total_perf = std_perf + comp_perf
            std_norm = std_perf / total_perf
            comp_norm = comp_perf / total_perf
    
    return std_norm, comp_norm

# Normalize each metric
std_values = []
comp_values = []

print("\n=== NORMALIZATION DEBUG ===")
for metric in metrics_columns:
    std_val = standard_trie_data[metric]
    comp_val = compressed_trie_data[metric]
    
    if metric in ['memory_usage', 'node_count']:
        # Lower is better
        std_norm, comp_norm = normalize_for_radar(std_val, comp_val, lower_is_better=True)
    elif metric == 'avg_branching_factor':
        # Higher is better
        std_norm, comp_norm = normalize_for_radar(std_val, comp_val, lower_is_better=False)
    else:
        # Timing metrics - lower is better
        std_norm, comp_norm = normalize_for_radar(std_val, comp_val, lower_is_better=True)
    
    print(f"{metric}: std={std_norm:.3f}, comp={comp_norm:.3f}")
    
    std_values.append(std_norm)
    comp_values.append(comp_norm)

print(f"\nFinal Standard Values: {std_values}")
print(f"Final Compressed Values: {comp_values}")

# Create the radar chart
fig = go.Figure()

# Add Standard Trie trace
fig.add_trace(go.Scatterpolar(
    r=std_values,
    theta=metrics_columns,
    fill='toself',
    name='Standard Trie',
    line_color='blue',
    fillcolor='rgba(0, 100, 255, 0.3)',
    line=dict(width=2)
))

# Add Compressed Trie trace
fig.add_trace(go.Scatterpolar(
    r=comp_values,
    theta=metrics_columns,
    fill='toself',
    name='Compressed Trie',
    line_color='red',
    fillcolor='rgba(255, 0, 0, 0.3)',
    line=dict(width=2)
))

# Update layout
fig.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            range=[0, 1],
            tickfont=dict(size=10),
            tickmode='linear',
            tick0=0,
            dtick=0.2
        ),
        angularaxis=dict(
            tickfont=dict(size=12)
        )
    ),
    showlegend=True,
    title={
        'text': 'Trie Performance Comparison Radar Chart<br><sub>Values show relative performance (closer to 1.0 = better)</sub>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 16}
    },
    width=800,
    height=600,
    font=dict(size=12)
)

# Add annotations for better understanding
fig.add_annotation(
    text="<b>Note:</b> Values show relative performance where closer to 1.0 = better<br>" +
         "• Timing metrics: Lower actual values = better performance<br>" +
         "• Memory/Node count: Lower actual values = better performance<br>" +
         "• Branching factor: Higher actual values = better performance",
    xref="paper", yref="paper",
    x=0.02, y=0.02,
    showarrow=False,
    font=dict(size=10),
    bgcolor="rgba(255,255,255,0.8)",
    bordercolor="black",
    borderwidth=1
)

# Save the plot
fig.write_html("plots/radar_chart_performance_comparison.html")
fig.write_image("plots/radar_chart_performance_comparison.png", width=800, height=600)

print("Radar chart saved to plots/radar_chart_performance_comparison.html and .png")
print(f"Metrics included: {', '.join(metrics_columns)}")

# Display some statistics
print("\nPerformance Summary:")
print("=" * 50)
for i, metric in enumerate(metrics_columns):
    std_val = standard_trie_data[metric]
    comp_val = compressed_trie_data[metric]
    if metric in ['memory_usage', 'node_count']:
        improvement = ((std_val - comp_val) / std_val) * 100
        print(f"{metric}: Compressed uses {improvement:.1f}% less")
    elif metric == 'avg_branching_factor':
        improvement = ((comp_val - std_val) / std_val) * 100
        print(f"{metric}: Compressed has {improvement:.1f}% higher branching factor")
    else:
        improvement = ((std_val - comp_val) / std_val) * 100
        if improvement > 0:
            print(f"{metric}: Standard is {improvement:.1f}% faster")
        else:
            print(f"{metric}: Compressed is {abs(improvement):.1f}% faster")