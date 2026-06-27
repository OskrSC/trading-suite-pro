"""
Análisis de Sentimiento - NLP para Mercados
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Agregar ruta al proyecto raíz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import (
    obtener_datos, analizar_sentimiento_texto, generar_datos_sentimiento_demo
)


def mostrar_analisis_sentimiento():
    """Muestra el módulo de análisis de sentimiento"""
    
    st.title(" Análisis de Sentimiento")
    st.markdown("---")
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs(["📰 Análisis de Noticias", "️ Análisis de Texto Libre", " Correlación Sentimiento-Precio"])
    
    # ==========================================
    # TAB 1: Análisis de Noticias
    # ==========================================
    with tab1:
        st.subheader("📰 Análisis de Sentimiento de Noticias")
        
        with st.sidebar:
            st.header("⚙️ Configuración Noticias")
            
            ticker_noticias = st.text_input("Símbolo del Activo", value="AAPL", key="ticker_noticias")
            
            dias_analisis = st.slider(
                "Días de Análisis",
                min_value=7,
                max_value=90,
                value=30,
                step=7
            )
        
        # Generar datos demo
        with st.spinner("Analizando sentimiento de noticias..."):
            df_noticias = generar_datos_sentimiento_demo(ticker_noticias, dias_analisis)
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        total_noticias = len(df_noticias)
        positivas = len(df_noticias[df_noticias['sentimiento'] == 'POSITIVO'])
        negativas = len(df_noticias[df_noticias['sentimiento'] == 'NEGATIVO'])
        neutrales = len(df_noticias[df_noticias['sentimiento'] == 'NEUTRAL'])
        
        with col1:
            st.metric("Total Noticias", total_noticias)
        with col2:
            st.metric("Positivas", positivas, delta=f"{positivas/total_noticias*100:.1f}%" if total_noticias > 0 else "0%")
        with col3:
            st.metric("Negativas", negativas, delta=f"-{negativas/total_noticias*100:.1f}%" if total_noticias > 0 else "0%", delta_color="inverse")
        with col4:
            st.metric("Neutrales", neutrales)
        
        # Sentimiento promedio
        sentimiento_promedio = df_noticias['compound'].mean()
        if sentimiento_promedio > 0.05:
            tendencia = " Positiva"
        elif sentimiento_promedio < -0.05:
            tendencia = " Negativa"
        else:
            tendencia = "➡️ Neutral"
        
        st.info(f"**Tendencia General del Sentimiento**: {tendencia} (Score: {sentimiento_promedio:.3f})")
        
        st.markdown("---")
        
        # Gráfico de evolución del sentimiento
        st.subheader("📈 Evolución del Sentimiento")
        
        fig_sent = go.Figure()
        
        fig_sent.add_trace(go.Scatter(
            x=df_noticias['fecha'],
            y=df_noticias['compound'],
            mode='lines+markers',
            name='Sentimiento Diario',
            line=dict(color='#10b981', width=2),
            marker=dict(size=8)
        ))
        
        df_noticias['sent_ma'] = df_noticias['compound'].rolling(window=7).mean()
        fig_sent.add_trace(go.Scatter(
            x=df_noticias['fecha'],
            y=df_noticias['sent_ma'],
            mode='lines',
            name='Media Móvil 7 días',
            line=dict(color='#3b82f6', width=3, dash='dash')
        ))
        
        fig_sent.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.3)
        
        fig_sent.update_layout(
            height=400,
            template='plotly_dark',
            hovermode='x unified',
            yaxis_title='Score de Sentimiento',
            yaxis=dict(range=[-1.1, 1.1])
        )
        
        st.plotly_chart(fig_sent, width='stretch')
        
        # Distribución de sentimiento
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(" Distribución de Sentimiento")
            
            distribucion = pd.DataFrame({
                'Sentimiento': ['Positivo', 'Negativo', 'Neutral'],
                'Cantidad': [positivas, negativas, neutrales]
            })
            
            fig_pie = px.pie(
                distribucion,
                values='Cantidad',
                names='Sentimiento',
                color='Sentimiento',
                color_discrete_map={
                    'Positivo': '#10b981',
                    'Negativo': '#ef4444',
                    'Neutral': '#6b7280'
                }
            )
            
            fig_pie.update_layout(height=350, template='plotly_dark')
            st.plotly_chart(fig_pie, width='stretch')
        
        with col2:
            st.subheader(" Histograma de Sentimiento")
            
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=df_noticias['compound'],
                nbinsx=20,
                marker_color='#3b82f6',
                opacity=0.75
            ))
            fig_hist.update_layout(
                height=350,
                template='plotly_dark',
                xaxis_title='Score de Sentimiento',
                yaxis_title='Frecuencia'
            )
            st.plotly_chart(fig_hist, width='stretch')
        
        st.markdown("---")
        
        # Tabla de noticias
        st.subheader("📋 Noticias Analizadas")
        
        df_display = df_noticias.copy()
        df_display['fecha'] = df_display['fecha'].dt.strftime('%Y-%m-%d')
        df_display = df_display.rename(columns={
            'fecha': 'Fecha',
            'titular': 'Titular',
            'sentimiento': 'Sentimiento',
            'compound': 'Score'
        })
        
        st.dataframe(
            df_display[['Fecha', 'Titular', 'Sentimiento', 'Score']],
            width='stretch',
            hide_index=True,
            height=400
        )
        
        st.warning("""
        ️ **Nota**: Los datos mostrados son de demostración. 
        Para datos reales, integra con NewsAPI, Alpha Vantage o Finnhub.
        """)
    
    # ==========================================
    # TAB 2: Análisis de Texto Libre
    # ==========================================
    with tab2:
        st.subheader("✍️ Análisis de Texto Personalizado")
        
        st.markdown("""
        Ingresa cualquier texto (noticia, tweet, comunicado, análisis) para analizar su sentimiento.
        Se utilizan dos motores NLP: **TextBlob** y **VADER** (NLTK).
        """)
        
        texto_usuario = st.text_area(
            "Ingresa el texto a analizar:",
            height=200,
            placeholder="Ej: Apple reports record earnings thanks to strong iPhone 15 performance..."
        )
        
        if st.button("🔍 Analizar Sentimiento", type="primary"):
            if not texto_usuario.strip():
                st.warning("Por favor ingresa un texto para analizar")
            else:
                resultado = analizar_sentimiento_texto(texto_usuario)
                
                st.markdown("---")
                
                if resultado['sentimiento'] == 'POSITIVO':
                    emoji = ""
                elif resultado['sentimiento'] == 'NEGATIVO':
                    emoji = "🔴"
                else:
                    emoji = "⚪"
                
                st.markdown(f"### {emoji} Sentimiento Detectado: **{resultado['sentimiento']}**")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("VADER Compound", f"{resultado['compound']:.3f}")
                with col2:
                    st.metric("TextBlob Polarity", f"{resultado['polarity']:.3f}")
                with col3:
                    st.metric("Subjetividad", f"{resultado['subjectivity']:.3f}")
                with col4:
                    confianza = "Alta" if abs(resultado['compound']) > 0.5 else "Media" if abs(resultado['compound']) > 0.2 else "Baja"
                    st.metric("Confianza", confianza)
                
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Desglose VADER")
                    fig_vader = go.Figure(data=[
                        go.Bar(name='Positivo', x=['Sentimiento'], y=[resultado['positive'] * 100], marker_color='#10b981'),
                        go.Bar(name='Neutral', x=['Sentimiento'], y=[resultado['neutral'] * 100], marker_color='#6b7280'),
                        go.Bar(name='Negativo', x=['Sentimiento'], y=[resultado['negative'] * 100], marker_color='#ef4444')
                    ])
                    fig_vader.update_layout(
                        barmode='stack', height=300, template='plotly_dark',
                        yaxis_title='Porcentaje (%)'
                    )
                    st.plotly_chart(fig_vader, width='stretch')
                
                with col2:
                    st.subheader("📈 Métricas TextBlob")
                    st.metric("Polaridad", f"{resultado['polarity']:.3f}")
                    st.metric("Subjetividad", f"{resultado['subjectivity']:.3f}")
                    
                    if resultado['polarity'] > 0.3:
                        st.success("Texto fuertemente positivo")
                    elif resultado['polarity'] > 0:
                        st.info("Texto ligeramente positivo")
                    elif resultado['polarity'] < -0.3:
                        st.error("Texto fuertemente negativo")
                    elif resultado['polarity'] < 0:
                        st.warning("Texto ligeramente negativo")
                    else:
                        st.markdown("Texto neutral")
                
                st.markdown("---")
                st.subheader("💡 Interpretación")
                
                interpretacion = []
                if resultado['compound'] > 0.5:
                    interpretacion.append("✅ **Sentimiento fuertemente positivo**")
                elif resultado['compound'] > 0.05:
                    interpretacion.append("🟢 **Sentimiento moderadamente positivo**")
                elif resultado['compound'] < -0.5:
                    interpretacion.append("❌ **Sentimiento fuertemente negativo**")
                elif resultado['compound'] < -0.05:
                    interpretacion.append("🔴 **Sentimiento moderadamente negativo**")
                else:
                    interpretacion.append("⚪ **Sentimiento neutral**")
                
                if resultado['subjectivity'] > 0.6:
                    interpretacion.append("📝 **Alta subjetividad**")
                elif resultado['subjectivity'] < 0.4:
                    interpretacion.append("📊 **Alta objetividad**")
                else:
                    interpretacion.append("⚖️ **Subjetividad moderada**")
                
                for interp in interpretacion:
                    st.markdown(f"- {interp}")
    
    # ==========================================
    # TAB 3: Correlación Sentimiento-Precio
    # ==========================================
    with tab3:
        st.subheader("📊 Correlación Sentimiento vs Precio")
        
        with st.sidebar:
            st.header("⚙️ Configuración Correlación")
            
            ticker_corr = st.text_input("Símbolo del Activo", value="AAPL", key="ticker_corr")
            
            # ✅ CORREGIDO: st.selectbox en lugar de st.select
            periodo_corr = st.selectbox(
                "Período",
                options=["1mo", "3mo", "6mo", "1y"],
                index=2,
                key="periodo_corr"
            )
        
        try:
            with st.spinner("Cargando datos y calculando correlación..."):
                data_precio = obtener_datos(ticker_corr, periodo_corr)
                
                dias = min(len(data_precio), 124)
                df_sentimiento = generar_datos_sentimiento_demo(ticker_corr, dias)
                
                df_corr = pd.DataFrame({
                    'fecha': data_precio.index[:dias],
                    'precio': data_precio['Close'].values[:dias],
                    'sentimiento': df_sentimiento['compound'].values[:dias]
                })
                
                correlacion = df_corr['precio'].corr(df_corr['sentimiento'])
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Correlación", f"{correlacion:.3f}" if not pd.isna(correlacion) else "N/A")
                
                with col2:
                    if pd.isna(correlacion):
                        st.metric("Interpretación", "Sin Datos")
                    elif correlacion > 0.3:
                        st.metric("Interpretación", "Positiva Fuerte")
                    elif correlacion > 0.1:
                        st.metric("Interpretación", "Positiva Débil")
                    elif correlacion < -0.3:
                        st.metric("Interpretación", "Negativa Fuerte")
                    elif correlacion < -0.1:
                        st.metric("Interpretación", "Negativa Débil")
                    else:
                        st.metric("Interpretación", "Sin Correlación")
                
                with col3:
                    st.metric("Días Analizados", dias)
                
                st.markdown("---")
                
                if not pd.isna(correlacion):
                    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    fig_dual.add_trace(
                        go.Scatter(x=df_corr['fecha'], y=df_corr['precio'], name='Precio', line=dict(color='#10b981', width=2)),
                        secondary_y=False,
                    )
                    fig_dual.add_trace(
                        go.Scatter(x=df_corr['fecha'], y=df_corr['sentimiento'], name='Sentimiento', line=dict(color='#3b82f6', width=2), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)'),
                        secondary_y=True,
                    )
                    
                    fig_dual.update_layout(
                        height=500, template='plotly_dark', hovermode='x unified',
                        title_text=f'Correlación Precio-Sentimiento: {ticker_corr}',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    fig_dual.update_yaxes(title_text="Precio ($)", secondary_y=False)
                    fig_dual.update_yaxes(title_text="Sentimiento", secondary_y=True)
                    
                    st.plotly_chart(fig_dual, width='stretch')
                    
                    st.info(f"""
                    📊 **Análisis de Correlación**: {correlacion:.3f}
                    
                    - **Correlación positiva** (>0): Cuando el sentimiento mejora, el precio tiende a subir
                    - **Correlación negativa** (<0): Cuando el sentimiento mejora, el precio tiende a bajar
                    - **Sin correlación** (≈0): El sentimiento no tiene relación clara con el precio
                    """)
                else:
                    st.warning("No hay datos suficientes para calcular la correlación")
        
        except Exception as e:
            st.error(f"Error al calcular correlación: {str(e)}")