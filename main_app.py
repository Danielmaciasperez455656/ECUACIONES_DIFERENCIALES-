import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QComboBox, QScrollArea, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QUrl

from ode_solver import EcuacionDiferencialSolver 

class MathViewer(QWebEngineView):
    """
    Visor robusto de LaTeX. Espera a que la página cargue antes de
    ejecutar JavaScript para evitar errores de 'property of null'.
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(80) # Altura por defecto
        self.is_loaded = False
        self.pending_formula = None

        # HTML Base con MathJax
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <script type="text/javascript" 
                src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
            </script>
            <style>
                body { 
                    font-family: sans-serif; 
                    font-size: 16px; 
                    padding: 5px; 
                    margin: 0;
                    overflow: hidden; 
                }
                #math-output { color: #333; }
            </style>
        </head>
        <body>
            <div id="math-output">Cargando motor matemático...</div>
        </body>
        </html>
        """
        
        self.loadFinished.connect(self._on_load_finished)
        self.setHtml(html_content)

    def _on_load_finished(self, ok):
        self.is_loaded = True
        # Limpiar mensaje de carga
        self.page().runJavaScript("document.getElementById('math-output').innerHTML = '';")
        # Si había una fórmula esperando, mostrarla ahora
        if self.pending_formula:
            self.render_latex(self.pending_formula)
            self.pending_formula = None

    def set_formula(self, latex_code):
        if not latex_code: 
            return
        
        if self.is_loaded:
            self.render_latex(latex_code)
        else:
            self.pending_formula = latex_code

    def render_latex(self, latex_code):
        # Escapar comillas simples y backslashes para string de JS
        safe_latex = latex_code.replace('\\', '\\\\').replace("'", "\\'")
        
        js_script = f"""
        var mathDiv = document.getElementById('math-output');
        if (mathDiv) {{
            mathDiv.innerHTML = '$$ {safe_latex} $$';
            MathJax.Hub.Queue(['Typeset', MathJax.Hub, 'math-output']);
        }}
        """
        self.page().runJavaScript(js_script)


class OdeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prototipo ED Solver")
        self.setGeometry(100, 100, 1100, 700)
        
        self.solver = EcuacionDiferencialSolver()
        self.load_ejercicios()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        
        # --- ORDEN IMPORTANTE ---
        # 1. Crear Panel de Salida (Derecha) primero para que existan las referencias
        self.create_output_panel()
        # 2. Crear Panel de Entrada (Izquierda)
        self.create_input_panel()
        
        # Agregar al layout principal (Entrada Izq, Salida Der)
        self.layout.addWidget(self.input_container, 1)
        self.layout.addWidget(self.output_container, 2)

    def load_ejercicios(self):
        try:
            with open('ejercicios.json', 'r', encoding='utf-8') as f:
                self.ejercicios = json.load(f)
        except Exception as e:
            print(f"Error cargando JSON: {e}")
            self.ejercicios = {}

    def create_input_panel(self):
        self.input_container = QWidget()
        layout = QVBoxLayout(self.input_container)
        
        layout.addWidget(QLabel("<h2>Entrada</h2>"))
        
        layout.addWidget(QLabel("M(x, y):"))
        self.m_input = QLineEdit()
        layout.addWidget(self.m_input)
        
        layout.addWidget(QLabel("N(x, y):"))
        self.n_input = QLineEdit()
        layout.addWidget(self.n_input)
        
        btn = QPushButton("Resolver")
        btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        btn.clicked.connect(self.solve_equation)
        layout.addWidget(btn)
        
        layout.addWidget(QLabel("<hr>"))
        layout.addWidget(QLabel("<b>Ejercicios:</b>"))
        
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(self.ejercicios.keys())
        self.cat_combo.currentIndexChanged.connect(self.update_exercise_list)
        layout.addWidget(self.cat_combo)
        
        self.ex_combo = QComboBox()
        self.ex_combo.currentIndexChanged.connect(self.load_selected_exercise)
        layout.addWidget(self.ex_combo)
        
        self.update_exercise_list() # Llenar lista inicial
        layout.addStretch()

    def create_output_panel(self):
        self.output_container = QWidget()
        layout = QVBoxLayout(self.output_container)
        
        layout.addWidget(QLabel("<h2>Solución</h2>"))
        
        # Visor solución final
        self.solution_view = MathViewer()
        layout.addWidget(self.solution_view)
        
        layout.addWidget(QLabel("<b>Paso a Paso:</b>"))
        
        # Scroll para los pasos
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.steps_widget = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_widget)
        self.steps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.steps_widget)
        
        layout.addWidget(self.scroll)

    def update_exercise_list(self):
        cat = self.cat_combo.currentText()
        self.ex_combo.blockSignals(True)
        self.ex_combo.clear()
        if cat in self.ejercicios:
            items = [f"Ej {e['id']}" for e in self.ejercicios[cat]]
            self.ex_combo.addItems(items)
        self.ex_combo.blockSignals(False)

    def load_selected_exercise(self):
        cat = self.cat_combo.currentText()
        idx = self.ex_combo.currentIndex()
        if idx >= 0 and cat in self.ejercicios:
            data = self.ejercicios[cat][idx]
            self.m_input.setText(data['enunciado_M'])
            self.n_input.setText(data['enunciado_N'])
            # Resolver automáticamente al seleccionar
            self.solve_equation()

    def solve_equation(self):
        m_txt = self.m_input.text()
        n_txt = self.n_input.text()
        
        if not m_txt or not n_txt: return

        # Limpiar pasos anteriores
        for i in reversed(range(self.steps_layout.count())): 
            w = self.steps_layout.itemAt(i).widget()
            if w: w.deleteLater()
            
        # Resolver
        sol, pasos = self.solver.resolver_exacta(m_txt, n_txt)
        
        # Mostrar solución final
        if sol:
            self.solution_view.set_formula(sol)
        else:
            self.solution_view.set_formula(r"\text{No se encontró solución}")

        # Mostrar pasos
        for paso in pasos:
            # Separamos explicación de fórmula usando nuestro delimitador $$$
            parts = paso.split('$$')
            texto = parts[0]
            formula = parts[1] if len(parts) > 1 else ""
            
            w = QWidget()
            l = QVBoxLayout(w)
            l.setContentsMargins(0,5,0,5)
            
            lbl = QLabel(texto)
            lbl.setWordWrap(True)
            l.addWidget(lbl)
            
            if formula:
                mv = MathViewer()
                mv.set_formula(formula)
                l.addWidget(mv)
                
            w.setStyleSheet("background: #f0f0f0; border-radius: 5px; padding: 5px;")
            self.steps_layout.addWidget(w)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OdeApp()
    window.show()
    sys.exit(app.exec())