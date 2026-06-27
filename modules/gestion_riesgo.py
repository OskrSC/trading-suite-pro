"""
Gestión de Riesgo - Análisis Cuantitativo de Riesgo
"""
import os
import sys
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots  # ✅ IMPORTANTE
import plotly.express as px
import pandas as pd
import numpy as np


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    obtener_datos, calcular_var_historico, calcular_cvar,
    simulacion_monte_carlo, calcular_matriz_correlacion, calcular_drawdown
)

# Ocultar navegación automática
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


def mostrar_gestion_riesgo():
    """Muestra el módulo de gestión de riesgo"""
    
    st.title("🛡️ Gestión de Riesgo")
    st.markdown("---")
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 VaR y CVaR",
        "🎲 Monte Carlo",
        "📉 Análisis de Drawdown",
        "💼 Portafolio Multi-Activo"
    ])
    
    # ==========================================
    # TAB 1: VaR y CVaR
    # ==========================================
    with tab1:
        st.subheader("📊 Value at Risk (VaR) y Conditional VaR")
        
        with st.sidebar:
            st.header("⚙️ Configuración VaR")
            
            ticker_var = st.text_input("Símbolo del Activo", value="AAPL", key="ticker_var")
            
            periodo_var = st.selectbox(
                "Período Histórico",
                options=["6mo", "1y", "2y", "5y"],
                index=1,
                key="periodo_var"
            )
            
            confianza = st.slider(
                "Nivel de Confianza (%)",
                min_value=90,
                max_value=99,
                value=95,
                step=1
            ) / 100
            
            capital = st.number_input(
                "Capital en Riesgo ($)",
                min_value=1000,
                max_value=10000000,
                value=100000,
                step=1000
            )
        
        try:
            with st.spinner("Calculando VaR y CVaR..."):
                data_var = obtener_datos(ticker_var, periodo_var)
                returns = data_var['Close'].pct_change().dropna()
                
                # Calcular métricas
                var = calcular_var_historico(returns, confianza)
                cvar = calcular_cvar(returns, confianza)
                
                var_dolar = capital * abs(var)
                cvar_dolar = capital * abs(cvar)
                
                # Métricas principales
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        f"VaR ({confianza*100:.0f}%)",
                        f"{var*100:.2f}%",
                        delta=f"-${var_dolar:,.2f}",
                        delta_color="inverse"
                    )
                
                with col2:
                    st.metric(
                        "CVaR (Expected Shortfall)",
                        f"{cvar*100:.2f}%",
                        delta=f"-${cvar_dolar:,.2f}",
                        delta_color="inverse"
                    )
                
                with col3:
                    volatilidad = returns.std() * np.sqrt(252) * 100
                    st.metric("Volatilidad Anualizada", f"{volatilidad:.2f}%")
                
                with col4:
                    retorno_anual = returns.mean() * 252 * 100
                    st.metric("Retorno Anualizado", f"{retorno_anual:.2f}%")
                
                st.markdown("---")
                
                # Explicación
                st.info(f"""
                📊 **Interpretación**:
                
                - **VaR ({confianza*100:.0f}%)**: Con {confianza*100:.0f}% de confianza, la pérdida máxima esperada en un día es **{var*100:.2f}%** (${var_dolar:,.2f})
                - **CVaR**: Cuando se excede el VaR, la pérdida promedio esperada es **{cvar*100:.2f}%** (${cvar_dolar:,.2f})
                - **Diferencia**: El CVaR es más conservador que el VaR porque considera la cola de la distribución
                """)
                
                # Distribución de retornos
                st.subheader("📈 Distribución de Retornos")
                
                fig_dist = go.Figure()
                
                fig_dist.add_trace(go.Histogram(
                    x=returns * 100,
                    nbinsx=50,
                    name='Retornos Diarios',
                    marker_color='#3b82f6',
                    opacity=0.7
                ))
                
                # Líneas VaR y CVaR
                fig_dist.add_vline(
                    x=var * 100,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"VaR: {var*100:.2f}%",
                    annotation_position="top"
                )
                
                fig_dist.add_vline(
                    x=cvar * 100,
                    line_dash="dash",
                    line_color="orange",
                    annotation_text=f"CVaR: {cvar*100:.2f}%",
                    annotation_position="top"
                )
                
                fig_dist.update_layout(
                    height=400,
                    template='plotly_dark',
                    xaxis_title='Retorno Diario (%)',
                    yaxis_title='Frecuencia',
                    showlegend=False
                )
                
                st.plotly_chart(fig_dist, width='stretch')
                
                # Retornos extremos
                st.subheader("⚠️ Eventos Extremos")
                
                percentiles = [0.01, 0.05, 0.10, 0.25, 0.50]
                eventos = pd.DataFrame({
                    'Percentil': [f"{p*100:.0f}%" for p in percentiles],
                    'Retorno (%)': [f"{returns.quantile(p)*100:.2f}%" for p in percentiles],
                    'Pérdida en Capital ($)': [f"${capital * abs(returns.quantile(p)):,.2f}" for p in percentiles]
                })
                
                st.dataframe(eventos, width='stretch', hide_index=True)
        
        except Exception as e:
            st.error(f"Error al calcular VaR: {str(e)}")
    
    # ==========================================
    # TAB 2: Monte Carlo
    # ==========================================
    with tab2:
        st.subheader("🎲 Simulación de Monte Carlo")
        
        with st.sidebar:
            st.header("⚙️ Configuración Monte Carlo")
            
            ticker_mc = st.text_input("Símbolo del Activo", value="AAPL", key="ticker_mc")
            
            periodo_mc = st.selectbox(
                "Período Histórico",
                options=["1y", "2y", "5y"],
                index=0,
                key="periodo_mc"
            )
            
            dias_proyeccion = st.slider(
                "Días a Proyectar",
                min_value=30,
                max_value=504,
                value=252,
                step=30
            )
            
            num_simulaciones = st.slider(
                "Número de Simulaciones",
                min_value=100,
                max_value=5000,
                value=1000,
                step=100
            )
            
            capital_mc = st.number_input(
                "Capital Inicial ($)",
                min_value=1000,
                max_value=10000000,
                value=100000,
                step=1000
            )
        
        try:
            with st.spinner("Ejecutando simulación de Monte Carlo..."):
                data_mc = obtener_datos(ticker_mc, periodo_mc)
                returns_mc = data_mc['Close'].pct_change().dropna()
                
                # Ejecutar simulación
                resultados_mc = simulacion_monte_carlo(
                    returns_mc,
                    dias=dias_proyeccion,
                    simulaciones=num_simulaciones,
                    capital_inicial=capital_mc
                )
                
                # Estadísticas finales
                valores_finales = resultados_mc.iloc[-1]
                
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Mediana", f"${valores_finales.median():,.2f}")
                with col2:
                    st.metric("Media", f"${valores_finales.mean():,.2f}")
                with col3:
                    st.metric("Percentil 5%", f"${valores_finales.quantile(0.05):,.2f}")
                with col4:
                    st.metric("Percentil 95%", f"${valores_finales.quantile(0.95):,.2f}")
                with col5:
                    prob_perdida = (valores_finales < capital_mc).mean() * 100
                    st.metric("Prob. Pérdida", f"{prob_perdida:.1f}%")
                
                st.markdown("---")
                
                # Gráfico de simulaciones
                st.subheader(f"📈 {num_simulaciones} Simulaciones de {dias_proyeccion} Días")
                
                fig_mc = go.Figure()
                
                # Mostrar subset de simulaciones (para no saturar)
                num_mostrar = min(100, num_simulaciones)
                simulaciones_mostrar = resultados_mc.sample(n=num_mostrar, axis=1, random_state=42)
                
                for col in simulaciones_mostrar.columns:
                    fig_mc.add_trace(go.Scatter(
                        y=simulaciones_mostrar[col],
                        mode='lines',
                        line=dict(color='#3b82f6', width=0.5),
                        opacity=0.3,
                        showlegend=False
                    ))
                
                # Percentiles
                percentil_5 = resultados_mc.quantile(0.05, axis=1)
                percentil_50 = resultados_mc.quantile(0.50, axis=1)
                percentil_95 = resultados_mc.quantile(0.95, axis=1)
                
                fig_mc.add_trace(go.Scatter(
                    y=percentil_5,
                    mode='lines',
                    line=dict(color='red', width=2, dash='dash'),
                    name='Percentil 5%'
                ))
                
                fig_mc.add_trace(go.Scatter(
                    y=percentil_50,
                    mode='lines',
                    line=dict(color='green', width=3),
                    name='Mediana (50%)'
                ))
                
                fig_mc.add_trace(go.Scatter(
                    y=percentil_95,
                    mode='lines',
                    line=dict(color='blue', width=2, dash='dash'),
                    name='Percentil 95%'
                ))
                
                fig_mc.update_layout(
                    height=500,
                    template='plotly_dark',
                    xaxis_title='Días',
                    yaxis_title='Capital ($)',
                    showlegend=True
                )
                
                st.plotly_chart(fig_mc, width='stretch')
                
                # Histograma de valores finales
                st.subheader("📊 Distribución de Valores Finales")
                
                fig_hist_mc = go.Figure()
                
                fig_hist_mc.add_trace(go.Histogram(
                    x=valores_finales,
                    nbinsx=50,
                    marker_color='#10b981',
                    opacity=0.7
                ))
                
                fig_hist_mc.add_vline(
                    x=capital_mc,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Capital Inicial",
                    annotation_position="top"
                )
                
                fig_hist_mc.update_layout(
                    height=400,
                    template='plotly_dark',
                    xaxis_title='Capital Final ($)',
                    yaxis_title='Frecuencia',
                    showlegend=False
                )
                
                st.plotly_chart(fig_hist_mc, width='stretch')
        
        except Exception as e:
            st.error(f"Error en simulación Monte Carlo: {str(e)}")
    
    # ==========================================
    # TAB 3: Análisis de Drawdown
    # ==========================================
    with tab3:
        st.subheader("📉 Análisis de Drawdown")
        
        with st.sidebar:
            st.header("⚙️ Configuración Drawdown")
            
            ticker_dd = st.text_input("Símbolo del Activo", value="AAPL", key="ticker_dd")
            
            periodo_dd = st.selectbox(
                "Período",
                options=["1y", "2y", "5y", "max"],
                index=2,
                key="periodo_dd"
            )
        
        try:
            with st.spinner("Calculando drawdown..."):
                data_dd = obtener_datos(ticker_dd, periodo_dd)
                
                # Calcular drawdown
                equity = data_dd['Close']
                rolling_max = equity.expanding().max()
                drawdown = (equity / rolling_max - 1) * 100
                
                # Métricas
                max_dd = drawdown.min()
                max_dd_date = drawdown.idxmin()
                
                # Encontrar recuperación
                recovery_date = None
                for i in range(drawdown.index.get_loc(max_dd_date), len(drawdown)):
                    if drawdown.iloc[i] == 0:
                        recovery_date = drawdown.index[i]
                        break
                
                dias_recuperacion = (recovery_date - max_dd_date).days if recovery_date else None
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Max Drawdown", f"{max_dd:.2f}%")
                with col2:
                    st.metric("Fecha Inicio", max_dd_date.strftime('%Y-%m-%d'))
                with col3:
                    if recovery_date:
                        st.metric("Fecha Recuperación", recovery_date.strftime('%Y-%m-%d'))
                    else:
                        st.metric("Fecha Recuperación", "No recuperado")
                with col4:
                    if dias_recuperacion:
                        st.metric("Días en Drawdown", dias_recuperacion)
                    else:
                        st.metric("Días en Drawdown", "En curso")
                
                st.markdown("---")
                
                # Gráfico de drawdown
                fig_dd = go.Figure()
                
                fig_dd.add_trace(go.Scatter(
                    x=drawdown.index,
                    y=drawdown,
                    fill='tozeroy',
                    line=dict(color='#ef4444', width=1),
                    name='Drawdown'
                ))
                
                fig_dd.add_trace(go.Scatter(
                    x=[max_dd_date],
                    y=[max_dd],
                    mode='markers+text',
                    marker=dict(size=12, color='red'),
                    text=[f"Max: {max_dd:.2f}%"],
                    textposition="bottom center",
                    name='Máximo Drawdown'
                ))
                
                fig_dd.update_layout(
                    height=400,
                    template='plotly_dark',
                    yaxis_title='Drawdown (%)',
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_dd, width='stretch')
                
                # Precio vs Drawdown
                st.subheader("📊 Precio vs Drawdown")
                
                fig_precio_dd = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig_precio_dd.add_trace(
                    go.Scatter(
                        x=data_dd.index,
                        y=data_dd['Close'],
                        name='Precio',
                        line=dict(color='#10b981', width=2)
                    ),
                    secondary_y=False,
                )
                
                fig_precio_dd.add_trace(
                    go.Scatter(
                        x=drawdown.index,
                        y=drawdown,
                        name='Drawdown',
                        line=dict(color='#ef4444', width=1),
                        fill='tozeroy'
                    ),
                    secondary_y=True,
                )
                
                fig_precio_dd.update_layout(
                    height=500,
                    template='plotly_dark',
                    hovermode='x unified'
                )
                
                fig_precio_dd.update_yaxes(title_text="Precio ($)", secondary_y=False)
                fig_precio_dd.update_yaxes(title_text="Drawdown (%)", secondary_y=True)
                
                st.plotly_chart(fig_precio_dd, width='stretch')
                
                # Top 5 peores drawdowns
                st.subheader("⚠️ Top 5 Peores Drawdowns")
                
                drawdown_periods = calcular_drawdown(equity)
                
                if not drawdown_periods.empty:
                    drawdown_periods = drawdown_periods.sort_values('max_drawdown').head(5)
                    drawdown_periods['max_drawdown'] = drawdown_periods['max_drawdown'] * 100
                    drawdown_periods['duracion'] = (drawdown_periods['end'] - drawdown_periods['start']).dt.days
                    
                    st.dataframe(
                        drawdown_periods.rename(columns={
                            'start': 'Inicio',
                            'end': 'Fin',
                            'max_drawdown': 'Max Drawdown (%)',
                            'duracion': 'Duración (días)'
                        }),
                        width='stretch',
                        hide_index=True
                    )
        
        except Exception as e:
            st.error(f"Error al calcular drawdown: {str(e)}")
    
    # ==========================================
    # TAB 4: Portafolio Multi-Activo
    # ==========================================
    with tab4:
        st.subheader("💼 Análisis de Portafolio Multi-Activo")
        
        with st.sidebar:
            st.header("⚙️ Configuración Portafolio")
            
            st.markdown("**Activos del Portafolio**")
            
            activos_default = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            activos_input = st.text_area(
                "Símbolos (uno por línea)",
                value="\n".join(activos_default),
                height=150
            )
            
            activos = [a.strip().upper() for a in activos_input.split("\n") if a.strip()]
            
            if len(activos) < 2:
                st.warning("Ingresa al menos 2 activos")
            
            periodo_port = st.selectbox(
                "Período",
                options=["6mo", "1y", "2y", "5y"],
                index=1,
                key="periodo_port"
            )
            
            st.markdown("---")
            st.markdown("**Asignación de Pesos**")
            
            pesos = {}
            peso_total = 0
            
            for i, activo in enumerate(activos):
                if i == len(activos) - 1:
                    peso = 100 - peso_total
                    pesos[activo] = st.number_input(
                        f"{activo} (%)",
                        min_value=0,
                        max_value=100,
                        value=peso,
                        disabled=True,
                        key=f"peso_{activo}"
                    )
                else:
                    peso_default = 100 // len(activos)
                    peso = st.number_input(
                        f"{activo} (%)",
                        min_value=0,
                        max_value=100,
                        value=peso_default,
                        key=f"peso_{activo}"
                    )
                    pesos[activo] = peso
                    peso_total += peso
        
        if len(activos) >= 2 and sum(pesos.values()) == 100:
            try:
                with st.spinner("Analizando portafolio..."):
                    # Obtener datos de todos los activos
                    data_portafolio = {}
                    for activo in activos:
                        data_portafolio[activo] = obtener_datos(activo, periodo_port)
                    
                    # Calcular matriz de correlación
                    matriz_corr = calcular_matriz_correlacion(data_portafolio)
                    
                    # Métricas del portafolio
                    returns_portafolio = pd.DataFrame()
                    for activo in activos:
                        returns_portafolio[activo] = data_portafolio[activo]['Close'].pct_change()
                    
                    # Retorno y riesgo del portafolio
                    retorno_esperado = sum(
                        returns_portafolio[activo].mean() * 252 * (pesos[activo] / 100)
                        for activo in activos
                    )
                    
                    volatilidad_portafolio = np.sqrt(
                        np.dot(
                            np.array([pesos[a] / 100 for a in activos]),
                            np.dot(
                                returns_portafolio.cov() * 252,
                                np.array([pesos[a] / 100 for a in activos])
                            )
                        )
                    )
                    
                    # ✅ CORREGIDO: Nombre de variable sin espacios
                    volatilidades_individuales = [
                        returns_portafolio[activo].std() * np.sqrt(252) * (pesos[activo] / 100)
                        for activo in activos
                    ]
                    volatilidad_ponderada = sum(volatilidades_individuales)
                    beneficio_diversificacion = (1 - volatilidad_portafolio / volatilidad_ponderada) * 100
                    
                    sharpe_portafolio = retorno_esperado / volatilidad_portafolio if volatilidad_portafolio > 0 else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Retorno Anualizado", f"{retorno_esperado*100:.2f}%")
                    with col2:
                        st.metric("Volatilidad", f"{volatilidad_portafolio*100:.2f}%")
                    with col3:
                        st.metric("Sharpe Ratio", f"{sharpe_portafolio:.2f}")
                    with col4:
                        st.metric("Beneficio Diversificación", f"{beneficio_diversificacion:.2f}%")
                    
                    st.markdown("---")
                    
                    # Matriz de correlación
                    st.subheader("🔗 Matriz de Correlación")
                    
                    fig_corr = px.imshow(
                        matriz_corr,
                        text_auto=".2f",
                        color_continuous_scale='RdBu_r',
                        zmin=-1,
                        zmax=1,
                        title='Correlación entre Activos'
                    )
                    
                    fig_corr.update_layout(
                        height=500,
                        template='plotly_dark'
                    )
                    
                    st.plotly_chart(fig_corr, width='stretch')
                    
                    # Evolución del portafolio
                    st.subheader("📈 Evolución del Portafolio")
                    
                    # Calcular valor del portafolio
                    portafolio_value = pd.DataFrame()
                    for activo in activos:
                        portafolio_value[activo] = data_portafolio[activo]['Close'] / data_portafolio[activo]['Close'].iloc[0] * (pesos[activo] / 100)
                    
                    portafolio_total = portafolio_value.sum(axis=1) * 10000
                    
                    fig_port = go.Figure()
                    
                    for activo in activos:
                        fig_port.add_trace(go.Scatter(
                            x=data_portafolio[activo].index,
                            y=data_portafolio[activo]['Close'] / data_portafolio[activo]['Close'].iloc[0] * 100,
                            name=f"{activo} ({pesos[activo]}%)",
                            line=dict(width=1)
                        ))
                    
                    fig_port.add_trace(go.Scatter(
                        x=data_portafolio[activos[0]].index,
                        y=portafolio_total / 100,
                        name='Portafolio',
                        line=dict(color='white', width=3),
                    ))
                    
                    fig_port.update_layout(
                        height=500,
                        template='plotly_dark',
                        yaxis_title='Valor Normalizado (Base 100)',
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_port, width='stretch')
                    
                    # Distribución del portafolio
                    st.subheader("🥧 Distribución del Portafolio")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        df_pesos = pd.DataFrame({
                            'Activo': activos,
                            'Peso (%)': [pesos[a] for a in activos]
                        })
                        
                        fig_pie = px.pie(
                            df_pesos,
                            values='Peso (%)',
                            names='Activo',
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        
                        fig_pie.update_layout(
                            height=400,
                            template='plotly_dark'
                        )
                        
                        st.plotly_chart(fig_pie, width='stretch')
                    
                    with col2:
                        # Riesgo vs Retorno
                        fig_riesgo_retorno = go.Figure()
                        
                        for activo in activos:
                            retorno_activo = returns_portafolio[activo].mean() * 252 * 100
                            riesgo_activo = returns_portafolio[activo].std() * np.sqrt(252) * 100
                            
                            fig_riesgo_retorno.add_trace(go.Scatter(
                                x=[riesgo_activo],
                                y=[retorno_activo],
                                mode='markers+text',
                                marker=dict(size=15, color='#3b82f6'),
                                text=[activo],
                                textposition="top center",
                                name=activo
                            ))
                        
                        # Portafolio
                        fig_riesgo_retorno.add_trace(go.Scatter(
                            x=[volatilidad_portafolio * 100],
                            y=[retorno_esperado * 100],
                            mode='markers+text',
                            marker=dict(size=20, color='#10b981', symbol='star'),
                            text=['Portafolio'],
                            textposition="top center",
                            name='Portafolio'
                        ))
                        
                        fig_riesgo_retorno.update_layout(
                            height=400,
                            template='plotly_dark',
                            xaxis_title='Riesgo (Volatilidad %)',
                            yaxis_title='Retorno Anualizado (%)',
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_riesgo_retorno, width='stretch')
            
            except Exception as e:
                st.error(f"Error al analizar portafolio: {str(e)}")
        elif sum(pesos.values()) != 100:
            st.warning(f"⚠️ La suma de pesos debe ser 100%. Actual: {sum(pesos.values())}%")