import sys
import os
import json
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QComboBox, QScrollArea, QFrame,
    QDialog, QTextEdit, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QByteArray
from PyQt6.QtGui import QPixmap, QImage

from ode_solver import EcuacionDiferencialSolver 

# =============================================================================
# 🔑 CONFIGURACIÓN DE LA API
# =============================================================================
API_KEY = "AIzaSyALbTjqEJj-YiPUujPKxCEfWsSn-dPck1U" 
# =============================================================================

# --- 1. VISOR MATEMÁTICO ---
class MathViewer(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.page().setBackgroundColor(Qt.GlobalColor.transparent)
        
        self.html_template = """
        <!DOCTYPE html><html><head>
            <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML"></script>
            <style>
                body {{ font-family: 'Segoe UI', sans-serif; font-size: 18px; color: #333; margin: 0; padding: 5px; display: flex; justify-content: center; align-items: center; overflow: hidden; }}
                .MathJax_Display {{ margin: 0 !important; }}
            </style>
        </head><body><div id="math">{}</div></body></html>
        """
        self.setHtml(self.html_template.format(""))

    def set_formula(self, latex):
        if not latex: latex = ""
        safe_latex = f"$${latex}$$"
        content = self.html_template.format(safe_latex)
        self.setHtml(content)

# --- 2. WORKER DE IA ---
class AIWorker(QThread):
    finished_exercise = pyqtSignal(dict)
    finished_explanation = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, mode, data):
        super().__init__()
        self.mode = mode
        self.data = data

    def run(self):
        # Corregido a gemini-1.5-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
        headers = {'Content-Type': 'application/json'}
        
        if self.mode == "generate":
            prompt = (f"Actúa como un profesor de cálculo avanzado. Genera UN problema de Ecuación Diferencial Exacta (o reducible por factor integrante) de dificultad '{self.data}'. "
                      "IMPORTANTE: Usa sintaxis matemática estándar compatible con SymPy (ej: usa 'exp(x)' NO 'math.exp(x)', usa 'sin(y)' NO 'math.sin(y)', usa 'sqrt(x)'). "
                      "Tu respuesta debe ser EXCLUSIVAMENTE un objeto JSON válido (sin markdown) con formato: "
                      "{'enunciado_M': 'expresion_python_sympy', 'enunciado_N': 'expresion_python_sympy'}.")
        
        elif self.mode == "explain":
            prompt = (f"Actúa como un profesor. Un estudiante no entiende este paso:\n"
                      f"Contexto ED: {self.data['contexto']}\n"
                      f"Paso actual: {self.data['paso_titulo']}\n"
                      f"Fórmula del paso: {self.data['formula']}\n"
                      f"Explica breve y didácticamente qué operación matemática se hizo para llegar a ese resultado.")

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            text_resp = result['candidates'][0]['content']['parts'][0]['text']

            if self.mode == "generate":
                clean_text = text_resp.replace('```json', '').replace('```', '').strip()
                data_dict = json.loads(clean_text)
                self.finished_exercise.emit(data_dict)
            else:
                self.finished_explanation.emit(text_resp)

        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

# --- 3. TARJETA DE PASO ---
class StepCard(QFrame):
    def __init__(self, step_data, parent_app):
        super().__init__()
        self.step_data = step_data
        self.parent_app = parent_app
        self.init_ui()

    def init_ui(self):
        self.setObjectName("StepCard")
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        lbl_title = QLabel(self.step_data['titulo'])
        lbl_title.setObjectName("StepTitle")
        layout.addWidget(lbl_title)
        
        lbl_text = QLabel(self.step_data['texto'])
        lbl_text.setWordWrap(True)
        lbl_text.setObjectName("StepText")
        layout.addWidget(lbl_text)
        
        if self.step_data['formula']:
            viewer = MathViewer()
            viewer.set_formula(self.step_data['formula'])
            layout.addWidget(viewer)
            
        btn_ask = QPushButton("🤖 Explícame este paso")
        btn_ask.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ask.setObjectName("BtnAskAI")
        btn_ask.clicked.connect(self.ask_ai)
        layout.addWidget(btn_ask, alignment=Qt.AlignmentFlag.AlignRight)

    def ask_ai(self):
        self.parent_app.open_explanation_dialog(self.step_data)

# --- 4. VENTANA EMERGENTE ---
class ExplanationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profe IA - Explicación")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)
        
        self.lbl_info = QLabel("🤖 <b>Analizando tu duda...</b>")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setStyleSheet("font-size: 14px; color: #6c5ce7;")
        layout.addWidget(self.lbl_info)
        
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("border: 1px solid #eee; padding: 10px; font-size: 14px; color: #333; background-color: #f9f9f9;")
        layout.addWidget(self.text_area)
        
        self.btn_close = QPushButton("¡Entendido!")
        self.btn_close.clicked.connect(self.accept)
        self.btn_close.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        self.btn_close.hide()
        layout.addWidget(self.btn_close)

    def set_text(self, text):
        self.lbl_info.setText("🤖 <b>Explicación:</b>")
        self.text_area.setMarkdown(text)
        self.btn_close.show()

# --- 5. APLICACIÓN PRINCIPAL ---
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ED-Solver: UNIPUTUMAYO")
        self.setGeometry(100, 100, 1200, 800)
        self.solver = EcuacionDiferencialSolver()
        
        self.apply_styles()
        
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QHBoxLayout(central)
        self.main_layout.setContentsMargins(0,0,0,0)
        
        self.create_sidebar()
        self.create_content_area()
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f4f6f9; }
            QLabel { font-family: 'Segoe UI'; color: #2c3e50; }
            #Sidebar { background-color: #ffffff; border-right: 1px solid #d1d8e0; }
            #UniTitle { font-size: 18px; font-weight: bold; color: #1e3799; margin-top: 10px; }
            #CareerSubtitle { font-size: 13px; color: #576574; font-weight: 500; margin-bottom: 20px; }
            #DevNames { font-size: 12px; color: #7f8c8d; font-style: italic; margin-bottom: 15px; }
            QLineEdit { padding: 10px; border: 2px solid #dfe6e9; border-radius: 8px; font-size: 14px; background: #fff; }
            QLineEdit:focus { border: 2px solid #6c5ce7; }
            QPushButton { padding: 10px; border-radius: 8px; font-weight: bold; font-size: 13px; }
            #BtnSolve { background-color: #0984e3; color: white; border: none; }
            #BtnSolve:hover { background-color: #74b9ff; }
            #BtnAI { background-color: #6c5ce7; color: white; border: none; }
            #BtnAI:hover { background-color: #a29bfe; }
            #StepCard { background-color: white; border: 1px solid #dfe6e9; border-radius: 12px; padding: 10px; }
            #StepTitle { font-size: 16px; font-weight: bold; color: #0984e3; }
        """)

    def load_local_logo(self, filename="logo.png"):
        if os.path.exists(filename):
            return QPixmap(filename)
        return None

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(320)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        lbl_logo = QLabel()
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setFixedHeight(120) 
        pixmap = self.load_local_logo("logo.jpeg")
        if pixmap:
            lbl_logo.setPixmap(pixmap.scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            lbl_logo.setText("[Logo no encontrado]")
            lbl_logo.setStyleSheet("border: 2px dashed #ccc; color: #999;")
        
        layout.addWidget(lbl_logo)
        layout.addWidget(QLabel("Universidad del Putumayo", objectName="UniTitle", alignment=Qt.AlignmentFlag.AlignCenter))
        layout.addWidget(QLabel("Tecnología en Desarrollo de Software", objectName="CareerSubtitle", alignment=Qt.AlignmentFlag.AlignCenter))
        
        lbl_devs = QLabel("Daniel Alejandro Macías Pérez\nJose Leonel Enriquez Zambrano\nNeider Duvan Gindigua Machoa", objectName="DevNames")
        lbl_devs.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_devs)
        layout.addWidget(QLabel("<hr style='color:#eee'>"))
        
        layout.addWidget(QLabel("<b>Función M(x, y):</b>"))
        self.m_input = QLineEdit()
        self.m_input.setPlaceholderText("Ej: 2*x*y")
        layout.addWidget(self.m_input)
        
        layout.addWidget(QLabel("<b>Función N(x, y):</b>"))
        self.n_input = QLineEdit()
        self.n_input.setPlaceholderText("Ej: x**2")
        layout.addWidget(self.n_input)
        
        self.btn_solve = QPushButton("✨ Resolver")
        self.btn_solve.setObjectName("BtnSolve")
        self.btn_solve.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_solve.clicked.connect(self.solve_manual)
        layout.addWidget(self.btn_solve)
        
        layout.addSpacing(10)
        layout.addWidget(QLabel("<hr style='color:#eee'>"))
        layout.addWidget(QLabel("<b>🧠 Generador IA</b>"))
        self.combo_diff = QComboBox()
        self.combo_diff.addItems(["Principiante", "Intermedio", "Avanzado"])
        layout.addWidget(self.combo_diff)
        
        self.btn_gen_ai = QPushButton("🎲 Ejercicio Sorpresa")
        self.btn_gen_ai.setObjectName("BtnAI")
        self.btn_gen_ai.clicked.connect(self.generate_ai_exercise)
        layout.addWidget(self.btn_gen_ai)
        
        btn_concepts = QPushButton("📘 Conceptos previos")
        btn_concepts.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_concepts.clicked.connect(self.show_concepts_view)
        layout.addWidget(btn_concepts)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)
        
        layout.addStretch()
        self.main_layout.addWidget(sidebar)

    def create_content_area(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        self.lbl_res = QLabel("Solución Final")
        self.lbl_res.setStyleSheet("font-size: 20px; font-weight: bold; color: #2d3436;")
        layout.addWidget(self.lbl_res)

        self.final_res_viewer = MathViewer()
        self.final_res_viewer.setFixedHeight(80)
        self.final_res_viewer.setStyleSheet("border: 1px dashed #ccc; border-radius: 10px;")
        layout.addWidget(self.final_res_viewer)
        
        self.lbl_steps = QLabel("Procedimiento Detallado")
        self.lbl_steps.setStyleSheet("font-size: 16px; font-weight: bold; color: #2d3436; margin-top: 10px;")
        layout.addWidget(self.lbl_steps)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        self.steps_container = QWidget()
        self.steps_container.setStyleSheet("background-color: transparent;")
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.steps_layout.setSpacing(15)
        
        scroll.setWidget(self.steps_container)
        layout.addWidget(scroll)
        self.main_layout.addWidget(content)

    def solve_manual(self):
        m, n = self.m_input.text(), self.n_input.text()
        if not m or not n:
            self.status_lbl.setText("⚠️ Ingresa M y N")
            return
        self.status_lbl.setText("Calculando...")
        self.process_solution(m, n)

    def process_solution(self, m, n):
        while self.steps_layout.count():
            child = self.steps_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        sol, pasos = self.solver.resolver_exacta(m, n)
        
        if sol:
            self.final_res_viewer.set_formula(sol)
            self.status_lbl.setText("✅ Resuelto")
        else:
            self.final_res_viewer.set_formula(r"\text{Sin solución / Error de sintaxis}")
            self.status_lbl.setText("❌ Error")
        
        for paso in pasos:
            card = StepCard(paso, self)
            self.steps_layout.addWidget(card)

    def generate_ai_exercise(self):
        diff = self.combo_diff.currentText()
        self.status_lbl.setText("⏳ IA Generando...")
        self.btn_gen_ai.setEnabled(False)
        self.ai_thread = AIWorker("generate", diff)
        self.ai_thread.finished_exercise.connect(self.on_ai_exercise_ready)
        self.ai_thread.error.connect(self.on_ai_error)
        self.ai_thread.start()

    def on_ai_exercise_ready(self, data):
        self.btn_gen_ai.setEnabled(True)
        self.m_input.setText(data.get('enunciado_M', ''))
        self.n_input.setText(data.get('enunciado_N', ''))
        self.status_lbl.setText("✅ Cargado.")

    def on_ai_error(self, err_msg):
        self.btn_gen_ai.setEnabled(True)
        QMessageBox.warning(self, "Error", f"{err_msg}")

    def open_explanation_dialog(self, step_data):
        context = f"ED: ({self.m_input.text()})dx + ({self.n_input.text()})dy = 0"
        data = {"contexto": context, "paso_titulo": step_data['titulo'], "formula": step_data['formula']}
        self.dialog = ExplanationDialog(self)
        self.dialog.show()
        self.explainer_thread = AIWorker("explain", data)
        self.explainer_thread.finished_explanation.connect(self.dialog.set_text)
        self.explainer_thread.start()
        
    def show_concepts_view(self):
        self.lbl_res.hide()
        self.lbl_steps.hide()
        self.final_res_viewer.hide()

        while self.steps_layout.count():
            child = self.steps_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()

        title = QLabel("📘 Conceptos Previos: Derivadas e Integrales")
        title.setStyleSheet("font-size:18px; font-weight:bold; color:#2d3436;")
        self.steps_layout.addWidget(title)

        # Derivadas
        self.steps_layout.addWidget(QLabel("🔹 <b>Derivadas</b>", styleSheet="font-size:16px;"))
        self.steps_layout.addWidget(QLabel("Derivar significa calcular la razón de cambio...", wordWrap=True))
        dv = MathViewer(); dv.set_formula(r"\frac{d}{dx}(x^n) = n x^{n-1}"); self.steps_layout.addWidget(dv)

        # Integrales
        self.steps_layout.addWidget(QLabel("🔹 <b>Integrales</b>", styleSheet="font-size:16px;"))
        self.steps_layout.addWidget(QLabel("Integrar es el proceso inverso de derivar...", wordWrap=True))
        iv = MathViewer(); iv.set_formula(r"\int x^n \, dx = \frac{x^{n+1}}{n+1} + C"); self.steps_layout.addWidget(iv)

        btn_back = QPushButton("🔙 Volver a la solución")
        btn_back.setStyleSheet("background-color: #0984e3; color: white; padding: 14px; border-radius: 10px; font-weight: bold; margin-top: 20px;")
        btn_back.clicked.connect(self.restore_solution_view)
        self.steps_layout.addWidget(btn_back)
        self.steps_layout.addStretch() # Asegura visibilidad del botón

    def restore_solution_view(self):
        self.lbl_res.show()
        self.lbl_steps.show()
        self.final_res_viewer.show()
        self.solve_manual()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())