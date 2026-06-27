"""
Página de inicio - Trading Suite Pro
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

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


def mostrar_home():
    """Muestra la página de inicio"""
    
    st.title("🏠 Trading Suite Pro")
    st.markdown("---")
    
    # Hero Section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🚀 Plataforma Integral de Análisis de Mercados
        
        **Trading Suite Pro** consolida 16 proyectos especializados en una única aplicación profesional 
        para análisis técnico, backtesting, sentimiento de mercado y gestión de riesgo.
        
        #### 🎯 Características Principales
        
        - **📊 Análisis Técnico Avanzado**: 15+ indicadores con señales automáticas
        - **⚡ Backtesting Cuantitativo**: 4 estrategias con métricas profesionales
        - **🧠 Análisis de Sentimiento**: NLP con TextBlob y VADER
        - **🛡️ Gestión de Riesgo**: VaR, CVaR, Monte Carlo y diversificación
        
        #### 💡 Tecnologías Utilizadas
        
        - **Streamlit**: Framework de UI interactivo
        - **yfinance**: Datos de mercado en tiempo real
        - **Plotly**: Visualizaciones interactivas
        - **Pandas/NumPy**: Procesamiento de datos
        - **NLTK/TextBlob**: Análisis de sentimiento
        - **scikit-learn**: Machine Learning
        """)
    
    with col2:
        # Tarjeta de estadísticas
        st.markdown("### 📈 Estadísticas")
        
        stats_data = {
            'Indicadores Técnicos': '15+',
            'Estrategias Backtest': '4',
            'Métricas de Riesgo': '10+',
            'Fuentes NLP': '2'
        }
        
        for label, value in stats_data.items():
            st.metric(label=label, value=value)
    
    st.markdown("---")
    
    # Módulos disponibles
    st.subheader("🎯 Módulos Disponibles")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 4px solid #10b981;'>
            <h3 style='color: #10b981; margin-top: 0;'>📊 Dashboard Técnico</h3>
            <p>Análisis técnico completo con 15+ indicadores, gráficos de velas japonesas y generación automática de señales.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6;'>
            <h3 style='color: #3b82f6; margin-top: 0;'>⚡ Backtesting</h3>
            <p>Motor de backtesting con 4 estrategias, métricas profesionales (Sharpe, Sortino, Calmar) y comparativas.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 4px solid #f59e0b;'>
            <h3 style='color: #f59e0b; margin-top: 0;'>🧠 Sentimiento</h3>
            <p>Análisis NLP con TextBlob y VADER, correlación sentimiento-precio y análisis de noticias.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style='background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 4px solid #ef4444;'>
            <h3 style='color: #ef4444; margin-top: 0;'>🛡️ Gestión Riesgo</h3>
            <p>VaR, CVaR, Monte Carlo, análisis de drawdown y optimización de portafolios multi-activo.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Instrucciones de uso
    st.subheader("🚀 Cómo Empezar")
    
    st.markdown("""
    1. **Selecciona un módulo** en el menú lateral izquierdo
    2. **Configura los parámetros** según tus necesidades
    3. **Analiza los resultados** con visualizaciones interactivas
    4. **Exporta datos** en formato CSV para análisis adicional
    
    💡 **Tip**: Usa los gráficos interactivos para hacer zoom, pan y explorar los datos en detalle.
    """)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #94a3b8;'>
        <p>Trading Suite Pro v1.0 | Desarrollado con Streamlit | Última actualización: {datetime.now().strftime('%d/%m/%Y')}</p>
    </div>
    """, unsafe_allow_html=True)