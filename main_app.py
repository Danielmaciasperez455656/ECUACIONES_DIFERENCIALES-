import streamlit as st
import json
import os
import google.generativeai as genai
from ode_solver import EcuacionDiferencialSolver

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ED-Solver UNIPUTUMAYO", page_icon="∫", layout="wide")

# --- 2. GESTIÓN DE API KEY ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "" 

# --- 3. FUNCIONES AUXILIARES (LIBRERÍA OFICIAL GOOGLE) ---
def get_ai_data(prompt_text):
    if not API_KEY:
        st.error("⚠️ Error: No se encontró la API KEY en los Secrets.")
        return None
    
    try:
        # Configuración oficial de Google
        genai.configure(api_key=API_KEY)
        
        # Usamos 'gemini-1.5-flash' que es rápido y estable
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generamos la respuesta
        response = model.generate_content(prompt_text)
        return response.text
        
    except Exception as e:
        st.error(f"Error de conexión con IA: {str(e)}")
        return None

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.header("🏫 UNIPUTUMAYO")
    st.write("Tecnología en Desarrollo de Software")
    
    # Logo opcional
    if os.path.exists("logo.jpeg"):
        st.image("logo.jpeg", width=120)

    st.divider()
    
    st.subheader("Entrada de Datos")
    
    # Inputs vinculados a claves de sesión para que la IA pueda escribir en ellos
    m_input = st.text_input("Función M(x, y)", placeholder="Ej: 2*x*y", key="m_input_key")
    n_input = st.text_input("Función N(x, y)", placeholder="Ej: x**2", key="n_input_key")
    
    btn_resolver = st.button("✨ Resolver Ecuación", type="primary")

    st.divider()
    st.subheader("🧠 Generador IA")
    diff = st.selectbox("Dificultad", ["Principiante", "Intermedio"])
    
    if st.button("🎲 Generar Ejercicio"):
        if not API_KEY:
            st.error("❌ Faltan los Secrets (Clave API).")
        else:
            with st.spinner("Generando ejercicio..."):
                prompt = (f"Genera un problema de Ecuación Diferencial Exacta nivel {diff}. "
                          "IMPORTANTE: Responde SOLO con un JSON válido. "
                          "Formato: {'enunciado_M': '...', 'enunciado_N': '...'}. "
                          "Usa sintaxis SymPy (ej: exp(x), sin(y)). NO uses markdown.")
                
                res = get_ai_data(prompt)
                
                if res:
                    try:
                        # Limpiamos el texto por si la IA agrega ```json
                        clean_res = res.replace("```json", "").replace("```", "").strip()
                        data_json = json.loads(clean_res)
                        
                        # Actualizamos las cajas de texto automáticamente
                        st.session_state.m_input_key = data_json['enunciado_M']
                        st.session_state.n_input_key = data_json['enunciado_N']
                        
                        st.toast("✅ ¡Ejercicio Generado!", icon="🎉")
                        st.rerun() # Recargamos la página para ver los cambios
                    except Exception as e:
                        st.error("La IA no devolvió un formato válido. Intenta de nuevo.")

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