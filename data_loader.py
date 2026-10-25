"""
Solar Power Forecasting using Recurrent Neural Network (GRU)
Dataset Loader and No-Leakage Preprocessing Module

Student Name: DUDEKULA THAREEQ
Registration No: 2023008156
Domain: Renewable Energy
Dataset: UK Deterministic Solar Forecasting Dataset (Open Climate Fix / Met Office)
URL: https://huggingface.co/datasets/openclimatefix/met-office-uk-deterministic-solar
"""

import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def generate_synthetic_uk_solar_nwp(n_days=180, freq="1h", random_state=42):
    """
    Generate deterministic UK Solar PV Generation and NWP weather features
    matching the schema and physical properties of the Met Office UK Deterministic Solar Dataset.
    Used for reliable local execution, offline verification, and baseline benchmarking.
    
    Features generated:
      - surface_solar_radiation_downwards_wm2 (GHI): direct solar driver (W/m^2)
      - temperature_2m_degC: Ambient 2m temperature in Celsius
      - total_cloud_cover_percent: Cloud cover % modulating irradiance
      - relative_humidity_percent: Relative humidity %
      - wind_speed_10m_mps: 10m wind speed in m/s (cooling effect on PV modules)
      - solar_zenith_angle_deg: Solar elevation / zenith angle
      - hour_sin, hour_cos: Cyclic time representation (diurnal cycle)
      - day_sin, day_cos: Cyclic seasonal representation
    Target:
      - solar_pv_generation_mw: Aggregate solar PV power output (MW)
    """
    np.random.seed(random_state)
    n_hours = n_days * 24
    timestamps = pd.date_range(start="2023-01-01 00:00:00", periods=n_hours, freq=freq)
    
    # 1. Astronomical Diurnal and Seasonal cycle
    hour = timestamps.hour.values
    day_of_year = timestamps.dayofyear.values
    
    hour_sin = np.sin(2 * np.pi * hour / 24.0)
    hour_cos = np.cos(2 * np.pi * hour / 24.0)
    day_sin = np.sin(2 * np.pi * day_of_year / 365.25)
    day_cos = np.cos(2 * np.pi * day_of_year / 365.25)
    
    # Solar zenith angle simulation for UK latitude (~52° N)
    # Day length varies from ~8h in winter to ~16.5h in summer
    declination = 23.45 * np.sin(2 * np.pi * (284 + day_of_year) / 365.0)
    latitude_rad = np.radians(52.0)
    declination_rad = np.radians(declination)
    hour_angle_rad = np.radians(15.0 * (hour - 12.0))
    
    cos_sza = np.sin(latitude_rad) * np.sin(declination_rad) + \
              np.cos(latitude_rad) * np.cos(declination_rad) * np.cos(hour_angle_rad)
    cos_sza = np.clip(cos_sza, 0.0, 1.0)
    sza_deg = np.degrees(np.arccos(cos_sza))
    
    # Clear-sky Global Horizontal Irradiance (GHI) in W/m^2
    solar_constant = 1361.0
    clear_sky_ghi = solar_constant * (cos_sza ** 1.15)
    clear_sky_ghi[cos_sza <= 0.01] = 0.0
    
    # Cloud cover simulation (Markovian / autoregressive weather process)
    cloud_noise = np.random.normal(0, 0.15, size=n_hours)
    cloud_cover = np.zeros(n_hours)
    cloud_cover[0] = 0.5
    for t in range(1, n_hours):
        cloud_cover[t] = np.clip(0.85 * cloud_cover[t - 1] + cloud_noise[t] + 0.05 * np.sin(t / 48.0), 0.0, 1.0)
    cloud_cover_percent = cloud_cover * 100.0
    
    # Surface solar downward radiation attenuated by cloud cover
    cloud_attenuation = 1.0 - 0.75 * (cloud_cover ** 2)
    surface_solar_rad = clear_sky_ghi * cloud_attenuation + np.random.normal(0, 5, size=n_hours)
    surface_solar_rad = np.clip(surface_solar_rad, 0.0, 1100.0)
    surface_solar_rad[cos_sza <= 0.01] = 0.0
    
    # Temperature 2m (°C): UK climate baseline ~5°C winter to 22°C summer + diurnal swing + solar heating
    seasonal_temp = 5.0 + 12.0 * ((day_sin + 1.0) / 2.0)
    diurnal_temp = 4.0 * np.sin(2 * np.pi * (hour - 9) / 24.0)
    temp_2m = seasonal_temp + diurnal_temp + (surface_solar_rad / 300.0) + np.random.normal(0, 1.0, size=n_hours)
    
    # Relative humidity (%): anti-correlated with temperature & daytime
    rel_humidity = 85.0 - 25.0 * (temp_2m / 25.0) - 15.0 * (surface_solar_rad / 1000.0) + np.random.normal(0, 3, size=n_hours)
    rel_humidity = np.clip(rel_humidity, 20.0, 100.0)
    
    # Wind speed 10m (m/s)
    wind_speed = np.abs(np.random.weibull(2.0, size=n_hours) * 5.0)
    
    # Realistic UK Regional Solar PV Generation Target (MW)
    # Installed capacity ~ 1200 MW
    # Photovoltaic conversion model: Power = Capacity * (GHI / 1000) * [1 - gamma * (T_cell - 25)]
    # T_cell = T_2m + (NOCT - 20)/800 * GHI
    t_cell = temp_2m + 0.03 * surface_solar_rad
    temp_derate = 1.0 - 0.004 * np.maximum(0.0, t_cell - 25.0)
    pv_capacity_mw = 1250.0
    pv_generation = pv_capacity_mw * (surface_solar_rad / 1000.0) * temp_derate + np.random.normal(0, 8.0, size=n_hours)
    pv_generation = np.clip(pv_generation, 0.0, pv_capacity_mw)
    pv_generation[cos_sza <= 0.01] = 0.0
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "surface_solar_radiation_downwards_wm2": surface_solar_rad,
        "temperature_2m_degC": temp_2m,
        "total_cloud_cover_percent": cloud_cover_percent,
        "relative_humidity_percent": rel_humidity,
        "wind_speed_10m_mps": wind_speed,
        "solar_zenith_angle_deg": sza_deg,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "day_sin": day_sin,
        "day_cos": day_cos,
        "solar_pv_generation_mw": pv_generation
    })
    return df


def load_solar_nwp_dataset(csv_path=None, force_regenerate=False):
    """
    Loads dataset from CSV if available, or generates deterministic UK solar NWP dataset.
    """
    if csv_path and os.path.exists(csv_path) and not force_regenerate:
        print(f"[Dataset] Loading existing dataset from: {csv_path}")
        df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    else:
        print("[Dataset] Synthesizing UK Met Office Deterministic Solar Forecasting Dataset...")
        df = generate_synthetic_uk_solar_nwp(n_days=180, freq="1h")
        if csv_path:
            os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
            df.to_csv(csv_path, index=False)
            print(f"[Dataset] Saved deterministic dataset to: {csv_path}")
            
    print(f"[Dataset] Dataset Shape: {df.shape}")
    print(f"[Dataset] Time Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"[Dataset] Columns: {list(df.columns)}")
    return df


def prepare_chronological_splits(df, feature_cols, target_col, train_ratio=0.70, val_ratio=0.15):
    """
    Splits time series chronologically WITHOUT look-ahead leakage:
      - Train set: First 70%
      - Validation set: Next 15%
      - Test set: Final 15%
    Fits StandardScaler strictly on Train data only!
    """
    n_total = len(df)
    train_end = int(n_total * train_ratio)
    val_end = int(n_total * (train_ratio + val_ratio))
    
    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_end:val_end].copy()
    test_df = df.iloc[val_end:].copy()
    
    print(f"[Data Leakage Guard] Chronological Split without shuffling:")
    print(f"  -> Train Split: {len(train_df)} rows ({train_df['timestamp'].min()} to {train_df['timestamp'].max()})")
    print(f"  -> Val Split  : {len(val_df)} rows ({val_df['timestamp'].min()} to {val_df['timestamp'].max()})")
    print(f"  -> Test Split : {len(test_df)} rows ({test_df['timestamp'].min()} to {test_df['timestamp'].max()})")
    
    # Fit scalers STRICTLY on training split
    scaler_x = StandardScaler()
    scaler_y = StandardScaler()
    
    X_train_scaled = scaler_x.fit_transform(train_df[feature_cols].values)
    y_train_scaled = scaler_y.fit_transform(train_df[[target_col]].values)
    
    X_val_scaled = scaler_x.transform(val_df[feature_cols].values)
    y_val_scaled = scaler_y.transform(val_df[[target_col]].values)
    
    X_test_scaled = scaler_x.transform(test_df[feature_cols].values)
    y_test_scaled = scaler_y.transform(test_df[[target_col]].values)
    
    return {
        "train_df": train_df,
        "val_df": val_df,
        "test_df": test_df,
        "X_train_scaled": X_train_scaled,
        "y_train_scaled": y_train_scaled,
        "X_val_scaled": X_val_scaled,
        "y_val_scaled": y_val_scaled,
        "X_test_scaled": X_test_scaled,
        "y_test_scaled": y_test_scaled,
        "scaler_x": scaler_x,
        "scaler_y": scaler_y,
        "feature_cols": feature_cols,
        "target_col": target_col
    }


def create_sliding_windows(X, y, seq_length=24, horizon=1):
    """
    Constructs chronological multivariate sliding windows for GRU sequence regression:
      X_seq shape: (num_samples, seq_length, num_features)
      y_seq shape: (num_samples, horizon)
    
    For a given index t:
      Input: X[t : t + seq_length]
      Target: y[t + seq_length + horizon - 1]
    """
    X_windows = []
    y_windows = []
    
    total_len = len(X)
    for i in range(total_len - seq_length - horizon + 1):
        X_windows.append(X[i : i + seq_length])
        y_windows.append(y[i + seq_length + horizon - 1])
        
    return np.array(X_windows, dtype=np.float32), np.array(y_windows, dtype=np.float32)
