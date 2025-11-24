import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

def add_technical_indicators(df):
    """
    Adds technical indicators to the dataframe.
    """
    if df.empty:
        return df

    # Moving Averages
    df['MA5'] = SMAIndicator(close=df['Close'], window=5).sma_indicator()
    df['MA20'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
    df['MA60'] = SMAIndicator(close=df['Close'], window=60).sma_indicator()

    # RSI
    df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()

    # MACD
    macd = MACD(close=df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Diff'] = macd.macd_diff()

    # Bollinger Bands
    bb = BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low'] = bb.bollinger_lband()
    df['BB_Mid'] = bb.bollinger_mavg()

    # KD (Stochastic Oscillator)
    from ta.momentum import StochasticOscillator
    stoch = StochasticOscillator(high=df['High'], low=df['Low'], close=df['Close'], window=9, smooth_window=3)
    df['K'] = stoch.stoch()
    df['D'] = stoch.stoch_signal()

    return df
