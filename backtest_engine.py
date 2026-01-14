"""
backtest_engine.py - Phase 2 Simple Backtest

Probability-driven backtest with buy/sell thresholds.
"""

import pandas as pd
import numpy as np

import feature_engineering
import model_trainer


def run_backtest(ohlcv_df: pd.DataFrame, model_or_payload,
                 buy_threshold: float = 0.60, sell_threshold: float = 0.40,
                 add_kd: bool = False) -> dict:
    """
    Run simple backtest on OHLCV data using model predictions.
    
    Rules:
    - If NOT holding and P(up) > buy_threshold -> BUY
    - If holding and P(up) < sell_threshold -> SELL
    
    Args:
        ohlcv_df: OHLCV DataFrame
        model_or_payload: Model or payload dict
        buy_threshold: P(up) threshold to buy
        sell_threshold: P(up) threshold to sell
        add_kd: Whether to include KD features
        
    Returns:
        dict with total_return, win_rate, max_drawdown, num_trades
    """
    result = {
        'total_return': 0.0,
        'win_rate': 0.0,
        'max_drawdown': 0.0,
        'num_trades': 0,
        'error': None
    }
    
    if ohlcv_df is None or ohlcv_df.empty or len(ohlcv_df) < 50:
        result['error'] = 'Insufficient data'
        return result
    
    # Get model and feature cols from payload
    if isinstance(model_or_payload, dict):
        model = model_or_payload.get('model')
        feature_cols = model_or_payload.get('feature_cols')
    else:
        model = model_or_payload
        feature_cols = feature_engineering.get_feature_columns(add_kd)
    
    if model is None:
        result['error'] = 'No model provided'
        return result
    
    # Compute features
    feat_df = feature_engineering.create_features(ohlcv_df, include_target=False, add_kd=add_kd)
    
    if feat_df.empty or len(feat_df) < 50:
        result['error'] = 'Failed to compute features'
        return result
    
    # Align columns
    missing_cols = set(feature_cols) - set(feat_df.columns)
    for col in missing_cols:
        feat_df[col] = 0
    
    feat_df = feat_df[feature_cols].fillna(0)
    close = ohlcv_df.loc[feat_df.index, 'Close']
    
    # Predict probabilities for all rows
    try:
        probas = model.predict_proba(feat_df)
        if len(probas.shape) > 1 and probas.shape[1] > 1:
            prob_up = probas[:, 1]
        else:
            prob_up = np.full(len(feat_df), 0.5)
    except Exception as e:
        result['error'] = f'Prediction failed: {e}'
        return result
    
    # --- Backtest simulation ---
    holding = False
    entry_price = 0.0
    trades = []
    portfolio_values = [1.0]  # Start with 1.0
    
    # TODO: Add fees/slippage in future versions
    
    for i in range(len(prob_up) - 1):
        current_price = close.iloc[i]
        next_price = close.iloc[i + 1]
        p = prob_up[i]
        
        if not holding:
            # Check buy signal
            if p > buy_threshold:
                holding = True
                entry_price = current_price
        else:
            # Check sell signal
            daily_return = (next_price - current_price) / current_price
            portfolio_values.append(portfolio_values[-1] * (1 + daily_return))
            
            if p < sell_threshold:
                # Sell
                exit_price = next_price
                trade_return = (exit_price - entry_price) / entry_price
                trades.append({
                    'entry': entry_price,
                    'exit': exit_price,
                    'return': trade_return
                })
                holding = False
    
    # Close any open position at end
    if holding and len(close) > 0:
        exit_price = close.iloc[-1]
        trade_return = (exit_price - entry_price) / entry_price
        trades.append({
            'entry': entry_price,
            'exit': exit_price,
            'return': trade_return
        })
    
    # Calculate metrics
    if trades:
        total_return = sum(t['return'] for t in trades)
        wins = sum(1 for t in trades if t['return'] > 0)
        win_rate = wins / len(trades)
    else:
        total_return = 0.0
        win_rate = 0.0
    
    # Max drawdown
    if len(portfolio_values) > 1:
        pv = np.array(portfolio_values)
        peaks = np.maximum.accumulate(pv)
        drawdowns = (pv - peaks) / peaks
        max_drawdown = abs(drawdowns.min())
    else:
        max_drawdown = 0.0
    
    result['total_return'] = round(total_return * 100, 2)  # as percentage
    result['win_rate'] = round(win_rate * 100, 2)  # as percentage
    result['max_drawdown'] = round(max_drawdown * 100, 2)  # as percentage
    result['num_trades'] = len(trades)
    
    return result
