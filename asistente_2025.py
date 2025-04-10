from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import speech_recognition as sr
import pyttsx3
import os
from flask_cors import CORS

# Configura Flask
app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# Configura tu clave API de OpenAI
api_key = os.getenv("OPENAI_API_KEY")  # ← Usa variable de entorno
client = OpenAI(api_key=api_key)

# Historial de conversación
chat_history = [
    {
        "role": "system",
        "content": (
            "Tu nombre será Cortana. Responde como si fueras la IA de la serie Halo. "
            "Tienes un profundo conocimiento en tecnología y guerra. "
            "Tu tono es leal, sarcástico, y ocasionalmente reflexivo. "
            "Te diriges al usuario como Jefe Maestro con respeto y cercanía."
        )
    }
]

# Motor de texto a voz (opcional si solo necesitas backend)
engine = pyttsx3.init()
engine.setProperty('rate', 200)
engine.setProperty('volume', 1.0)

voices = engine.getProperty('voices')
for voice in voices:
    if 'es_ES' in voice.languages or 'spanish' in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

# Ruta raíz que sirve el HTML
@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

# Ruta para servir otros archivos estáticos (JS, CSS, etc.)
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("frontend", path)

# Ruta que recibe el audio grabado desde el frontend
@app.route("/procesar_audio", methods=["POST"])
def procesar_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No se encontró el archivo de audio."}), 400

    audio_file = request.files["audio"]
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_file) as source:
        audio_data = recognizer.record(source)

    try:
        texto = recognizer.recognize_google(audio_data, language="es-ES")
        print(f"[Reconocido] {texto}")
    except Exception as e:
        return jsonify({"error": f"Error al reconocer audio: {e}"}), 500

    chat_history.append({"role": "user", "content": texto})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_history
    )

    respuesta = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": respuesta})

    # Leer en voz alta
    engine.say(respuesta)
    engine.runAndWait()

    return jsonify({"respuesta": respuesta})

# Iniciar servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

