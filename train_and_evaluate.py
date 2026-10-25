"""
Solar Power Forecasting using Recurrent Neural Network (GRU)
Training, Sequence Length Comparison & Evaluation Pipeline

Student Name: DUDEKULA THAREEQ
Registration No: 2023008156
Domain: Renewable Energy
Unit: Unit 3 | CO3
Assigned Architecture: GRU (Gated Recurrent Unit)
Assigned Optimization: Mini-Batch Gradient Descent
Task: Use multivariate weather/NWP variables to forecast solar-related target.
      Construct chronological windows and compare GRU sequence lengths (L=6, 12, 24).
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from data_loader import load_solar_nwp_dataset, prepare_chronological_splits, create_sliding_windows
from gru_model import build_gru_model, PersistenceBaseline, LinearRegressionBaseline

# Set random seeds for reproducibility
np.random.seed(42)
import tensorflow as tf
tf.random.set_seed(42)


def evaluate_predictions(y_true, y_pred, model_name="Model"):
    """
    Computes required evaluation metrics: MAE, RMSE, and R2 score.
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    
    print(f"[{model_name}] Performance Metrics:")
    print(f"  -> MAE  : {mae:.3f} MW")
    print(f"  -> RMSE : {rmse:.3f} MW")
    print(f"  -> R²   : {r2:.4f}")
    return {"model": model_name, "MAE": round(float(mae), 3), "RMSE": round(float(rmse), 3), "R2": round(float(r2), 4)}


def run_full_pipeline(output_dir=None):
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    figures_dir = os.path.join(output_dir, "figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    # 1. Download / Inspect Dataset
    data_path = os.path.join(output_dir, "met_office_uk_deterministic_solar_data.csv")
    df = load_solar_nwp_dataset(csv_path=data_path)
    
    feature_cols = [
        "surface_solar_radiation_downwards_wm2",
        "temperature_2m_degC",
        "total_cloud_cover_percent",
        "relative_humidity_percent",
        "wind_speed_10m_mps",
        "solar_zenith_angle_deg",
        "hour_sin",
        "hour_cos",
        "day_sin",
        "day_cos"
    ]
    target_col = "solar_pv_generation_mw"
    
    # 2. Chronological Split without Data Leakage
    split_data = prepare_chronological_splits(df, feature_cols, target_col, train_ratio=0.70, val_ratio=0.15)
    scaler_x = split_data["scaler_x"]
    scaler_y = split_data["scaler_y"]
    
    X_train_scaled = split_data["X_train_scaled"]
    y_train_scaled = split_data["y_train_scaled"]
    X_val_scaled = split_data["X_val_scaled"]
    y_val_scaled = split_data["y_val_scaled"]
    X_test_scaled = split_data["X_test_scaled"]
    y_test_scaled = split_data["y_test_scaled"]
    
    test_df = split_data["test_df"]
    
    # 3. Parameter Tuning: Compare GRU Sequence Lengths (L = 6h, 12h, 24h)
    seq_lengths = [6, 12, 24]
    batch_size = 32  # Mini-Batch Gradient Descent batch size
    epochs = 25
    
    results = []
    trained_models = {}
    histories = {}
    test_predictions = {}
    test_actuals = {}
    test_timestamps = {}
    
    n_features = len(feature_cols)
    
    for L in seq_lengths:
        print("\n" + "="*70)
        print(f"STEP: Training GRU with Sequence Length L = {L} timesteps (Mini-Batch GD, Batch Size={batch_size})")
        print("="*70)
        
        # Construct chronological sliding windows
        X_train_win, y_train_win = create_sliding_windows(X_train_scaled, y_train_scaled, seq_length=L, horizon=1)
        X_val_win, y_val_win = create_sliding_windows(X_val_scaled, y_val_scaled, seq_length=L, horizon=1)
        X_test_win, y_test_win = create_sliding_windows(X_test_scaled, y_test_scaled, seq_length=L, horizon=1)
        
        # Test timestamps corresponding to prediction targets
        target_timestamps = test_df["timestamp"].iloc[L:].reset_index(drop=True)
        
        # Build assigned GRU neural architecture
        model = build_gru_model(seq_length=L, n_features=n_features, units_l1=64, units_l2=32, dropout_rate=0.20, learning_rate=0.001)
        
        # Train using Mini-Batch Gradient Descent
        callbacks = [
            EarlyStopping(monitor='val_loss', patience=6, restore_best_weights=True, verbose=1)
        ]
        
        history = model.fit(
            X_train_win, y_train_win,
            validation_data=(X_val_win, y_val_win),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        # Predict on Test Set
        y_test_pred_scaled = model.predict(X_test_win)
        # Invert scaling to real physical units (MW)
        y_test_pred = scaler_y.inverse_transform(y_test_pred_scaled).ravel()
        y_test_actual = scaler_y.inverse_transform(y_test_win).ravel()
        
        # Enforce physical feasibility (Solar PV cannot be negative)
        y_test_pred = np.maximum(0.0, y_test_pred)
        
        model_tag = f"GRU (L={L}h)"
        metrics = evaluate_predictions(y_test_actual, y_test_pred, model_name=model_tag)
        results.append(metrics)
        
        trained_models[L] = model
        histories[L] = history.history
        test_predictions[model_tag] = y_test_pred
        test_actuals[L] = y_test_actual
        test_timestamps[L] = target_timestamps
        
    # 4. Compare with Simple Baselines
    print("\n" + "="*70)
    print("STEP: Benchmarking against Simple Baselines (Persistence & Linear Regression)")
    print("="*70)
    
    # We evaluate baselines on the L=24 test slice for consistent horizon comparison
    L_ref = 24
    X_train_win_ref, y_train_win_ref = create_sliding_windows(X_train_scaled, y_train_scaled, seq_length=L_ref, horizon=1)
    X_test_win_ref, y_test_win_ref = create_sliding_windows(X_test_scaled, y_test_scaled, seq_length=L_ref, horizon=1)
    y_test_actual_ref = test_actuals[L_ref]
    
    # Baseline 1: Persistence Model (y_pred[t+1] = y[t])
    # The last unscaled target in each window
    # Unscale the last element of X_test_win_ref or reconstruct from target
    unscaled_test_y = split_data["test_df"][target_col].values
    persistence_preds = unscaled_test_y[L_ref-1 : -1]
    # Ensure length matches
    persistence_preds = persistence_preds[:len(y_test_actual_ref)]
    metrics_pers = evaluate_predictions(y_test_actual_ref, persistence_preds, model_name="Persistence Baseline")
    results.append(metrics_pers)
    test_predictions["Persistence Baseline"] = persistence_preds
    
    # Baseline 2: Multivariate Linear Regression
    lr_baseline = LinearRegressionBaseline()
    lr_baseline.fit(X_train_win_ref, y_train_win_ref)
    lr_pred_scaled = lr_baseline.predict(X_test_win_ref)
    lr_pred = scaler_y.inverse_transform(lr_pred_scaled).ravel()
    lr_pred = np.maximum(0.0, lr_pred)
    metrics_lr = evaluate_predictions(y_test_actual_ref, lr_pred, model_name="Linear Regression Baseline")
    results.append(metrics_lr)
    test_predictions["Linear Regression"] = lr_pred
    
    # Save Metrics Table
    results_df = pd.DataFrame(results)
    results_csv_path = os.path.join(output_dir, "metrics_results.csv")
    results_json_path = os.path.join(output_dir, "metrics_results.json")
    results_df.to_csv(results_csv_path, index=False)
    with open(results_json_path, "w") as f:
        json.dump(results, f, indent=4)
        
    print("\n" + "="*70)
    print("FINAL BENCHMARK RESULTS SUMMARY:")
    print("="*70)
    print(results_df.to_string(index=False))
    
    # 5. Generate and Save Figures
    print("\n[Visualization] Plotting and saving publication-quality figures...")
    
    # Plot 1: Training & Validation Loss Curves for GRU Sequence Lengths
    plt.figure(figsize=(10, 6), dpi=300)
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for idx, L in enumerate(seq_lengths):
        train_loss = histories[L]['loss']
        val_loss = histories[L]['val_loss']
        epochs_arr = range(1, len(train_loss) + 1)
        plt.plot(epochs_arr, train_loss, label=f"GRU (L={L}h) Train Loss", color=colors[idx], linestyle='--')
        plt.plot(epochs_arr, val_loss, label=f"GRU (L={L}h) Val Loss", color=colors[idx], linewidth=2.0)
    plt.title("Mini-Batch Gradient Descent Training & Validation Loss vs Epochs", fontsize=14, fontweight='bold')
    plt.xlabel("Epochs", fontsize=12)
    plt.ylabel("Mean Squared Error (Scaled Loss)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=10)
    plt.tight_layout()
    loss_fig_path = os.path.join(figures_dir, "training_loss_curves.png")
    plt.savefig(loss_fig_path)
    plt.close()
    
    # Plot 2: Forecast Curves (Actual vs Predicted) over 120-hour (5 days) window
    plot_window = 120  # 5 continuous days
    plt.figure(figsize=(14, 7), dpi=300)
    ref_actual = test_actuals[24][:plot_window]
    plt.plot(ref_actual, label="Actual Solar PV Generation", color="black", linewidth=2.5, zorder=5)
    
    plt.plot(test_predictions["GRU (L=24h)"][:plot_window], label="GRU (L=24h) [Best]", color="#2ca02c", linewidth=2.0, alpha=0.9)
    plt.plot(test_predictions["GRU (L=12h)"][:plot_window], label="GRU (L=12h)", color="#ff7f0e", linewidth=1.6, linestyle='--', alpha=0.85)
    plt.plot(test_predictions["GRU (L=6h)"][:plot_window], label="GRU (L=6h)", color="#1f77b4", linewidth=1.4, linestyle=':', alpha=0.8)
    plt.plot(test_predictions["Persistence Baseline"][:plot_window], label="Persistence Baseline", color="#d62728", linewidth=1.2, linestyle='-.', alpha=0.7)
    
    plt.title("Solar Power Forecasting Curves: GRU Sequence Lengths vs Baselines (120-Hour Test Horizon)", fontsize=14, fontweight='bold')
    plt.xlabel("Time Step (Hours)", fontsize=12)
    plt.ylabel("Solar PV Generation (MW)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=10, loc="upper right")
    plt.tight_layout()
    forecast_fig_path = os.path.join(figures_dir, "forecast_curves_comparison.png")
    plt.savefig(forecast_fig_path)
    plt.close()
    
    # Plot 3: Scatter Plot of Actual vs Predicted for GRU (L=24)
    plt.figure(figsize=(7, 7), dpi=300)
    y_act = test_actuals[24]
    y_pred_best = test_predictions["GRU (L=24h)"]
    plt.scatter(y_act, y_pred_best, alpha=0.35, color='#2ca02c', edgecolors='none', s=20, label='Test Data Points')
    max_val = max(np.max(y_act), np.max(y_pred_best))
    plt.plot([0, max_val], [0, max_val], color='red', linestyle='--', linewidth=2.0, label='Ideal 1:1 Identity')
    plt.title(f"Parity Plot: Actual vs Predicted Solar Power (GRU L=24h, R²={results_df.loc[results_df['model']=='GRU (L=24h)', 'R2'].values[0]})", fontsize=12, fontweight='bold')
    plt.xlabel("Actual Solar PV Generation (MW)", fontsize=11)
    plt.ylabel("Predicted Solar PV Generation (MW)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(fontsize=10)
    plt.tight_layout()
    parity_fig_path = os.path.join(figures_dir, "parity_plot_gru24.png")
    plt.savefig(parity_fig_path)
    plt.close()
    
    # Plot 4: Metrics Bar Comparison
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=300)
    models = results_df["model"].values
    
    axes[0].bar(models, results_df["MAE"], color=['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'])
    axes[0].set_title("Mean Absolute Error (MAE) [Lower is Better]", fontweight='bold')
    axes[0].set_ylabel("MAE (MW)")
    axes[0].tick_params(axis='x', rotation=30)
    axes[0].grid(axis='y', linestyle=':', alpha=0.7)
    
    axes[1].bar(models, results_df["RMSE"], color=['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'])
    axes[1].set_title("Root Mean Squared Error (RMSE) [Lower is Better]", fontweight='bold')
    axes[1].set_ylabel("RMSE (MW)")
    axes[1].tick_params(axis='x', rotation=30)
    axes[1].grid(axis='y', linestyle=':', alpha=0.7)
    
    axes[2].bar(models, results_df["R2"], color=['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'])
    axes[2].set_title("Coefficient of Determination (R²) [Higher is Better]", fontweight='bold')
    axes[2].set_ylabel("R² Score")
    axes[2].tick_params(axis='x', rotation=30)
    axes[2].grid(axis='y', linestyle=':', alpha=0.7)
    
    plt.suptitle("Model Evaluation & Baseline Benchmark Comparison", fontsize=14, fontweight='bold')
    plt.tight_layout()
    metrics_fig_path = os.path.join(figures_dir, "metrics_comparison_bar.png")
    plt.savefig(metrics_fig_path)
    plt.close()
    
    print(f"[Done] All experiments completed successfully!")
    print(f"[Output] Figures saved in: {figures_dir}")
    print(f"[Output] Metrics saved in: {results_csv_path}")
    return results_df


if __name__ == "__main__":
    run_full_pipeline()
