"""
Motor de Backtesting - Estrategias Cuantitativas
"""
import os
import sys
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from utils.helpers import (
    obtener_datos, estrategia_cruce_medias, estrategia_rsi,
    estrategia_macd, estrategia_bollinger, ejecutar_backtest
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


def mostrar_backtesting():
    """Muestra el módulo de backtesting"""
    
    st.title("⚡ Motor de Backtesting")
    st.markdown("---")
    
    # Sidebar - Configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        ticker = st.text_input("Símbolo del Activo", value="AAPL")
        
        periodo = st.selectbox(
            "Período de Tiempo",
            options=["1y", "2y", "5y", "max"],
            index=2
        )
        
        capital_inicial = st.number_input(
            "Capital Inicial ($)",
            min_value=1000,
            max_value=1000000,
            value=10000,
            step=1000
        )
        
        comision = st.slider(
            "Comisión por Operación (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.05
        ) / 100
        
        st.markdown("---")
        st.subheader("Estrategias")
        
        usar_cruce_medias = st.checkbox("Cruce de Medias Móviles", value=True)
        usar_rsi = st.checkbox("RSI Mean Reversion", value=True)
        usar_macd = st.checkbox("Cruce MACD", value=True)
        usar_bollinger = st.checkbox("Bollinger Breakout", value=True)
        
        if not any([usar_cruce_medias, usar_rsi, usar_macd, usar_bollinger]):
            st.warning("Selecciona al menos una estrategia")
        
        st.markdown("---")
        
        if st.button("🔄 Ejecutar Backtest"):
            st.rerun()
    
    # Obtener datos
    try:
        with st.spinner("Cargando datos y ejecutando backtests..."):
            data = obtener_datos(ticker, periodo)
        
        if data.empty:
            st.error(f"No se encontraron datos para {ticker}")
            return
        
        st.info(f"📊 Datos cargados: {len(data)} días | {data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}")
        
        # Ejecutar estrategias seleccionadas
        resultados = {}
        
        if usar_cruce_medias:
            df_cruce = estrategia_cruce_medias(data, fast=50, slow=200)
            resultados['Cruce Medias (50/200)'] = ejecutar_backtest(df_cruce, capital_inicial, comision)
        
        if usar_rsi:
            df_rsi = estrategia_rsi(data, periodo=14, sobreventa=30, sobrecompra=70)
            resultados['RSI (30/70)'] = ejecutar_backtest(df_rsi, capital_inicial, comision)
        
        if usar_macd:
            df_macd = estrategia_macd(data, fast=12, slow=26, signal=9)
            resultados['MACD (12/26/9)'] = ejecutar_backtest(df_macd, capital_inicial, comision)
        
        if usar_bollinger:
            df_boll = estrategia_bollinger(data, periodo=20, std_dev=2)
            resultados['Bollinger (20,2)'] = ejecutar_backtest(df_boll, capital_inicial, comision)
        
        if not resultados:
            st.warning("No hay estrategias seleccionadas para ejecutar")
            return
        
        # Tabla comparativa de métricas
        st.subheader("📊 Comparativa de Estrategias")
        
        metricas_comparativa = []
        for nombre, res in resultados.items():
            metricas_comparativa.append({
                'Estrategia': nombre,
                'Retorno Total (%)': f"{res['total_return']:.2f}%",
                'Buy & Hold (%)': f"{res['buy_hold_return']:.2f}%",
                'Sharpe Ratio': f"{res['sharpe_ratio']:.2f}",
                'Sortino Ratio': f"{res['sortino_ratio']:.2f}",
                'Calmar Ratio': f"{res['calmar_ratio']:.2f}",
                'Max Drawdown (%)': f"{res['max_drawdown']:.2f}%",
                'Win Rate (%)': f"{res['win_rate']:.2f}%",
                '# Operaciones': res['num_trades'],
                'Capital Final ($)': f"${res['final_capital']:,.2f}"
            })
        
        df_comparativa = pd.DataFrame(metricas_comparativa)
        st.dataframe(df_comparativa, width='stretch', hide_index=True)
        
        # Identificar mejor estrategia
        mejor_estrategia = max(resultados.items(), key=lambda x: x[1]['total_return'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏆 Mejor Estrategia", mejor_estrategia[0])
        with col2:
            st.metric("📈 Retorno", f"{mejor_estrategia[1]['total_return']:.2f}%")
        with col3:
            st.metric("⚡ Sharpe Ratio", f"{mejor_estrategia[1]['sharpe_ratio']:.2f}")
        
        st.markdown("---")
        
        # Gráfico de Curva de Equity
        st.subheader("📈 Curva de Equity")
        
        fig_equity = go.Figure()
        
        colores = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
        
        for i, (nombre, res) in enumerate(resultados.items()):
            fig_equity.add_trace(go.Scatter(
                x=data.index,
                y=res['equity_curve'],
                name=nombre,
                line=dict(color=colores[i % len(colores)], width=2)
            ))
        
        # Buy & Hold como referencia
        primera_estrategia = list(resultados.values())[0]
        fig_equity.add_trace(go.Scatter(
            x=data.index,
            y=primera_estrategia['buy_hold_curve'],
            name='Buy & Hold (Referencia)',
            line=dict(color='gray', width=2, dash='dash')
        ))
        
        fig_equity.update_layout(
            height=500,
            template='plotly_dark',
            hovermode='x unified',
            yaxis_title='Capital ($)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_equity, width='stretch')
        
        # Análisis detallado por estrategia
        st.subheader("🔍 Análisis Detallado")
        
        tabs = st.tabs(list(resultados.keys()))
        
        for tab, (nombre, res) in zip(tabs, resultados.items()):
            with tab:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Retorno Total", f"{res['total_return']:.2f}%")
                with col2:
                    st.metric("Max Drawdown", f"{res['max_drawdown']:.2f}%")
                with col3:
                    st.metric("Win Rate", f"{res['win_rate']:.2f}%")
                with col4:
                    st.metric("Nº Operaciones", res['num_trades'])
                
                # Métricas de riesgo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sharpe Ratio", f"{res['sharpe_ratio']:.2f}")
                with col2:
                    st.metric("Sortino Ratio", f"{res['sortino_ratio']:.2f}")
                with col3:
                    st.metric("Calmar Ratio", f"{res['calmar_ratio']:.2f}")
        
        st.markdown("---")
        
        # Drawdown Analysis
        st.subheader("📉 Análisis de Drawdown")
        
        fig_dd = go.Figure()
        
        for i, (nombre, res) in enumerate(resultados.items()):
            equity = res['equity_curve']
            rolling_max = equity.expanding().max()
            drawdown = (equity / rolling_max - 1) * 100
            
            fig_dd.add_trace(go.Scatter(
                x=data.index,
                y=drawdown,
                name=nombre,
                fill='tozeroy',
                line=dict(color=colores[i % len(colores)], width=1)
            ))
        
        fig_dd.update_layout(
            height=400,
            template='plotly_dark',
            yaxis_title='Drawdown (%)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_dd, width='stretch')
        
        # Exportar resultados
        with st.expander("📥 Exportar Resultados"):
            csv_comparativa = df_comparativa.to_csv(index=False)
            st.download_button(
                label="Descargar Comparativa CSV",
                data=csv_comparativa,
                file_name=f"{ticker}_backtest_comparativa.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error al ejecutar backtest: {str(e)}")
        st.info("Verifica que el símbolo sea correcto y esté disponible en Yahoo Finance")