"""
Trading Suite Pro - Aplicación Principal
Navegación manual con st.session_state
"""

import streamlit as st
import sys
import os

# Agregar ruta al proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuración de la página
st.set_page_config(
    page_title="Trading Suite Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session_state para navegación
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = 'inicio'

# Importar módulos
from modules.home import mostrar_home
from modules.dashboard_tecnico import mostrar_dashboard_tecnico
from modules.backtesting import mostrar_backtesting
from modules.analisis_sentimiento import mostrar_analisis_sentimiento
from modules.gestion_riesgo import mostrar_gestion_riesgo


def main():
    """Función principal de la aplicación"""
    
    # Sidebar con navegación
    with st.sidebar:
        st.title("📈 Trading Suite Pro")
        st.markdown("---")
        
        # Botones de navegación
        st.subheader("Navegación")
        
        if st.button("🏠 Inicio", use_container_width=True, 
                     type="primary" if st.session_state.pagina_actual == 'inicio' else "secondary"):
            st.session_state.pagina_actual = 'inicio'
            st.rerun()
        
        if st.button("📊 Dashboard Técnico", use_container_width=True,
                     type="primary" if st.session_state.pagina_actual == 'dashboard' else "secondary"):
            st.session_state.pagina_actual = 'dashboard'
            st.rerun()
        
        if st.button("⚡ Backtesting", use_container_width=True,
                     type="primary" if st.session_state.pagina_actual == 'backtesting' else "secondary"):
            st.session_state.pagina_actual = 'backtesting'
            st.rerun()
        
        if st.button("🧠 Análisis de Sentimiento", use_container_width=True,
                     type="primary" if st.session_state.pagina_actual == 'sentimiento' else "secondary"):
            st.session_state.pagina_actual = 'sentimiento'
            st.rerun()
        
        if st.button("🛡️ Gestión de Riesgo", use_container_width=True,
                     type="primary" if st.session_state.pagina_actual == 'riesgo' else "secondary"):
            st.session_state.pagina_actual = 'riesgo'
            st.rerun()
        
        st.markdown("---")
        
        # Información de la app
        st.markdown("### ℹ️ Acerca de")
        st.markdown("""
        **Trading Suite Pro** v1.0
        
        Plataforma integral de análisis de mercados.
        
        **Desarrollado con**:
        - Streamlit
        - yfinance
        - Plotly
        - Pandas/NumPy
        - NLTK/TextBlob
        """)
    
    # Renderizar página según selección
    if st.session_state.pagina_actual == 'inicio':
        mostrar_home()
    elif st.session_state.pagina_actual == 'dashboard':
        mostrar_dashboard_tecnico()
    elif st.session_state.pagina_actual == 'backtesting':
        mostrar_backtesting()
    elif st.session_state.pagina_actual == 'sentimiento':
        mostrar_analisis_sentimiento()
    elif st.session_state.pagina_actual == 'riesgo':
        mostrar_gestion_riesgo()


if __name__ == "__main__":
    main()