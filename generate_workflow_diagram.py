"""
Generate Figure 1: Project Workflow Diagram for GITAM University ANN Template
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig_dir = r"C:\Users\dell\.gemini\antigravity\scratch\solar_power_forecasting_gru\figures"
os.makedirs(fig_dir, exist_ok=True)

fig, ax = plt.subplots(figsize=(13, 3.8), dpi=300)
ax.axis('off')

steps = [
    ("1. Problem Definition", "Renewable Solar PV\nSequence Regression\n(1-Hour Horizon)", "#e0f2fe", "#0284c7"),
    ("2. Dataset Ingestion", "UK Met Office NWP\n4,320 Hourly Records\n10 Weather Variables", "#f0fdf4", "#16a34a"),
    ("3. Preprocessing", "Anti-Leakage Split\nStandardScaler (Train)\nSliding Windows (L)", "#fef3c7", "#d97706"),
    ("4. GRU Architecture", "Stacked GRU (64, 32)\nDropout (0.20)\nDense (16) -> Linear (1)", "#ede9fe", "#7c3aed"),
    ("5. Mini-Batch GD", "Batch Size = 32\nAdam (lr = 0.001)\nEarlyStopping (Pat=6)", "#fee2e2", "#dc2626"),
    ("6. Multi-Experiments", "L = 6h, 12h, 24h\nvs Persistence\nvs Linear Regression", "#fdf4ff", "#c026d3"),
    ("7. Evaluation", "MAE, RMSE, R² Score\nForecast Curves\nGrid Feasibility", "#ecfdf5", "#059669")
]

x_start = 0.02
box_width = 0.115
box_height = 0.70
spacing = 0.024

for i, (title, desc, bg, border) in enumerate(steps):
    x = x_start + i * (box_width + spacing)
    y = 0.15
    rect = patches.FancyBboxPatch((x, y), box_width, box_height, boxstyle="round,pad=0.015,rounding_size=0.03",
                                  facecolor=bg, edgecolor=border, linewidth=2.0)
    ax.add_patch(rect)
    ax.text(x + box_width/2, y + box_height*0.75, title, ha='center', va='center',
            fontsize=8.5, fontweight='bold', color=border)
    ax.text(x + box_width/2, y + box_height*0.35, desc, ha='center', va='center',
            fontsize=7.5, color='#1e293b')
    
    # Arrow to next step
    if i < len(steps) - 1:
        ax.annotate("", xy=(x + box_width + spacing - 0.004, 0.50),
                    xytext=(x + box_width + 0.004, 0.50),
                    arrowprops=dict(arrowstyle="->", lw=2.2, color="#475569"))

plt.title("Figure 1: End-to-End Project Workflow Diagram for Solar Power Forecasting using GRU",
          fontsize=11.5, fontweight='bold', pad=12)
plt.tight_layout()
workflow_path = os.path.join(fig_dir, "project_workflow_diagram.png")
plt.savefig(workflow_path, bbox_inches='tight')
plt.close()
print("Saved:", workflow_path)
