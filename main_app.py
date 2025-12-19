import streamlit as st
import json
import requests
import os
from ode_solver import EcuacionDiferencialSolver

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ED-Solver UNIPUTUMAYO", page_icon="∫", layout="wide")

# --- 2. GESTIÓN DE API KEY ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "" 

# --- 3. FUNCIONES AUXILIARES (MEJORADAS) ---
def get_ai_data(prompt_text):
    if not API_KEY:
        st.error("⚠️ Error: No se encontró la API KEY en los Secrets.")
        return None
    
    # CAMBIO IMPORTANTE: Usamos 'gemini-1.5-flash' que es más estable
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        resp = requests.post(url, headers=headers, json=data)
        
        if resp.status_code != 200:
            # ESTO NOS DIRÁ EL ERROR EXACTO EN PANTALLA
            st.error(f"Error de Google ({resp.status_code}): {resp.text}")
            return None
            
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.header("🏫 UNIPUTUMAYO")
    st.write("Tecnología en Desarrollo de Software")
    
    # LOGO (Opcional)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    
    st.divider()
    
    st.subheader("Entrada de Datos")
    # CORRECCIÓN: Usamos 'key' para vincular los inputs directamente al estado de la app
    # Esto permite que la IA actualice el texto visible en las cajas.
    m_input = st.text_input("Función M(x, y)", placeholder="Ej: 2*x*y", key="m_input_key")
    n_input = st.text_input("Función N(x, y)", placeholder="Ej: x**2", key="n_input_key")
    
    btn_resolver = st.button("✨ Resolver Ecuación", type="primary")

    st.divider()
    st.subheader("🧠 Generador IA")
    diff = st.selectbox("Dificultad", ["Principiante", "Intermedio"])
    
    if st.button("🎲 Generar Ejercicio"):
        if not API_KEY:
            st.error("❌ Faltan los Secrets.")
        else:
            with st.spinner("Conectando con Gemini 1.5..."):
                prompt = (f"Genera un problema de Ecuación Diferencial Exacta nivel {diff}. "
                          "IMPORTANTE: Responde SOLO con un JSON válido. "
                          "Formato: {'enunciado_M': '...', 'enunciado_N': '...'}. "
                          "Usa sintaxis SymPy (ej: exp(x), sin(y)). NO uses markdown.")
                
                res = get_ai_data(prompt)
                
                if res:
                    try:
                        # Limpieza agresiva del JSON
                        clean_res = res.replace("```json", "").replace("```", "").strip()
                        data_json = json.loads(clean_res)
                        
                        # ACTUALIZACIÓN DIRECTA DE LAS CAJAS DE TEXTO
                        st.session_state.m_input_key = data_json['enunciado_M']
                        st.session_state.n_input_key = data_json['enunciado_N']
                        st.toast("✅ ¡Ejercicio Generado!", icon="🎉")
                        st.rerun() # Recargamos para mostrar los cambios
                    except Exception as e:
                        st.error(f"Error leyendo respuesta de IA: {e}")
                        st.text(f"Respuesta recibida: {res}") # Para depurar

# --- 5. ÁREA PRINCIPAL ---
st.title("📘 Solucionador de Ecuaciones Diferenciales")
st.markdown("Herramienta para resolver Ecuaciones Exactas y por Factor Integrante.")

if btn_resolver:
    if m_input and n_input:
        solver = EcuacionDiferencialSolver()
        try:
            sol, pasos = solver.resolver_exacta(m_input, n_input)
            
            if sol:
                st.success("✅ ¡Ecuación Resuelta!")
                st.latex(sol)
                
                st.markdown("### 📝 Procedimiento")
                for i, paso in enumerate(pasos):
                    with st.expander(f"Paso {i+1}: {paso['titulo']}", expanded=True):
                        st.write(paso['texto'])
                        st.latex(paso['formula'])
                        
                        if st.button("🤖 Explicar paso", key=f"btn_{i}"):
                            with st.spinner("Analizando..."):
                                expl = get_ai_data(f"Explica brevemente este paso matemático: {paso['titulo']} -> {paso['formula']}")
                                if expl: st.info(expl)
            else:
                st.error("⚠️ No se encontró solución o hubo un error matemático.")
                if pasos: st.warning(pasos[0]['texto'])
        except Exception as e:
             st.error(f"Error interno: {e}")
    else:
        st.warning("⚠️ Ingresa M y N.")
else:
    st.info("👈 Usa el menú lateral para comenzar.")