"""
analysis_engine.py - Phase 2 Analysis Layer

Integrates ML model for real prob_up predictions.
Falls back to 0.5 when model not available.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, Optional
from functools import lru_cache

import data_manager


# --- Constants ---
TOP_STOCKS = [
    "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW",
    "2881.TW", "2882.TW", "2891.TW", "2886.TW",
    "0050.TW", "0056.TW", "00878.TW"
]

SECTOR_MAP = {
    "全部 (All)": TOP_STOCKS,
    "半導體 (Semi)": ["2330.TW", "2454.TW", "2303.TW", "2308.TW"],
    "金融 (Finance)": ["2881.TW", "2882.TW", "2886.TW", "2891.TW"],
    "ETF": ["0050.TW", "0056.TW", "00878.TW", "00919.TW"]
}


# --- SignalSnapshot Dataclass ---
@dataclass
class SignalSnapshot:
    """Standardized signal output for UI display."""
    ticker: str
    name: str
    last_close: float
    direction: str
    prob_up: float
    confidence: float
    key_metrics: Dict
    model_used: bool = False
    
    def to_dict(self):
        return asdict(self)


# --- Model Loading with Caching ---
@lru_cache(maxsize=4)
def load_model_cached(model_path: str):
    """Load model payload with LRU caching."""
    try:
        import model_trainer
        return model_trainer.load_model_payload(model_path)
    except Exception as e:
        print(f"[Model] Failed to load: {e}")
        return None


# --- Key Metrics Computation ---
def compute_key_metrics(ohlcv_df: pd.DataFrame) -> Dict:
    """Compute OHLCV-derived metrics."""
    metrics = {
        "return_1d": None,
        "return_5d": None,
        "volatility_20d": None,
        "volume_ratio_20d": None
    }
    
    if ohlcv_df is None or ohlcv_df.empty or len(ohlcv_df) < 2:
        return metrics
    
    close = ohlcv_df['Close']
    volume = ohlcv_df['Volume']
    returns = close.pct_change()
    
    if len(returns) >= 2:
        metrics["return_1d"] = round(returns.iloc[-1] * 100, 2)
    
    if len(close) >= 6:
        metrics["return_5d"] = round((close.iloc[-1] / close.iloc[-6] - 1) * 100, 2)
    
    if len(returns) >= 20:
        metrics["volatility_20d"] = round(returns.tail(20).std() * 100, 2)
    
    if len(volume) >= 20:
        vol_avg_20 = volume.tail(20).mean()
        if vol_avg_20 > 0:
            metrics["volume_ratio_20d"] = round(volume.iloc[-1] / vol_avg_20, 2)
    
    return metrics


# --- Signal Snapshot Generator ---
def get_signal_snapshot(ticker: str, period: str = "6mo", 
                        model_path: str = None, add_kd: bool = False) -> tuple:
    """
    Generate SignalSnapshot with real prob_up if model available.
    
    Args:
        ticker: Stock ticker
        period: Data period
        model_path: Path to saved model (optional)
        add_kd: Whether to use KD features
        
    Returns:
        (SignalSnapshot, ohlcv_df, info_dict)
    """
    # Fetch data
    ohlcv_df, _ = data_manager.fetch_stock_history(ticker, period=period)
    info = data_manager.fetch_stock_info(ticker)
    
    # Get stock name
    name = info.get('longName', info.get('shortName', ''))
    if not name:
        name = data_manager.get_stock_name(ticker)
    
    # Last close price
    last_close = 0.0
    if not ohlcv_df.empty:
        last_close = float(ohlcv_df['Close'].iloc[-1])
    
    # Compute key metrics
    key_metrics = compute_key_metrics(ohlcv_df)
    
    # Get prob_up from model or fallback to 0.5
    prob_up = 0.5
    model_used = False
    
    if model_path:
        payload = load_model_cached(model_path)
        if payload is not None:
            try:
                import model_trainer
                prob_up = model_trainer.predict_proba_latest(
                    payload, ohlcv_df, add_kd=add_kd
                )
                model_used = True
            except Exception as e:
                print(f"[Predict] Error: {e}")
                prob_up = 0.5
    
    # Direction from prob_up
    if prob_up >= 0.5:
        direction = "UP"
    else:
        direction = "DOWN"
    
    # Confidence = abs(prob_up - 0.5) * 2, clipped to [0, 1]
    confidence = min(max(abs(prob_up - 0.5) * 2, 0.0), 1.0)
    
    snapshot = SignalSnapshot(
        ticker=ticker,
        name=name,
        last_close=last_close,
        direction=direction,
        prob_up=prob_up,
        confidence=confidence,
        key_metrics=key_metrics,
        model_used=model_used
    )
    
    return snapshot, ohlcv_df, info


# --- Recommendations (Ranked by prob_up) ---
def get_stock_recommendations(sector: str = "全部 (All)", model_path: str = None,
                               period: str = "6mo", top_n: int = 5,
                               add_kd: bool = False) -> Dict:
    """
    Get stock recommendations ranked by prob_up.
    
    Args:
        sector: Sector filter
        model_path: Path to saved model
        period: Data period
        top_n: Number of top picks to return
        add_kd: Whether to use KD features
        
    Returns:
        dict with 'top_picks' and 'warnings' lists
    """
    target_list = SECTOR_MAP.get(sector, TOP_STOCKS)
    
    results = []
    
    for ticker in target_list:
        try:
            snapshot, _, _ = get_signal_snapshot(
                ticker, period=period, model_path=model_path, add_kd=add_kd
            )
            if snapshot.last_close > 0:
                results.append({
                    'ticker': ticker,
                    'name': snapshot.name,
                    'prob_up': snapshot.prob_up,
                    'direction': snapshot.direction,
                    'price': snapshot.last_close
                })
        except Exception as e:
            print(f"[Scan] Skipping {ticker}: {e}")
            continue
    
    # Sort by prob_up descending
    results.sort(key=lambda x: x['prob_up'], reverse=True)
    
    # Top picks: prob_up >= 0.60
    top_picks = [r for r in results if r['prob_up'] >= 0.60][:top_n]
    
    # Warnings: prob_up <= 0.40
    warnings = [r for r in results if r['prob_up'] <= 0.40][:5]
    
    return {'top_picks': top_picks, 'warnings': warnings}
