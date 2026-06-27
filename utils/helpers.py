"""
Trading Suite Pro - Motor Central
Funciones utilitarias para análisis técnico, backtesting, sentimiento y riesgo
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
import time
warnings.filterwarnings('ignore')


# ============================================
# OBTENCIÓN DE DATOS
# ============================================

@st.cache_data(ttl=300)
def obtener_datos(ticker: str, periodo: str = "1y") -> pd.DataFrame:
    """
    Obtiene datos históricos de Yahoo Finance con manejo robusto de errores
    """
    max_reintentos = 3
    intento = 0
    
    while intento < max_reintentos:
        try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period=periodo, auto_adjust=True)
            
            if data.empty:
                raise ValueError(f"No se encontraron datos para {ticker}")
            
            data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            data = data.dropna()
            
            if not isinstance(data.index, pd.DatetimeIndex):
                data.index = pd.to_datetime(data.index)
            
            return data
            
        except Exception as e:
            intento += 1
            if intento < max_reintentos:
                time.sleep(2 * intento)
                continue
            else:
                st.warning(
                    f"⚠️ **No se pudieron descargar datos de {ticker}**\n\n"
                    f"Error: {str(e)}\n\n"
                    f"Usando datos de demostración."
                )
                return _generar_datos_demo(ticker, periodo)


def _generar_datos_demo(ticker: str, periodo: str) -> pd.DataFrame:
    """Genera datos de demostración cuando Yahoo Finance no está disponible"""
    dias_map = {
        '1mo': 30, '3mo': 90, '6mo': 180, '1y': 365,
        '2y': 730, '5y': 1825, 'max': 3650
    }
    
    dias = dias_map.get(periodo, 365)
    np.random.seed(hash(ticker) % 2**32)
    
    fechas = pd.date_range(end=datetime.now(), periods=dias, freq='D')
    precio_base = np.random.uniform(50, 500)
    
    retornos = np.random.normal(0.0005, 0.02, dias)
    precios = precio_base * np.cumprod(1 + retornos)
    
    data = pd.DataFrame({
        'Open': precios * (1 + np.random.uniform(-0.01, 0.01, dias)),
        'High': precios * (1 + np.abs(np.random.normal(0, 0.015, dias))),
        'Low': precios * (1 - np.abs(np.random.normal(0, 0.015, dias))),
        'Close': precios,
        'Volume': np.random.randint(1000000, 50000000, dias)
    }, index=fechas)
    
    data['High'] = data[['Open', 'High', 'Close']].max(axis=1)
    data['Low'] = data[['Open', 'Low', 'Close']].min(axis=1)
    
    return data


# ============================================
# INDICADORES TÉCNICOS
# ============================================

def calcular_sma(data: pd.Series, periodo: int) -> pd.Series:
    """Simple Moving Average"""
    return data.rolling(window=periodo).mean()


def calcular_ema(data: pd.Series, periodo: int) -> pd.Series:
    """Exponential Moving Average"""
    return data.ewm(span=periodo, adjust=False).mean()


def calcular_rsi(data: pd.Series, periodo: int = 14) -> pd.Series:
    """Relative Strength Index"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calcular_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD (Moving Average Convergence Divergence)"""
    ema_fast = calcular_ema(data, fast)
    ema_slow = calcular_ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calcular_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calcular_bollinger_bands(data: pd.Series, periodo: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands"""
    sma = calcular_sma(data, periodo)
    std = data.rolling(window=periodo).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band


def calcular_estocastico(high: pd.Series, low: pd.Series, close: pd.Series, periodo: int = 14) -> Tuple[pd.Series, pd.Series]:
    """Stochastic Oscillator"""
    lowest_low = low.rolling(window=periodo).min()
    highest_high = high.rolling(window=periodo).max()
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=3).mean()
    return k_percent, d_percent


def calcular_atr(high: pd.Series, low: pd.Series, close: pd.Series, periodo: int = 14) -> pd.Series:
    """Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=periodo).mean()
    return atr


def calcular_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume"""
    obv = [0]
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=close.index)


def calcular_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume Weighted Average Price"""
    typical_price = (high + low + close) / 3
    cumulative_tp_vol = (typical_price * volume).cumsum()
    cumulative_vol = volume.cumsum()
    vwap = cumulative_tp_vol / cumulative_vol
    return vwap


# ============================================
# GENERACIÓN DE SEÑALES
# ============================================

def generar_senal_compra(data: pd.DataFrame) -> Dict:
    """Genera señales de compra basadas en múltiples indicadores"""
    señales = []
    puntuacion = 0
    
    rsi = calcular_rsi(data['Close'])
    if rsi.iloc[-1] < 30:
        señales.append("RSI en sobreventa")
        puntuacion += 2
    elif rsi.iloc[-1] < 40:
        señales.append("RSI cercano a sobreventa")
        puntuacion += 1
    
    macd_line, signal_line, _ = calcular_macd(data['Close'])
    if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        señales.append("Cruce alcista MACD")
        puntuacion += 3
    
    sma_50 = calcular_sma(data['Close'], 50)
    sma_200 = calcular_sma(data['Close'], 200)
    if sma_50.iloc[-1] > sma_200.iloc[-1] and sma_50.iloc[-2] <= sma_200.iloc[-2]:
        señales.append("Golden Cross (SMA 50 > SMA 200)")
        puntuacion += 3
    
    upper, middle, lower = calcular_bollinger_bands(data['Close'])
    if data['Close'].iloc[-1] < lower.iloc[-1]:
        señales.append("Precio por debajo de banda inferior de Bollinger")
        puntuacion += 2
    
    k, d = calcular_estocastico(data['High'], data['Low'], data['Close'])
    if k.iloc[-1] < 20 and d.iloc[-1] < 20:
        señales.append("Estocástico en sobreventa")
        puntuacion += 2
    
    return {
        'señales': señales,
        'puntuacion': puntuacion,
        'recomendacion': 'COMPRA' if puntuacion >= 5 else 'ESPERAR' if puntuacion >= 3 else 'NEUTRAL'
    }


def generar_senal_venta(data: pd.DataFrame) -> Dict:
    """Genera señales de venta basadas en múltiples indicadores"""
    señales = []
    puntuacion = 0
    
    rsi = calcular_rsi(data['Close'])
    if rsi.iloc[-1] > 70:
        señales.append("RSI en sobrecompra")
        puntuacion += 2
    elif rsi.iloc[-1] > 60:
        señales.append("RSI cercano a sobrecompra")
        puntuacion += 1
    
    macd_line, signal_line, _ = calcular_macd(data['Close'])
    if macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        señales.append("Cruce bajista MACD")
        puntuacion += 3
    
    sma_50 = calcular_sma(data['Close'], 50)
    sma_200 = calcular_sma(data['Close'], 200)
    if sma_50.iloc[-1] < sma_200.iloc[-1] and sma_50.iloc[-2] >= sma_200.iloc[-2]:
        señales.append("Death Cross (SMA 50 < SMA 200)")
        puntuacion += 3
    
    upper, middle, lower = calcular_bollinger_bands(data['Close'])
    if data['Close'].iloc[-1] > upper.iloc[-1]:
        señales.append("Precio por encima de banda superior de Bollinger")
        puntuacion += 2
    
    k, d = calcular_estocastico(data['High'], data['Low'], data['Close'])
    if k.iloc[-1] > 80 and d.iloc[-1] > 80:
        señales.append("Estocástico en sobrecompra")
        puntuacion += 2
    
    return {
        'señales': señales,
        'puntuacion': puntuacion,
        'recomendacion': 'VENTA' if puntuacion >= 5 else 'ESPERAR' if puntuacion >= 3 else 'NEUTRAL'
    }


# ============================================
# BACKTESTING
# ============================================

def estrategia_cruce_medias(data: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.DataFrame:
    """Estrategia de cruce de medias móviles"""
    df = data.copy()
    df['SMA_Fast'] = calcular_sma(df['Close'], fast)
    df['SMA_Slow'] = calcular_sma(df['Close'], slow)
    
    df['Signal'] = 0
    df.loc[df['SMA_Fast'] > df['SMA_Slow'], 'Signal'] = 1
    df.loc[df['SMA_Fast'] < df['SMA_Slow'], 'Signal'] = -1
    
    df['Position'] = df['Signal'].diff()
    return df


def estrategia_rsi(data: pd.DataFrame, periodo: int = 14, sobreventa: int = 30, sobrecompra: int = 70) -> pd.DataFrame:
    """Estrategia de reversión a la media con RSI"""
    df = data.copy()
    df['RSI'] = calcular_rsi(df['Close'], periodo)
    
    df['Signal'] = 0
    df.loc[df['RSI'] < sobreventa, 'Signal'] = 1
    df.loc[df['RSI'] > sobrecompra, 'Signal'] = -1
    
    df['Position'] = df['Signal'].diff()
    return df


def estrategia_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """Estrategia de cruce MACD"""
    df = data.copy()
    macd_line, signal_line, _ = calcular_macd(df['Close'], fast, slow, signal)
    df['MACD'] = macd_line
    df['Signal_Line'] = signal_line
    
    df['Signal'] = 0
    df.loc[df['MACD'] > df['Signal_Line'], 'Signal'] = 1
    df.loc[df['MACD'] < df['Signal_Line'], 'Signal'] = -1
    
    df['Position'] = df['Signal'].diff()
    return df


def estrategia_bollinger(data: pd.DataFrame, periodo: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """Estrategia de ruptura de Bandas de Bollinger"""
    df = data.copy()
    upper, middle, lower = calcular_bollinger_bands(df['Close'], periodo, std_dev)
    df['BB_Upper'] = upper
    df['BB_Middle'] = middle
    df['BB_Lower'] = lower
    
    df['Signal'] = 0
    df.loc[df['Close'] < lower, 'Signal'] = 1
    df.loc[df['Close'] > upper, 'Signal'] = -1
    
    df['Position'] = df['Signal'].diff()
    return df


def ejecutar_backtest(df: pd.DataFrame, capital_inicial: float = 10000, comision: float = 0.001) -> Dict:
    """Ejecuta backtest sobre una estrategia"""
    df = df.copy()
    df['Market_Returns'] = df['Close'].pct_change()
    df['Strategy_Returns'] = df['Market_Returns'] * df['Signal'].shift(1)
    
    trades = df[df['Position'] != 0]
    df.loc[trades.index, 'Strategy_Returns'] -= comision
    
    df['Equity'] = capital_inicial * (1 + df['Strategy_Returns']).cumprod()
    df['Buy_Hold'] = capital_inicial * (1 + df['Market_Returns']).cumprod()
    
    total_return = (df['Equity'].iloc[-1] / capital_inicial - 1) * 100
    buy_hold_return = (df['Buy_Hold'].iloc[-1] / capital_inicial - 1) * 100
    
    sharpe = np.sqrt(252) * df['Strategy_Returns'].mean() / df['Strategy_Returns'].std() if df['Strategy_Returns'].std() != 0 else 0
    
    downside_returns = df['Strategy_Returns'][df['Strategy_Returns'] < 0]
    sortino = np.sqrt(252) * df['Strategy_Returns'].mean() / downside_returns.std() if len(downside_returns) > 0 and downside_returns.std() != 0 else 0
    
    rolling_max = df['Equity'].expanding().max()
    drawdown = df['Equity'] / rolling_max - 1
    max_drawdown = drawdown.min() * 100
    
    calmar = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    winning_trades = df[df['Strategy_Returns'] > 0]
    losing_trades = df[df['Strategy_Returns'] < 0]
    win_rate = len(winning_trades) / (len(winning_trades) + len(losing_trades)) * 100 if (len(winning_trades) + len(losing_trades)) > 0 else 0
    
    num_trades = len(trades)
    
    return {
        'equity_curve': df['Equity'],
        'buy_hold_curve': df['Buy_Hold'],
        'total_return': total_return,
        'buy_hold_return': buy_hold_return,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'calmar_ratio': calmar,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'num_trades': num_trades,
        'final_capital': df['Equity'].iloc[-1]
    }


# ============================================
# ANÁLISIS DE SENTIMIENTO
# ============================================

def analizar_sentimiento_texto(texto: str) -> Dict:
    """Analiza sentimiento de un texto usando TextBlob y VADER"""
    from textblob import TextBlob
    from nltk.sentiment import SentimentIntensityAnalyzer
    import nltk
    
    try:
        sia = SentimentIntensityAnalyzer()
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
        sia = SentimentIntensityAnalyzer()
    
    blob = TextBlob(texto)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    
    vader_scores = sia.polarity_scores(texto)
    compound = vader_scores['compound']
    
    # ✅ UMBRALES MÁS PERMISIVOS para español
    # Priorizar VADER compound score
    if compound >= 0.1:  # Umbral más bajo
        sentimiento = 'POSITIVO'
    elif compound <= -0.1:  # Umbral más bajo
        sentimiento = 'NEGATIVO'
    # Si VADER es neutral, usar TextBlob polarity
    elif polarity > 0.1:
        sentimiento = 'POSITIVO'
    elif polarity < -0.1:
        sentimiento = 'NEGATIVO'
    else:
        sentimiento = 'NEUTRAL'
    
    return {
        'sentimiento': sentimiento,
        'compound': compound,
        'polarity': polarity,
        'subjectivity': subjectivity,
        'positive': vader_scores['pos'],
        'neutral': vader_scores['neu'],
        'negative': vader_scores['neg']
    }


def generar_datos_sentimiento_demo(ticker: str, dias: int = 30) -> pd.DataFrame:
    """
    Genera datos de demostración de sentimiento con titulares en inglés
    (VADER funciona mejor con inglés)
    """
    import random
    
    # Titulares POSITIVOS en inglés (VADER los detecta mejor)
    titulares_positivos = [
        f"{ticker} reports record-breaking earnings, beats all expectations",
        f"Analysts upgrade {ticker} to strong buy with highest price target",
        f"{ticker} announces massive expansion with billion-dollar investment",
        f"{ticker} stock soars to all-time high after excellent quarter",
        f"{ticker} launches revolutionary product that transforms industry",
        f"Institutional investors dramatically increase stake in {ticker}",
        f"{ticker} exceeds projections with outstanding growth",
        f"Experts name {ticker} as the best investment opportunity of the year",
        f"{ticker} achieves historic strategic partnership with tech giant",
        f"Unprecedented demand drives {ticker} sales to record levels",
        f"{ticker} posts exceptional profit margins, outperforms competitors",
        f"{ticker} receives prestigious industry award for innovation"
    ]
    
    # Titulares NEGATIVOS en inglés
    titulares_negativos = [
        f"{ticker} reports massive losses, disappoints investors",
        f"{ticker} stock plummets after terrible earnings report",
        f"{ticker} faces billion-dollar lawsuit for accounting fraud",
        f"Analysts downgrade {ticker} to sell with slashed price target",
        f"{ticker} announces massive layoffs and division closures",
        f"Regulators launch investigation into {ticker} illegal practices",
        f"{ticker} loses significant market share to competitors",
        f"Investors flee {ticker} following corporate scandal",
        f"{ticker} reports technical bankruptcy and financial crisis",
        f"Defective products trigger reputation crisis for {ticker}",
        f"{ticker} CEO resigns amid controversy and turmoil",
        f"{ticker} warns of severe downturn and revenue collapse"
    ]
    
    # Titulares NEUTRALES en inglés
    titulares_neutrales = [
        f"{ticker} releases quarterly report as scheduled",
        f"{ticker} board meeting scheduled for next month",
        f"{ticker} maintains current policies without changes",
        f"{ticker} completes routine system update",
        f"{ticker} publishes corporate events calendar",
        f"{ticker} holds annual shareholder meeting",
        f"{ticker} files standard regulatory documents",
        f"{ticker} announces routine maintenance schedule"
    ]
    
    fechas = [datetime.now() - timedelta(days=i) for i in range(dias)]
    datos = []
    
    for i, fecha in enumerate(fechas):
        # Distribución forzada: ~33% positivos, ~33% negativos, ~33% neutrales
        # Usar módulo para distribución uniforme
        if i % 3 == 0:
            titular = random.choice(titulares_positivos)
        elif i % 3 == 1:
            titular = random.choice(titulares_negativos)
        else:
            titular = random.choice(titulares_neutrales)
        
        sentimiento = analizar_sentimiento_texto(titular)
        datos.append({
            'fecha': fecha,
            'titular': titular,
            'sentimiento': sentimiento['sentimiento'],
            'compound': sentimiento['compound'],
            'polarity': sentimiento['polarity']
        })
    
    return pd.DataFrame(datos).sort_values('fecha')


# ============================================
# GESTIÓN DE RIESGO
# ============================================

def calcular_var_historico(returns: pd.Series, confianza: float = 0.95) -> float:
    """Calcula Value at Risk histórico"""
    var = np.percentile(returns, (1 - confianza) * 100)
    return var


def calcular_cvar(returns: pd.Series, confianza: float = 0.95) -> float:
    """Calcula Conditional Value at Risk (Expected Shortfall)"""
    var = calcular_var_historico(returns, confianza)
    cvar = returns[returns <= var].mean()
    return cvar


def simulacion_monte_carlo(returns: pd.Series, dias: int = 252, simulaciones: int = 1000, capital_inicial: float = 10000) -> pd.DataFrame:
    """Simulación de Monte Carlo para proyectar rendimientos futuros"""
    resultados = pd.DataFrame()
    
    for i in range(simulaciones):
        retornos_simulados = np.random.choice(returns, size=dias, replace=True)
        equity = capital_inicial * (1 + retornos_simulados).cumprod()
        resultados[f'Sim_{i+1}'] = equity
    
    return resultados


def calcular_matriz_correlacion(data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Calcula matriz de correlación entre múltiples activos"""
    returns = pd.DataFrame()
    for ticker, df in data.items():
        returns[ticker] = df['Close'].pct_change()
    
    return returns.corr()


def calcular_drawdown(equity_curve: pd.Series) -> pd.DataFrame:
    """Calcula drawdown completo de una curva de equity"""
    rolling_max = equity_curve.expanding().max()
    drawdown = equity_curve / rolling_max - 1
    
    drawdown_periods = []
    in_drawdown = False
    start_date = None
    
    for i in range(len(drawdown)):
        if drawdown.iloc[i] < 0 and not in_drawdown:
            in_drawdown = True
            start_date = drawdown.index[i]
        elif drawdown.iloc[i] == 0 and in_drawdown:
            in_drawdown = False
            drawdown_periods.append({
                'start': start_date,
                'end': drawdown.index[i],
                'max_drawdown': drawdown.loc[start_date:drawdown.index[i]].min()
            })
    
    return pd.DataFrame(drawdown_periods)