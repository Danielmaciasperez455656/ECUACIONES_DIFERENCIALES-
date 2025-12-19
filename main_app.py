import streamlit as st
import json
import requests
import os
from ode_solver import EcuacionDiferencialSolver

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ED-Solver UNIPUTUMAYO", page_icon="∫", layout="wide")

# --- 2. GESTIÓN DE API KEY (SECRETS) ---
# Intentamos leer la clave de los "Secretos" de Streamlit Cloud.
# Si falla (porque estás en tu PC), usa una clave temporal o pide ingresarla.
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # Opción de respaldo para pruebas locales si no has configurado secrets.toml
    API_KEY = "" 

# --- 3. FUNCIONES AUXILIARES ---
def get_ai_data(prompt_text):
    if not API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    try:
        resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt_text}]}]})
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return None

# --- 4. BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.header("🏫 UNIPUTUMAYO")
    st.write("Tecnología en Desarrollo de Software")
    
    st.divider()
    
    st.subheader("Entrada de Datos")
    m_input = st.text_input("Función M(x, y)", value="", placeholder="Ej: 2*x*y")
    n_input = st.text_input("Función N(x, y)", value="", placeholder="Ej: x**2")
    
    btn_resolver = st.button("✨ Resolver Ecuación", type="primary")

    st.divider()
    st.subheader("🧠 Generador IA")
    diff = st.selectbox("Dificultad", ["Principiante", "Intermedio"])
    
    if st.button("🎲 Generar Ejercicio"):
        if not API_KEY:
            st.error("Falta configurar la API KEY en Secrets.")
        else:
            with st.spinner("Generando..."):
                prompt = (f"Genera un problema de Ecuación Diferencial Exacta nivel {diff}. "
                          "Responde SOLO JSON: {'enunciado_M': '...', 'enunciado_N': '...'}. "
                          "Usa sintaxis SymPy (exp(x), sin(y)).")
                res = get_ai_data(prompt)
                if res:
                    try:
                        clean_json = json.loads(res.replace('```json', '').replace('```', ''))
                        st.session_state['m_val'] = clean_json['enunciado_M']
                        st.session_state['n_val'] = clean_json['enunciado_N']
                        st.rerun() # Recarga la página para poner los valores
                    except:
                        st.error("Error leyendo respuesta IA")

# --- LÓGICA DE ACTUALIZACIÓN DE CAMPOS ---
if 'm_val' in st.session_state:
    m_input = st.session_state['m_val']
    n_input = st.session_state['n_val']
    # Limpiamos variables de sesión para permitir edición manual posterior
    del st.session_state['m_val']
    del st.session_state['n_val']

# --- 5. ÁREA PRINCIPAL ---
st.title("📘 Solucionador de Ecuaciones Diferenciales")
st.markdown("Herramienta para resolver Ecuaciones Exactas y por Factor Integrante.")

if btn_resolver:
    if m_input and n_input:
        solver = EcuacionDiferencialSolver()
        # Usamos tu lógica existente
        sol, pasos = solver.resolver_exacta(m_input, n_input)
        
        if sol:
            st.success("✅ ¡Ecuación Resuelta con Éxito!")
            st.markdown(f"### Solución General:  $${sol}$$")
            
            st.markdown("---")
            st.subheader("📝 Procedimiento Paso a Paso")
            
            for i, paso in enumerate(pasos):
                # Usamos 'expander' para que se vea ordenado como acordeón
                with st.expander(f"Paso {i+1}: {paso['titulo']}", expanded=True):
                    st.write(paso['texto'])
                    st.latex(paso['formula'])
                    
                    if st.button("🤖 Explicar este paso", key=f"btn_explain_{i}"):
                        if not API_KEY:
                            st.warning("Configura la API Key para explicaciones.")
                        else:
                            with st.spinner("Analizando..."):
                                p_expl = f"Explica brevemente este paso: {paso['titulo']} con fórmula {paso['formula']} en el contexto de ED."
                                expl = get_ai_data(p_expl)
                                st.info(f"💡 **Explicación IA:** {expl}")
        else:
            st.error("⚠️ No se encontró solución o hubo un error de sintaxis.")
            if pasos:
                st.warning(f"Detalle: {paso[0]['texto']}")
    else:
        st.warning("⚠️ Por favor ingresa las funciones M y N.")

else:
    st.info("👈 Usa el menú lateral para comenzar.")