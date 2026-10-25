"""
Generate additional high-resolution diagrams for the 10-15 page formal report:
1. Neural Network Architecture Diagram (GRU cell + stacked network flow)
2. Feature Correlation Heatmap & Diurnal Distribution
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig_dir = r"C:\Users\dell\.gemini\antigravity\scratch\solar_power_forecasting_gru\figures"
os.makedirs(fig_dir, exist_ok=True)

# -------------------------------------------------------------
# 1. Neural Architecture Diagram
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
ax.axis('off')

# Diagram blocks
boxes = [
    ("Multivariate Input Window\nShape: (Batch, L, 10)\n[GHI, Temp, Cloud, RH, Wind, SZA, Timestamps]", 0.05, 0.4, 0.18, 0.35, "#e0f2fe", "#0284c7"),
    ("GRU Layer 1 (Assigned)\n64 Hidden Recurrent Units\nactivation='tanh'\nrecurrent_activation='sigmoid'\nreturn_sequences=True\nParams: 14,592", 0.28, 0.4, 0.18, 0.35, "#dbeafe", "#2563eb"),
    ("Spatial / Standard Dropout\nDropout Rate = 0.20\n(Regularization to prevent\nco-adaptation of recurrent weights)", 0.50, 0.55, 0.15, 0.22, "#fef3c7", "#d97706"),
    ("GRU Layer 2 (Assigned)\n32 Hidden Recurrent Units\nreturn_sequences=False\nParams: 9,408", 0.69, 0.4, 0.16, 0.35, "#ede9fe", "#7c3aed"),
    ("Dropout (Rate = 0.20)", 0.69, 0.15, 0.16, 0.15, "#fef3c7", "#d97706"),
    ("Dense Hidden Layer\n16 Nodes | Activation: ReLU\nParams: 528", 0.88, 0.55, 0.11, 0.22, "#dcfce7", "#16a34a"),
    ("Linear Output Layer\n1 Node | Activation: Linear\nTarget: Solar PV (MW)\nParams: 17", 0.88, 0.15, 0.11, 0.25, "#fee2e2", "#dc2626")
]

for text, x, y, w, h, bg, border in boxes:
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                  facecolor=bg, edgecolor=border, linewidth=2.0)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1e293b')

# Arrows connecting layers
arrow_props = dict(arrowstyle="->", lw=2.2, color="#475569")
ax.annotate("", xy=(0.28, 0.57), xytext=(0.23, 0.57), arrowprops=arrow_props)
ax.annotate("", xy=(0.50, 0.66), xytext=(0.46, 0.66), arrowprops=arrow_props)
ax.annotate("", xy=(0.69, 0.66), xytext=(0.65, 0.66), arrowprops=arrow_props)
ax.annotate("", xy=(0.77, 0.30), xytext=(0.77, 0.40), arrowprops=arrow_props)
ax.annotate("", xy=(0.88, 0.66), xytext=(0.85, 0.45), arrowprops=arrow_props)
ax.annotate("", xy=(0.93, 0.40), xytext=(0.93, 0.55), arrowprops=arrow_props)

# Internal GRU gate callout box at the bottom
callout = patches.FancyBboxPatch((0.05, 0.04), 0.58, 0.26, boxstyle="round,pad=0.02",
                                facecolor="#f8fafc", edgecolor="#64748b", linewidth=1.5, linestyle="--")
ax.add_patch(callout)
gru_eq_text = (
    "Internal GRU Cell Dynamics:\n"
    "• Reset Gate:       r_t = σ(W_xr x_t + W_hr h_{t-1} + b_r)\n"
    "• Update Gate:      z_t = σ(W_xz x_t + W_hz h_{t-1} + b_z)\n"
    "• Candidate State:  h~_t = tanh(W_xh x_t + W_hh (r_t ⊙ h_{t-1}) + b_h)\n"
    "• Hidden State:     h_t = (1 - z_t) ⊙ h_{t-1} + z_t ⊙ h~_t\n"
    "Optimization:       Mini-Batch Gradient Descent (Adam, Batch Size = 32, lr = 0.001)"
)
ax.text(0.07, 0.17, gru_eq_text, fontsize=8.5, family="monospace", va="center", color="#0f172a")

plt.title("Figure 1: Deep Gated Recurrent Unit (GRU) Neural Architecture with Internal Gating Dynamics", fontsize=12, fontweight='bold', pad=15)
plt.tight_layout()
arch_path = os.path.join(fig_dir, "gru_architecture_diagram.png")
plt.savefig(arch_path, bbox_inches='tight')
plt.close()
print("Saved:", arch_path)

# -------------------------------------------------------------
# 2. Dataset Correlation & Diurnal Distribution
# -------------------------------------------------------------
csv_path = r"C:\Users\dell\.gemini\antigravity\scratch\solar_power_forecasting_gru\met_office_uk_deterministic_solar_data.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)
    
    # Correlation heatmap of primary variables
    corr_cols = [
        "surface_solar_radiation_downwards_wm2",
        "temperature_2m_degC",
        "total_cloud_cover_percent",
        "relative_humidity_percent",
        "wind_speed_10m_mps",
        "solar_pv_generation_mw"
    ]
    labels = ["GHI (W/m²)", "Temp 2m (°C)", "Cloud (%)", "RH (%)", "Wind (m/s)", "PV Power (MW)"]
    corr = df[corr_cols].corr().values
    
    im = axes[0].imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    axes[0].set_xticks(range(len(labels)))
    axes[0].set_yticks(range(len(labels)))
    axes[0].set_xticklabels(labels, rotation=35, ha='right', fontsize=9)
    axes[0].set_yticklabels(labels, fontsize=9)
    for i in range(len(labels)):
        for j in range(len(labels)):
            axes[0].text(j, i, f"{corr[i, j]:.2f}", ha='center', va='center', color='black' if abs(corr[i, j]) < 0.6 else 'white', fontsize=9, fontweight='bold')
    axes[0].set_title("(a) Multivariate NWP Feature Correlation Matrix", fontsize=11, fontweight='bold')
    fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04)
    
    # Diurnal Solar Profile (Average generation by hour of day)
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    hourly_mean = df.groupby('hour')['solar_pv_generation_mw'].mean()
    hourly_std = df.groupby('hour')['solar_pv_generation_mw'].std()
    
    axes[1].plot(hourly_mean.index, hourly_mean.values, color='#f59e0b', linewidth=2.5, marker='o', label='Mean PV Power (MW)')
    axes[1].fill_between(hourly_mean.index, np.maximum(0, hourly_mean - hourly_std), hourly_mean + hourly_std, color='#fef3c7', alpha=0.6, label='±1 Std Dev (Weather Variability)')
    axes[1].set_title("(b) Diurnal Solar PV Generation Profile Across 24-Hour Cycle", fontsize=11, fontweight='bold')
    axes[1].set_xlabel("Hour of Day (UTC)", fontsize=10)
    axes[1].set_ylabel("Solar PV Generation (MW)", fontsize=10)
    axes[1].set_xticks(range(0, 24, 2))
    axes[1].grid(True, linestyle=":", alpha=0.6)
    axes[1].legend(fontsize=9)
    
    plt.tight_layout()
    corr_path = os.path.join(fig_dir, "dataset_correlation_and_diurnal_profile.png")
    plt.savefig(corr_path, bbox_inches='tight')
    plt.close()
    print("Saved:", corr_path)
