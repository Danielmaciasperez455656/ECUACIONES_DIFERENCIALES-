import sympy as sp

class EcuacionDiferencialSolver:
    """
    Clase encargada de la lógica matemática utilizando SymPy.
    Resuelve Ecuaciones Diferenciales Exactas y Reducibles a Exactas (Factor Integrante).
    """

    def __init__(self):
        # Definimos los símbolos matemáticos base
        self.x, self.y, self.C = sp.symbols('x y C')
        
    def resolver_exacta(self, M_str, N_str):
        """
        Resuelve M(x,y)dx + N(x,y)dy = 0.
        Retorna: (Solución LaTeX, Lista de diccionarios de pasos)
        """
        pasos = []
        
        # Función auxiliar para guardar cada paso
        def agregar_paso(titulo, explicacion, formula_latex):
            pasos.append({
                "titulo": titulo,
                "texto": explicacion,
                "formula": formula_latex
            })

        try:
            # =========================================================
            # 0. LIMPIEZA Y NORMALIZACIÓN DE ENTRADAS
            # =========================================================
            
            # Quitar prefijos innecesarios
            M_str = M_str.replace("math.", "").replace("Math.", "")
            N_str = N_str.replace("math.", "").replace("Math.", "")

            # 👉 MEJORA: permitir usar ^ como potencia
            M_str = M_str.replace("^", "**")
            N_str = N_str.replace("^", "**")

            # Convertir texto a expresiones SymPy
            M = sp.sympify(M_str)
            N = sp.sympify(N_str)
            
            # =========================================================
            # 1. VERIFICAR EXACTITUD
            # =========================================================
            dM_dy = sp.diff(M, self.y)
            dN_dx = sp.diff(N, self.x)
            
            check_latex = (
                f"\\frac{{\\partial M}}{{\\partial y}} = {sp.latex(dM_dy)} "
                f"\\quad , \\quad "
                f"\\frac{{\\partial N}}{{\\partial x}} = {sp.latex(dN_dx)}"
            )
            
            agregar_paso(
                "1. Verificar Exactitud",
                "Calculamos las derivadas parciales cruzadas para verificar si la ecuación es exacta.",
                check_latex
            )

            exacta = dM_dy.equals(dN_dx)

            # =========================================================
            # 1.1 FACTOR INTEGRANTE (SI NO ES EXACTA)
            # =========================================================
            if not exacta:
                agregar_paso(
                    "No es Exacta",
                    "Las derivadas parciales no coinciden. Buscamos un factor integrante.",
                    r"\frac{\partial M}{\partial y} \neq \frac{\partial N}{\partial x}"
                )
                
                mu = None
                explicacion_mu = ""

                # Factor integrante dependiente de x
                factor_x = sp.simplify((dM_dy - dN_dx) / N)
                if self.y not in factor_x.free_symbols:
                    mu = sp.exp(sp.integrate(factor_x, self.x))
                    explicacion_mu = (
                        r"El factor integrante depende solo de $x$: "
                        r"$\mu(x) = e^{\int (" + sp.latex(factor_x) + r") dx}$"
                    )

                # Factor integrante dependiente de y
                if mu is None:
                    factor_y = sp.simplify((dN_dx - dM_dy) / M)
                    if self.x not in factor_y.free_symbols:
                        mu = sp.exp(sp.integrate(factor_y, self.y))
                        explicacion_mu = (
                            r"El factor integrante depende solo de $y$: "
                            r"$\mu(y) = e^{\int (" + sp.latex(factor_y) + r") dy}$"
                        )

                if mu is None:
                    agregar_paso(
                        "Error",
                        "No se encontró un factor integrante sencillo.",
                        r"\text{Método no aplicable}"
                    )
                    return None, pasos

                mu = sp.simplify(mu)
                agregar_paso(
                    "1.1 Factor Integrante",
                    explicacion_mu,
                    f"\\mu = {sp.latex(mu)}"
                )

                M = sp.simplify(M * mu)
                N = sp.simplify(N * mu)

                agregar_paso(
                    "1.2 Nueva Ecuación Exacta",
                    "Multiplicamos M y N por el factor integrante.",
                    f"\\tilde{{M}} = {sp.latex(M)}, \\quad \\tilde{{N}} = {sp.latex(N)}"
                )

            # =========================================================
            # 2. INTEGRAR M RESPECTO A x
            # =========================================================
            F_xy = sp.integrate(M, self.x)
            agregar_paso(
                "2. Integrar M respecto a x",
                "Integramos M con respecto a x y añadimos g(y).",
                f"F(x,y) = {sp.latex(F_xy)} + g(y)"
            )

            # =========================================================
            # 3. ENCONTRAR g'(y)
            # =========================================================
            dF_dy = sp.diff(F_xy, self.y)
            g_prime = sp.simplify(N - dF_dy)

            agregar_paso(
                "3. Encontrar g'(y)",
                "Derivamos F respecto a y y lo igualamos a N.",
                f"g'(y) = {sp.latex(g_prime)}"
            )

            # =========================================================
            # 4. INTEGRAR g'(y)
            # =========================================================
            g_y = sp.integrate(g_prime, self.y)
            agregar_paso(
                "4. Obtener g(y)",
                "Integramos g'(y).",
                f"g(y) = {sp.latex(g_y)}"
            )

            # =========================================================
            # 5. SOLUCIÓN FINAL
            # =========================================================
            solucion = sp.simplify(F_xy + g_y)
            solucion_eq = sp.Eq(solucion, self.C)

            agregar_paso(
                "5. Solución General",
                "La solución implícita de la ecuación diferencial es:",
                sp.latex(solucion_eq)
            )

            return sp.latex(solucion_eq), pasos

        except Exception as e:
            pasos.append({
                "titulo": "Error Matemático",
                "texto": f"No se pudo procesar la expresión: {str(e)}",
                "formula": ""
            })
            return None, pasos
