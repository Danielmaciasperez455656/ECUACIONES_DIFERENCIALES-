import sympy as sp

class EcuacionDiferencialSolver:
    """Clase para resolver EDs y mostrar el paso a paso."""

    def __init__(self):
        # Define la variable simbólica principal
        self.x, self.y, self.C = sp.symbols('x y C')
        
    def resolver_exacta(self, M_str, N_str):
        """
        Resuelve una Ecuación Diferencial Exacta de la forma M dx + N dy = 0.
        Retorna una tupla: (solucion_str, pasos_list)
        """
        pasos = []
        
        # Función auxiliar para formatear la salida
        def format_step(explanation, formula_symbolic):
            latex_code = sp.latex(formula_symbolic)
            # El marcador '$$$' se usa para separar texto de fórmula de manera segura
            return f"{explanation}$${latex_code}"

        try:
            # Convertir string a expresión SymPy
            M = sp.sympify(M_str)
            N = sp.sympify(N_str)
            
            # --- Paso 1: Verificar Exactitud ---
            dM_dy = sp.diff(M, self.y)
            dN_dx = sp.diff(N, self.x)
            
            pasos.append(f"**Paso 1: Verificar si es Exacta**")
            pasos.append(format_step("Derivada parcial de M respecto a y:", dM_dy))
            pasos.append(format_step("Derivada parcial de N respecto a x:", dN_dx))
            
            if dM_dy != dN_dx:
                pasos.append(f"¡Atención! La ecuación NO es exacta, ya que {sp.latex(dM_dy)} != {sp.latex(dN_dx)}.")
                return None, pasos

            pasos.append(f"Como las derivadas son iguales, es **Exacta**.")
            
            # --- Paso 2: Integrar M respecto a x ---
            F_xy_M_raw = sp.integrate(M, self.x)
            
            pasos.append(f"**Paso 2: Integrar M(x, y) respecto a x**")
            pasos.append(format_step("F(x, y) = integral(M) + g(y):", F_xy_M_raw))
            
            # --- Paso 3: Derivar F respecto a y ---
            dF_dy_raw = sp.diff(F_xy_M_raw, self.y)
            
            # Despejamos g'(y) = N - dF/dy
            g_prime_y = sp.simplify(N - dF_dy_raw)
            
            pasos.append(f"**Paso 3: Obtener g'(y)**")
            pasos.append(format_step("Restamos la derivada parcial de N:", g_prime_y))
            
            # --- Paso 4: Integrar g'(y) ---
            g_y = sp.integrate(g_prime_y, self.y)
            
            pasos.append(f"**Paso 4: Integrar g'(y) para hallar g(y)**")
            pasos.append(format_step("g(y) es:", g_y))
            
            # --- Paso 5: Solución Final ---
            solucion_simbolica = F_xy_M_raw + g_y
            
            pasos.append(f"**Paso 5: Solución General**")
            solucion_final = sp.Eq(solucion_simbolica, self.C)
            # Retornamos solo el lado izquierdo = C para visualización simple
            pasos.append(format_step("La solución implícita es:", solucion_final))
            
            return sp.latex(solucion_final), pasos
            
        except Exception as e:
            pasos.append(f"**Error:** {str(e)}")
            return None, pasos