"""
model_trainer.py - Phase 2 Model Training

RandomForest baseline with chronological split.
Supports pooled training from multiple tickers.
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

import feature_engineering


def time_series_train_test_split(feature_df: pd.DataFrame, test_size: float = 0.2,
                                  target_col: str = "target") -> tuple:
    """
    Chronological train/test split (no shuffle).
    
    Args:
        feature_df: DataFrame with features and target
        test_size: Fraction for test set
        target_col: Name of target column
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    # Drop rows with NaN target
    df = feature_df.dropna(subset=[target_col]).copy()
    df = df.sort_index()
    
    # Split point
    n = len(df)
    split_idx = int(n * (1 - test_size))
    
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    # Separate features and target
    feature_cols = [c for c in df.columns if c != target_col]
    
    X_train = train_df[feature_cols]
    X_test = test_df[feature_cols]
    y_train = train_df[target_col]
    y_test = test_df[target_col]
    
    return X_train, X_test, y_train, y_test


def get_rf_params(n_rows: int) -> dict:
    """
    Get RandomForest parameters with dynamic adjustment for small datasets.
    
    Args:
        n_rows: Number of effective training rows
        
    Returns:
        dict of RF parameters
    """
    if n_rows < 1000:
        # Conservative params for small datasets
        return {
            'n_estimators': 50,
            'max_depth': 5,
            'min_samples_leaf': 10,
            'max_features': 'sqrt',
            'random_state': 42,
            'n_jobs': -1
        }
    else:
        # Standard params for larger datasets
        return {
            'n_estimators': 100,
            'max_depth': None,
            'min_samples_leaf': 2,
            'max_features': 'sqrt',
            'random_state': 42,
            'n_jobs': -1
        }


def train_random_forest(data, target_col: str = "target", test_size: float = 0.2,
                         add_kd: bool = False) -> dict:
    """
    Train RandomForest classifier.
    
    Args:
        data: One of:
            - Single DataFrame with features + target
            - List of OHLCV DataFrames (will compute features)
            - List of feature DataFrames (will concatenate)
        target_col: Name of target column
        test_size: Test set fraction
        add_kd: Whether to include KD features
        
    Returns:
        dict with 'model', 'metrics', 'feature_cols', 'train_rows', 'test_rows'
    """
    # Handle different input types
    if isinstance(data, list):
        # List of DataFrames - check if they are OHLCV or feature DFs
        dfs = []
        for i, df in enumerate(data):
            if df is None or df.empty:
                continue
            
            # Check if this is OHLCV (has Close but no target) or feature DF
            if 'Close' in df.columns and target_col not in df.columns:
                # OHLCV - compute features
                feat_df = feature_engineering.create_features(df, include_target=True, add_kd=add_kd)
                if not feat_df.empty:
                    dfs.append(feat_df)
            else:
                # Already feature DF
                dfs.append(df)
        
        if not dfs:
            return {'model': None, 'metrics': {}, 'feature_cols': [], 'error': 'No valid data'}
        
        # Concatenate and sort by date
        combined_df = pd.concat(dfs, ignore_index=False)
        combined_df = combined_df.sort_index()
    else:
        # Single DataFrame
        if 'Close' in data.columns and target_col not in data.columns:
            combined_df = feature_engineering.create_features(data, include_target=True, add_kd=add_kd)
        else:
            combined_df = data.copy()
    
    if combined_df.empty:
        return {'model': None, 'metrics': {}, 'feature_cols': [], 'error': 'Empty dataset'}
    
    # Drop NaN targets and features
    combined_df = combined_df.dropna()
    
    if len(combined_df) < 50:
        return {'model': None, 'metrics': {}, 'feature_cols': [], 
                'error': f'Too few rows: {len(combined_df)}'}
    
    # Split
    X_train, X_test, y_train, y_test = time_series_train_test_split(
        combined_df, test_size=test_size, target_col=target_col
    )
    
    # Get dynamic params based on training size
    rf_params = get_rf_params(len(X_train))
    
    # Train
    model = RandomForestClassifier(**rf_params)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    
    # ROC AUC (may fail if only one class)
    try:
        if len(y_proba.shape) > 1 and y_proba.shape[1] > 1:
            roc_auc = roc_auc_score(y_test, y_proba[:, 1])
        else:
            roc_auc = np.nan
    except Exception:
        roc_auc = np.nan
    
    feature_cols = [c for c in combined_df.columns if c != target_col]
    
    return {
        'model': model,
        'metrics': {
            'accuracy': round(accuracy, 4),
            'roc_auc': round(roc_auc, 4) if not np.isnan(roc_auc) else None
        },
        'feature_cols': feature_cols,
        'train_rows': len(X_train),
        'test_rows': len(X_test),
        'rf_params': rf_params
    }


def save_model(model, model_path: str, feature_cols: list, metadata: dict = None):
    """
    Save model with payload for future loading.
    
    Args:
        model: Trained sklearn model
        model_path: Path to save
        feature_cols: List of feature column names
        metadata: Optional metadata dict
    """
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    
    payload = {
        'model_type': 'sklearn_rf',
        'model': model,
        'feature_cols': feature_cols,
        'metadata': metadata or {
            'feature_set_version': 'v1',
            'trained_at': datetime.now().isoformat()
        }
    }
    
    joblib.dump(payload, model_path)
    print(f"[Model] Saved to {model_path}")


def load_model_payload(model_path: str) -> dict:
    """Load model payload from disk."""
    if not Path(model_path).exists():
        return None
    
    try:
        payload = joblib.load(model_path)
        return payload
    except Exception as e:
        print(f"[Model] Error loading {model_path}: {e}")
        return None


def load_model(model_path: str):
    """Load just the estimator from model payload."""
    payload = load_model_payload(model_path)
    if payload:
        return payload.get('model')
    return None


def predict_proba_latest(model_or_payload, ohlcv_df: pd.DataFrame, 
                          feature_cols: list = None, add_kd: bool = False) -> float:
    """
    Predict P(up) for the latest row of OHLCV data.
    
    Args:
        model_or_payload: sklearn model or payload dict
        ohlcv_df: OHLCV DataFrame
        feature_cols: Feature columns (required if model is not payload)
        add_kd: Whether to include KD features
        
    Returns:
        P(up) probability, or 0.5 on failure
    """
    try:
        # Handle payload vs raw model
        if isinstance(model_or_payload, dict):
            model = model_or_payload.get('model')
            cols = model_or_payload.get('feature_cols', feature_cols)
        else:
            model = model_or_payload
            cols = feature_cols
        
        if model is None or cols is None:
            return 0.5
        
        # Compute features (no target needed)
        feat_df = feature_engineering.create_features(ohlcv_df, include_target=False, add_kd=add_kd)
        
        if feat_df.empty:
            return 0.5
        
        # Get latest row
        latest = feat_df.iloc[[-1]]
        
        # Align columns
        missing_cols = set(cols) - set(latest.columns)
        for col in missing_cols:
            latest[col] = 0
        
        latest = latest[cols]
        
        # Handle NaN
        if latest.isnull().any().any():
            latest = latest.fillna(0)
        
        # Predict
        proba = model.predict_proba(latest)
        
        # Return P(up) - class 1
        if len(proba.shape) > 1 and proba.shape[1] > 1:
            return float(proba[0, 1])
        else:
            return 0.5
            
    except Exception as e:
        print(f"[Predict] Error: {e}")
        return 0.5


def fit_from_pooled(ohlcv_list: list, model_out_path: str, 
                    test_size: float = 0.2, add_kd: bool = False) -> dict:
    """
    Train model from pooled OHLCV data and save.
    
    Args:
        ohlcv_list: List of OHLCV DataFrames
        model_out_path: Path to save model
        test_size: Test set fraction
        add_kd: Whether to include KD features
        
    Returns:
        Training result dict
    """
    result = train_random_forest(ohlcv_list, test_size=test_size, add_kd=add_kd)
    
    if result.get('model') is not None:
        metadata = {
            'feature_set_version': 'v1',
            'trained_at': datetime.now().isoformat(),
            'train_rows': result['train_rows'],
            'test_rows': result['test_rows'],
            'metrics': result['metrics'],
            'rf_params': result.get('rf_params', {})
        }
        save_model(result['model'], model_out_path, result['feature_cols'], metadata)
    
    return result
