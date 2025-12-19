import streamlit as st
import json
import os
import google.generativeai as genai
import sympy as sp
from ode_solver import EcuacionDiferencialSolver

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="ED-Solver UNIPUTUMAYO", 
    page_icon="🏫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS PARA ESTÉTICA (LOGO Y UI) ---
st.markdown("""
    <style>
    /* Estilo para el contenedor del logo */
    .logo-container {
        display: flex;
        justify-content: center;
        padding: 10px;
        margin-bottom: 20px;
    }
    
    /* Estilo para la imagen del logo */
    .logo-img {
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
        border: 2px solid #f0f2f6;
    }
    
    .logo-img:hover {
        transform: scale(1.05);
    }

    /* Ajuste de fuentes y títulos */
    .sidebar-title {
        text-align: center;
        font-weight: 700;
        color: #1E3A8A;
        margin-top: -10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. GESTIÓN DE API KEY ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = ""

# --- 4. FUNCIÓN DE IA ---
def get_ai_data(prompt_text):
    if not API_KEY:
        return None
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_text)
        return response.text
    except Exception:
        return None

# --- 5. BARRA LATERAL (CON LOGO ESTÉTICO) ---
with st.sidebar:
    # Renderizado del Logo Estético
    if os.path.exists("logo.jpeg"):
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image("logo.jpeg", width=150)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Placeholder estético si no hay imagen
        st.markdown("""
            <div style='text-align: center; padding: 20px; background: #f0f2f6; border-radius: 15px; margin-bottom: 20px;'>
                <h2 style='margin:0;'>🏫</h2>
                <small>Logo no encontrado</small>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<h2 class="sidebar-title">UNIPUTUMAYO</h2>', unsafe_allow_html=True)
    st.write("Tecnología en Desarrollo de Software")
    
    st.divider()
    
    st.subheader("📝 Entrada de Datos")
    m_input = st.text_input("Función M(x, y)", placeholder="Ej: 2*x*y", key="m_input_key")
    n_input = st.text_input("Función N(x, y)", placeholder="Ej: x**2", key="n_input_key")
    
    btn_resolver = st.button("✨ Resolver Ecuación", type="primary", use_container_width=True)

    st.divider()
    st.subheader("🧠 Asistente IA")
    
    if st.button("🎲 Generar Ejercicio Aleatorio", use_container_width=True):
        if not API_KEY:
            st.error("Configura la API KEY en Secrets.")
        else:
            with st.spinner("La IA está creando un reto..."):
                prompt = "Genera un JSON con una ED exacta: {'M': '...', 'N': '...'}. Usa sintaxis de SymPy."
                res = get_ai_data(prompt)
                if res:
                    try:
                        clean_res = res.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_res)
                        st.session_state.m_input_key = data['M']
                        st.session_state.n_input_key = data['N']
                        st.rerun()
                    except:
                        st.warning("Reintenta, formato no válido.")

# --- 6. CUERPO PRINCIPAL ---
st.title("📘 Solucionador de Ecuaciones Exactas")
st.info("Ingresa las funciones M y N en el panel izquierdo para obtener el paso a paso.")

if btn_resolver:
    if m_input and n_input:
        solver = EcuacionDiferencialSolver()
        sol, pasos = solver.resolver_exacta(m_input, n_input)
        
        if sol:
            st.success("🎉 ¡Solución encontrada con éxito!")
            st.latex(f"\\Phi(x, y) = {sp.latex(sol)} = C")
            
            st.subheader("📋 Procedimiento Detallado")
            for i, p in enumerate(pasos):
                with st.expander(f"Paso {i+1}: {p['titulo']}", expanded=True):
                    st.write(p['texto'])
                    if p['formula']:
                        st.latex(p['formula'])
                    
                    # Botón de explicación por IA
                    if st.button(f"💡 Explicación IA del Paso {i+1}", key=f"ai_btn_{i}"):
                        with st.spinner("Analizando con Gemini..."):
                            expl = get_ai_data(f"Explica como un profesor este paso: {p['titulo']} - {p['texto']} {p['formula']}")
                            if expl:
                                st.info(expl)
        else:
            st.error(pasos[0]['texto'])
    else:
        st.warning("Por favor, completa ambos campos (M y N).")