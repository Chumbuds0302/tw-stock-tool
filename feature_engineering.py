"""
feature_engineering.py - Phase 2 Feature Pipeline

OHLCV-derived features for ML training.
No leakage: all features use <= t data only.
"""

import pandas as pd
import numpy as np


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Compute RSI indicator."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, 
                 signal: int = 9) -> tuple:
    """Compute MACD, signal line, and histogram."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    
    return macd, macd_signal, macd_hist


def compute_stochastic_kd(high: pd.Series, low: pd.Series, close: pd.Series,
                          k_period: int = 9, d_period: int = 3) -> tuple:
    """Compute Stochastic %K and %D (optional feature)."""
    lowest_low = low.rolling(window=k_period, min_periods=k_period).min()
    highest_high = high.rolling(window=k_period, min_periods=k_period).max()
    
    k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    d = k.rolling(window=d_period, min_periods=d_period).mean()
    
    return k, d


def create_features(ohlcv_df: pd.DataFrame, include_target: bool = True,
                    lags: int = 3, add_kd: bool = False) -> pd.DataFrame:
    """
    Create ML features from OHLCV data.
    
    Args:
        ohlcv_df: DataFrame with Open, High, Low, Close, Volume columns
        include_target: Whether to add target column (next day up/down)
        lags: Number of lag periods for lag features (default 3)
        add_kd: Whether to include Stochastic KD features (default False)
        
    Returns:
        DataFrame with numeric features only, NaN-handled
    """
    if ohlcv_df is None or ohlcv_df.empty:
        return pd.DataFrame()
    
    df = ohlcv_df.copy()
    
    # Ensure required columns exist
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required:
        if col not in df.columns:
            return pd.DataFrame()
    
    features = pd.DataFrame(index=df.index)
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    # --- RSI(14) ---
    features['rsi_14'] = compute_rsi(close, 14)
    
    # --- MACD(12,26,9) ---
    macd, macd_signal, macd_hist = compute_macd(close, 12, 26, 9)
    features['macd'] = macd
    features['macd_signal'] = macd_signal
    features['macd_hist'] = macd_hist
    
    # --- Returns ---
    features['ret_1d'] = close.pct_change(1)
    features['ret_5d'] = close.pct_change(5)
    
    # --- Volatility (20-day rolling std of daily returns) ---
    features['volatility_20d'] = features['ret_1d'].rolling(window=20, min_periods=20).std()
    
    # --- Bias: (Close - MA20) / MA20 ---
    ma_20 = close.rolling(window=20, min_periods=20).mean()
    features['bias_20'] = (close - ma_20) / ma_20.replace(0, np.nan)
    
    # --- H-L Range ---
    features['hl_range'] = (high - low) / close.replace(0, np.nan)
    
    # --- Lag features ---
    for k in range(1, lags + 1):
        features[f'close_lag{k}'] = close.shift(k)
        features[f'volume_lag{k}'] = volume.shift(k)
        features[f'ret_1d_lag{k}'] = features['ret_1d'].shift(k)
    
    # --- Optional: Stochastic KD ---
    if add_kd:
        k, d = compute_stochastic_kd(high, low, close, 9, 3)
        features['stoch_k'] = k
        features['stoch_d'] = d
    
    # --- Target: 1 if next day close > today close, else 0 ---
    if include_target:
        next_close = close.shift(-1)
        features['target'] = (next_close > close).astype(float)
        # Last row target must be NaN (no future data)
        features.loc[features.index[-1], 'target'] = np.nan
    
    # Keep only numeric columns
    features = features.select_dtypes(include=[np.number])
    
    return features


def get_feature_columns(add_kd: bool = False) -> list:
    """Get list of feature column names (excluding target)."""
    cols = [
        'rsi_14', 'macd', 'macd_signal', 'macd_hist',
        'ret_1d', 'ret_5d', 'volatility_20d', 'bias_20', 'hl_range',
        'close_lag1', 'close_lag2', 'close_lag3',
        'volume_lag1', 'volume_lag2', 'volume_lag3',
        'ret_1d_lag1', 'ret_1d_lag2', 'ret_1d_lag3'
    ]
    if add_kd:
        cols.extend(['stoch_k', 'stoch_d'])
    return cols
