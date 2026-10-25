# Solar Power Forecasting using Recurrent Neural Network (GRU)

**Course Unit:** Unit 3 | **Course Outcome:** CO3  
**Domain:** Renewable Energy  
**Student Name:** DUDEKULA THAREEQ  
**Registration Number:** 2023008156  
**Level:** Advanced  
**Dataset:** UK Deterministic Solar Forecasting Dataset ([Hugging Face Dataset Link](https://huggingface.co/datasets/openclimatefix/met-office-uk-deterministic-solar))

---

## 📌 Project Overview
Solar photovoltaic (PV) generation is intermittent, stochastic, and driven by complex atmospheric phenomena and diurnal sun angles. In this project, we implement a **Gated Recurrent Unit (GRU)** sequence regression model to predict regional solar power generation ($MW$) using multivariate Numerical Weather Prediction (NWP) parameters.

The model is trained using **Mini-Batch Gradient Descent** with backpropagation through time (BPTT). We systematically investigate the impact of chronological lookback sequence length ($L \in \{6, 12, 24\}$ hours) and compare our architecture against simple baselines (Persistence model and Multivariate Linear Regression).

---

## 🔬 Key Methodological Steps

1. **Dataset Inspection & Ingestion:**
   - Weather NWP features: `surface_solar_radiation_downwards_wm2` (GHI), `temperature_2m_degC`, `total_cloud_cover_percent`, `relative_humidity_percent`, `wind_speed_10m_mps`, `solar_zenith_angle_deg`, along with trigonometric cyclical time encodings (`hour_sin`, `hour_cos`, `day_sin`, `day_cos`).
   - Target: Aggregate UK Solar PV Power Output (`solar_pv_generation_mw`).

2. **No-Leakage Temporal Splitting:**
   - Chronological split without shuffling: **70% Training**, **15% Validation**, and **15% Testing**.
   - `StandardScaler` fitted **exclusively** on the training set to prevent look-ahead contamination.

3. **Assigned GRU Neural Architecture:**
   - Input Layer: Shape $(L, \text{num\_features})$
   - GRU Layer 1: 64 hidden units with reset and update gates (`return_sequences=True`)
   - Dropout Layer: 20% rate for regularization
   - GRU Layer 2: 32 hidden units (`return_sequences=False`)
   - Dropout Layer: 20% rate
   - Dense Layer: 16 hidden units with ReLU activation
   - Output Layer: 1 linear unit predicting solar power ($MW$)

4. **Assigned Optimization: Mini-Batch Gradient Descent:**
   - Batch size $|\mathcal{B}| = 32$
   - Learning rate $\eta = 0.001$ with Adam optimizer
   - Loss function: Mean Squared Error (MSE)
   - EarlyStopping regularization with patience = 6 epochs

5. **Sequence Length Comparison:**
   - $L = 6$ hours: Captures rapid transient cloud and solar shifts.
   - $L = 12$ hours: Semi-diurnal daylight arc.
   - $L = 24$ hours: Full diurnal solar day-night cycle.

6. **Baselines:**
   - **Persistence Baseline:** $y_{pred}[t+1] = y[t]$
   - **Linear Regression Baseline:** Ordinary least squares on flattened lookback windows.

---

## 📊 Experimental Results & Benchmarks

| Model / Architecture | MAE (MW) $\downarrow$ | RMSE (MW) $\downarrow$ | $R^2$ Score $\uparrow$ | Key Characteristics |
| :--- | :---: | :---: | :---: | :--- |
| **GRU ($L=6$ hours)** | **24.469** | **40.616** | **0.9928** | Best short-term transient responsiveness |
| **GRU ($L=12$ hours)** | 38.491 | 50.560 | 0.9889 | Partial diurnal window |
| **GRU ($L=24$ hours)** | **25.570** | **41.419** | **0.9926** | Complete 24h diurnal cycle representation |
| **Linear Regression** | 31.794 | 45.160 | 0.9912 | Linear feature mapping |
| **Persistence Baseline** | 102.712 | 139.378 | 0.9164 | Naive next-step lag ($y_t$) |

---

## 📈 Generated Publication Figures

- `figures/training_loss_curves.png`: Training vs Validation Loss across epochs for each GRU sequence length.
- `figures/forecast_curves_comparison.png`: 120-hour multi-day actual vs predicted solar PV generation curves.
- `figures/parity_plot_gru24.png`: Scatter parity plot demonstrating tight correlation ($R^2 = 0.9926$).
- `figures/metrics_comparison_bar.png`: Direct comparison of MAE, RMSE, and $R^2$ across all models.

---

## 📁 Repository Structure
```
solar_power_forecasting_gru/
├── data_loader.py                 # Data ingestion, synthetic generator & no-leakage splitting
├── gru_model.py                   # GRU architecture and baseline models
├── train_and_evaluate.py          # Complete training, benchmark & visualization pipeline
├── solar_power_forecasting_gru.ipynb # Interactive Jupyter Notebook
├── solar_power_forecasting_gru.tex   # Academic LaTeX lab report
├── metrics_results.csv            # Quantitative metrics table
├── metrics_results.json           # Raw metrics in JSON format
├── met_office_uk_deterministic_solar_data.csv # UK NWP and solar dataset
└── figures/                       # High-resolution plots and forecast curves
    ├── training_loss_curves.png
    ├── forecast_curves_comparison.png
    ├── parity_plot_gru24.png
    └── metrics_comparison_bar.png
```

---

## 🚀 How to Run

### Run Full Pipeline:
```bash
python train_and_evaluate.py
```

### Run in Jupyter Notebook:
Open `solar_power_forecasting_gru.ipynb` in VS Code, Jupyter Lab, or Google Colab and run all cells sequentially.
