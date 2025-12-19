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

# --- 3. FUNCIONES AUXILIARES (MODO TODOTERRENO) ---
def get_ai_data(prompt_text):
    if not API_KEY:
        st.error("⚠️ Error: No se encontró la API KEY en los Secrets.")
        return None
    
    # Configuración oficial
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
        st.error(f"Error configurando API Key: {e}")
        return None

    # LISTA DE MODELOS A PROBAR (Si falla uno, prueba el siguiente)
    # Esto soluciona tu error 404 porque busca hasta encontrar uno compatible con tu clave.
    modelos_a_probar = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-pro',       # El clásico confiable
        'gemini-1.0-pro'
    ]

    errores = []

    for nombre_modelo in modelos_a_probar:
        try:
            model = genai.GenerativeModel(nombre_modelo)
            response = model.generate_content(prompt_text)
            return response.text  # ¡Éxito! Retornamos la respuesta
        except Exception as e:
            # Si falla, guardamos el error y probamos el siguiente
            errores.append(f"{nombre_modelo}: {str(e)}")
            continue
    
    # Si llegamos aquí, fallaron todos
    st.error(f"❌ No se pudo conectar con ningún modelo de IA. Detalles: {errores}")
    return None

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.header("🏫 UNIPUTUMAYO")
    st.write("Tecnología en Desarrollo de Software")
    
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
    
    st.divider()
    
    st.subheader("Entrada de Datos")
    
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
            with st.spinner("Intentando conectar con IA..."):
                prompt = (f"Genera un problema de Ecuación Diferencial Exacta nivel {diff}. "
                          "IMPORTANTE: Responde SOLO con un JSON válido. "
                          "Formato: {'enunciado_M': '...', 'enunciado_N': '...'}. "
                          "Usa sintaxis SymPy (ej: exp(x), sin(y)). NO uses markdown.")
                
                res = get_ai_data(prompt)
                
                if res:
                    try:
                        clean_res = res.replace("```json", "").replace("```", "").strip()
                        data_json = json.loads(clean_res)
                        
                        st.session_state.m_input_key = data_json['enunciado_M']
                        st.session_state.n_input_key = data_json['enunciado_N']
                        
                        st.toast("✅ ¡Ejercicio Generado!", icon="🎉")
                        st.rerun()
                    except Exception as e:
                        st.error("La IA respondió pero el formato no era válido. Intenta de nuevo.")

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