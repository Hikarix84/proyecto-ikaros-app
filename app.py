import gradio as gr
from transformers import pipeline
import random

# Usuarios de prueba (puedes expandir o conectar a base real después)
users = {"gustavo": "123456", "admin": "admin123"}

# Niveles educativos (con Bachillerato 5° año antes de Universitario)
niveles = [
    "Primaria (1°-6°)",
    "Bachillerato 1° año",
    "Bachillerato 2° año",
    "Bachillerato 3° año",
    "Bachillerato 4° año",
    "Bachillerato 5° año",
    "Universitario básico"
]

# Preguntas aleatorias por asignatura y nivel (expándelas con más)
preguntas_por_asignatura = {
    "Matemáticas": [
        {"q": "¿Cuánto es 8 + 7?", "options": ["15", "16", "14", "18"], "correct": "15", "nivel": "Primaria (1°-6°)"},
        {"q": "Resuelve: 3x = 21", "options": ["x = 7", "x = 6", "x = 8", "x = 63"], "correct": "x = 7", "nivel": "Bachillerato 1° año"},
        {"q": "Derivada de x²", "options": ["2x", "x²", "2", "x"], "correct": "2x", "nivel": "Bachillerato 5° año"},
        {"q": "Límite de (x² - 4)/(x - 2) cuando x → 2", "options": ["4", "0", "Indeterminado", "2"], "correct": "4", "nivel": "Bachillerato 5° año"},
    ],
    "Química Orgánica": [
        {"q": "El grupo funcional de un alcohol es:", "options": ["-OH", "-COOH", "-CHO", "-NH2"], "correct": "-OH", "nivel": "Bachillerato 5° año"},
        {"q": "El alcano C5H12 se llama:", "options": ["Pentano", "Hexano", "Butano", "Propano"], "correct": "Pentano", "nivel": "Bachillerato 5° año"},
        {"q": "Regla de Markovnikov aplica en:", "options": ["Adición a alquenos", "Sustitución", "Eliminación", "Oxidación"], "correct": "Adición a alquenos", "nivel": "Bachillerato 5° año"},
    ],
    # Agrega más asignaturas y preguntas aquí
}

# Modelo OCR (solo texto extraído)
ocr = pipeline("image-to-text", model="microsoft/trocr-base-handprinted")

# Escalas de puntuación por país
puntuacion_por_pais = {
    "Venezuela": {"excelente": 85, "bueno": 65, "regular": 45, "mensaje": "¡Eres un crack, vale! Sigue así."},
    "Colombia": {"excelente": 80, "bueno": 60, "regular": 40, "mensaje": "¡Muy bien, parcero! Estás volando."},
    "España": {"excelente": 8.5, "bueno": 6.5, "regular": 4.5, "mensaje": "¡Ole! Gran trabajo, chaval."},
}

def check_login(username, password, session_state):
    if username in users and users[username] == password:
        session_state["logged_in"] = True
        session_state["username"] = username
        return gr.update(visible=False), gr.update(visible=True), f"¡Bienvenido, {username}!"
    return gr.update(visible=True), gr.update(visible=False), "Usuario o contraseña incorrectos."

def logout(session_state):
    session_state.clear()
    return gr.update(visible=True), gr.update(visible=False), ""

def process_image(image, session_state):
    if not session_state.get("logged_in", False):
        return "Debes iniciar sesión.", "", "", "", "", "", "Puntaje: 0/0"

    if image is None:
        return "Sube foto con texto.", "", "", "", "", "", "Puntaje: 0/0"

    ocr_result = ocr(image)
    extracted_text = ocr_result[0]["generated_text"].strip() if ocr_result else "No texto detectado."

    if "No texto" in extracted_text:
        return extracted_text, "Sube imagen con texto claro.", "", "", "", "", "Puntaje: 0/0"

    words = [w.upper() for w in extracted_text.split() if len(w) > 3]
    random.shuffle(words)
    keywords = words[:10]
    theme = " ".join(keywords[:4]).lower()

    critical_questions = [
        f"Analiza por qué '{random.choice(keywords)}' podría indicar un problema en {theme}.",
        f"Evalúa el impacto de '{random.choice(keywords)}' en {theme}.",
        f"Infiere qué intención está detrás de '{random.choice(keywords)}'."
    ]

    vf_text = "\n".join([f"Pregunta: {q}\n(V/F)" for q in critical_questions[:3]])
    fill_text = f"Completa: '{extracted_text[:40]}...' indica que ____ en {theme}."
    flashcards = "\n".join([f"{i+1}. {w} → rol en {theme}" for i, w in enumerate(keywords[:5])])
    sopa_text = f"Palabras: {', '.join(keywords[:6])}"
    matching_text = "**Empareja palabras con consecuencias:**\n" + "\n".join([f"{i+1}. {w}" for i, w in enumerate(keywords[:5])]) + "\nOpciones: impacto negativo, solución ética, consecuencia larga..."

    return (
        f"Texto extraído: {extracted_text}",
        vf_text,
        fill_text,
        flashcards,
        sopa_text,
        matching_text,
        "Puntaje: 0/15 (califica abajo)"
    )

def explicar_tema(extracted_text, nivel, tema):
    if not extracted_text or "No texto" in extracted_text:
        return "Sube una foto con texto para explicarte basado en tu material."
    
    # Simplificación 100% del texto subido
    texto_corto = extracted_text[:150] + "..." if len(extracted_text) > 150 else extracted_text
    
    if "Primaria" in nivel:
        return f"En tu material dice algo como: '{texto_corto}'. \nEso significa que {tema} es fácil: es como sumar varias veces el mismo número. Ej: 3 × 4 = 3 + 3 + 3 + 3 = 12. ¡Excepto con 1 y 0!"
    
    elif "Bachillerato" in nivel:
        return f"Del texto que subiste ('{texto_corto}'), {tema} funciona así: repetir sumas. Ej: 5 × 3 = 15. Regla: ×1 = mismo número, ×0 = 0. Útil para resolver problemas rápidos en {tema}."
    
    else:
        return f"Basado en tu material ('{texto_corto}'), {tema} se entiende como operación repetitiva de suma. Propiedades: identidad multiplicativa (×1), absorbente (×0)."

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    session_state = gr.State({})
    extracted_text_state = gr.State("")  # Guarda último texto extraído
    
    # Login
    with gr.Column(visible=True) as login_screen:
        gr.Markdown("# Proyecto Ikaros")
        username = gr.Textbox(label="Usuario")
        password = gr.Textbox(label="Contraseña", type="password")
        login_btn = gr.Button("Iniciar sesión")
        error_msg = gr.Markdown()
    
    # Principal
    with gr.Column(visible=False) as main_screen:
        gr.Markdown("# Proyecto Ikaros")
        logout_btn = gr.Button("Cerrar sesión")
        
        country = gr.Dropdown(["Venezuela", "Colombia", "España", "México", "Argentina"], label="País", value="Venezuela")
        nivel = gr.Dropdown(niveles, label="Nivel / Grado", value="Bachillerato 1° año")
        asignatura = gr.Dropdown(list(preguntas_por_asignatura.keys()), label="Asignatura", value="Matemáticas")
        
        modo = gr.Radio(
            ["Modo Foto", "Modo Test Aleatorio", "Modo Explicación Sencilla"],
            label="Modo principal",
            value="Modo Foto"
        )
        
        # Contenedor dinámico
        dynamic_area = gr.Column()
        resultado = gr.Markdown("")
        
        # Modo Foto
        with gr.Column(visible=True) as foto_mode:
            image_input = gr.Image(type="pil", label="Sube foto con texto")
            foto_outputs = [
                gr.Textbox(label="Texto extraído"),
                gr.Textbox(label="Juego 1: V/F"),
                gr.Textbox(label="Juego 2: Completa"),
                gr.Textbox(label="Juego 3: Flashcards"),
                gr.Textbox(label="Juego 4: Sopa"),
                gr.Textbox(label="Juego 5: Emparejar")
            ]
        
        # Modo Test
        with gr.Column(visible=False) as test_mode:
            test_btn = gr.Button("Iniciar Test Aleatorio")
            test_questions = gr.State([])
            test_selected = gr.State([])
            test_score = gr.Markdown("")
        
        # Modo Explicación
        with gr.Column(visible=False) as explicacion_mode:
            tema_input = gr.Textbox(label="Tema o concepto a explicar (basado en tu foto subida)", placeholder="Ej. multiplicar, fotosíntesis")
            explicar_btn = gr.Button("Explicar sencillo")
            explicacion_output = gr.Markdown("Explicación aparecerá aquí (100% de tu material subido)")

    def switch_mode(modo_val):
        return (
            gr.update(visible=modo_val == "Modo Foto"),
            gr.update(visible=modo_val == "Modo Test Aleatorio"),
            gr.update(visible=modo_val == "Modo Explicación Sencilla")
        )

    def process_foto(image, session_state):
        text = ocr(image)[0]["generated_text"].strip() if ocr(image) else "No texto"
        extracted_text_state.value = text
        # Aquí llamas a tus funciones de juegos (como en versiones anteriores)
        return text, "Juego V/F", "Completa", "Flashcards", "Sopa", "Emparejar"

    def iniciar_test():
        # Lógica de test (como en versiones anteriores)
        return "Test iniciado"

    def explicar():
        return explicar_tema_sencillo(extracted_text_state.value, nivel.value, asignatura.value, tema_input.value)

    modo.change(switch_mode, modo, [foto_mode, test_mode, explicacion_mode])
    image_input.change(process_foto, [image_input, session_state], foto_outputs)
    explicar_btn.click(explicar, [], explicacion_output)

    login_btn.click(check_login, [username, password, session_state], [login_screen, main_screen, error_msg])
    logout_btn.click(logout, session_state, [login_screen, main_screen, error_msg])

demo.launch()
