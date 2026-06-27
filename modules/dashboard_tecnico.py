"""
Dashboard Técnico - Análisis Técnico Avanzado
"""
import os
import sys
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    obtener_datos, calcular_sma, calcular_ema, calcular_rsi, 
    calcular_macd, calcular_bollinger_bands, calcular_estocastico,
    calcular_atr, calcular_obv, calcular_vwap, generar_senal_compra,
    generar_senal_venta
)

# Ocultar navegación automática de Streamlit
st.markdown("""
    <style>
        div[data-testid="stSidebarNav"] {
            display: none !important;
        }
        nav[data-testid="stSidebarNav"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)


def mostrar_dashboard_tecnico():
    """Muestra el dashboard de análisis técnico"""
    
    st.title("📊 Dashboard de Análisis Técnico")
    st.markdown("---")
    
    # Sidebar - Configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        ticker = st.text_input("Símbolo del Activo", value="AAPL", help="Ej: AAPL, MSFT, BTC-USD")
        
        periodo = st.selectbox(
            "Período de Tiempo",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=3
        )
        
        st.markdown("---")
        st.subheader("Indicadores")
        
        mostrar_sma = st.checkbox("Medias Móviles (SMA)", value=True)
        mostrar_ema = st.checkbox("Medias Móviles (EMA)", value=False)
        mostrar_bollinger = st.checkbox("Bandas de Bollinger", value=True)
        mostrar_volumen = st.checkbox("Volumen", value=True)
        
        st.markdown("---")
        
        if st.button("🔄 Actualizar Datos"):
            st.cache_data.clear()
            st.rerun()
    
    # Obtener datos
    try:
        with st.spinner("Cargando datos..."):
            data = obtener_datos(ticker, periodo)
        
        if data.empty:
            st.error(f"No se encontraron datos para {ticker}")
            return
        
        # Métricas principales
        col1, col2, col3, col4, col5 = st.columns(5)
        
        precio_actual = data['Close'].iloc[-1]
        cambio = data['Close'].iloc[-1] - data['Close'].iloc[-2]
        cambio_pct = (cambio / data['Close'].iloc[-2]) * 100
        volumen = data['Volume'].iloc[-1]
        max_52w = data['High'].max()
        min_52w = data['Low'].min()
        
        with col1:
            st.metric(
                label="Precio Actual",
                value=f"${precio_actual:.2f}",
                delta=f"{cambio:.2f} ({cambio_pct:.2f}%)"
            )
        
        with col2:
            st.metric(label="Volumen", value=f"{volumen:,.0f}")
        
        with col3:
            st.metric(label="Máximo Período", value=f"${max_52w:.2f}")
        
        with col4:
            st.metric(label="Mínimo Período", value=f"${min_52w:.2f}")
        
        with col5:
            rsi = calcular_rsi(data['Close']).iloc[-1]
            st.metric(
                label="RSI (14)",
                value=f"{rsi:.2f}",
                delta="Sobrecompra" if rsi > 70 else "Sobreventa" if rsi < 30 else "Neutral"
            )
        
        st.markdown("---")
        
        # Generar señales
        col1, col2 = st.columns(2)
        
        with col1:
            senal_compra = generar_senal_compra(data)
            st.subheader("📈 Señales de Compra")
            if senal_compra['señales']:
                for señal in senal_compra['señales']:
                    st.success(f"✅ {señal}")
                st.metric("Puntuación", f"{senal_compra['puntuacion']}/13")
                st.info(f"**Recomendación**: {senal_compra['recomendacion']}")
            else:
                st.info("No hay señales de compra activas")
        
        with col2:
            senal_venta = generar_senal_venta(data)
            st.subheader("📉 Señales de Venta")
            if senal_venta['señales']:
                for señal in senal_venta['señales']:
                    st.error(f"⚠️ {señal}")
                st.metric("Puntuación", f"{senal_venta['puntuacion']}/13")
                st.info(f"**Recomendación**: {senal_venta['recomendacion']}")
            else:
                st.info("No hay señales de venta activas")
        
        st.markdown("---")
        
        # Gráfico principal
        st.subheader(f"📈 Gráfico de {ticker}")
        
        # Crear subplots
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.5, 0.15, 0.15, 0.2],
            subplot_titles=(f'Precio - {ticker}', 'RSI (14)', 'MACD', 'Volumen')
        )
        
        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Precio'
            ),
            row=1, col=1
        )
        
        # Medias móviles
        if mostrar_sma:
            sma_20 = calcular_sma(data['Close'], 20)
            sma_50 = calcular_sma(data['Close'], 50)
            sma_200 = calcular_sma(data['Close'], 200)
            
            fig.add_trace(go.Scatter(x=data.index, y=sma_20, name='SMA 20', line=dict(color='orange', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=sma_50, name='SMA 50', line=dict(color='blue', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=sma_200, name='SMA 200', line=dict(color='purple', width=1)), row=1, col=1)
        
        if mostrar_ema:
            ema_12 = calcular_ema(data['Close'], 12)
            ema_26 = calcular_ema(data['Close'], 26)
            
            fig.add_trace(go.Scatter(x=data.index, y=ema_12, name='EMA 12', line=dict(color='cyan', width=1, dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=ema_26, name='EMA 26', line=dict(color='magenta', width=1, dash='dash')), row=1, col=1)
        
        # Bandas de Bollinger
        if mostrar_bollinger:
            upper, middle, lower = calcular_bollinger_bands(data['Close'])
            fig.add_trace(go.Scatter(x=data.index, y=upper, name='BB Upper', line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=lower, name='BB Lower', line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
        
        # RSI
        rsi_data = calcular_rsi(data['Close'])
        fig.add_trace(go.Scatter(x=data.index, y=rsi_data, name='RSI', line=dict(color='purple', width=2)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        # MACD
        macd_line, signal_line, histogram = calcular_macd(data['Close'])
        fig.add_trace(go.Scatter(x=data.index, y=macd_line, name='MACD', line=dict(color='blue', width=2)), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=signal_line, name='Signal', line=dict(color='orange', width=2)), row=3, col=1)
        fig.add_trace(go.Bar(x=data.index, y=histogram, name='Histogram', marker_color='gray'), row=3, col=1)
        
        # Volumen
        if mostrar_volumen:
            colors = ['red' if data['Close'].iloc[i] < data['Open'].iloc[i] else 'green' for i in range(len(data))]
            fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volumen', marker_color=colors), row=4, col=1)
        
        # Layout
        fig.update_layout(
            height=1000,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Tabla de datos
        with st.expander("📋 Ver Datos Completos"):
            st.dataframe(data.tail(50))
            
            # Descargar CSV
            csv = data.to_csv()
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"{ticker}_datos.csv",
                mime="text/csv"
            )
        
        # Tabla de indicadores
        with st.expander("📊 Indicadores Técnicos Detallados"):
            indicadores_data = {
                'Indicador': ['SMA 20', 'SMA 50', 'SMA 200', 'EMA 12', 'EMA 26', 'RSI (14)', 'MACD', 'Signal', 'ATR (14)'],
                'Valor': [
                    f"{sma_20.iloc[-1]:.2f}" if mostrar_sma else "N/A",
                    f"{sma_50.iloc[-1]:.2f}" if mostrar_sma else "N/A",
                    f"{sma_200.iloc[-1]:.2f}" if mostrar_sma else "N/A",
                    f"{ema_12.iloc[-1]:.2f}" if mostrar_ema else "N/A",
                    f"{ema_26.iloc[-1]:.2f}" if mostrar_ema else "N/A",
                    f"{rsi_data.iloc[-1]:.2f}",
                    f"{macd_line.iloc[-1]:.4f}",
                    f"{signal_line.iloc[-1]:.4f}",
                    f"{calcular_atr(data['High'], data['Low'], data['Close']).iloc[-1]:.4f}"
                ]
            }
            st.dataframe(pd.DataFrame(indicadores_data), width='stretch')
    
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.info("Verifica que el símbolo sea correcto y esté disponible en Yahoo Finance")