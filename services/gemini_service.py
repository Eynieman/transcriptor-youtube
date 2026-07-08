import google.generativeai as genai


class GeminiError(Exception):
    pass


def _configure_api(api_key: str):
    if not api_key:
        raise GeminiError("No se encontró la API key de Google.")
    genai.configure(api_key=api_key)


def generar_texto(prompt: str, api_key: str, model: str = "gemini-2.5-flash-lite", temperature: float = 0.2) -> str:
    """Generate text from Gemini using a prompt."""
    _configure_api(api_key)
    modelo = genai.GenerativeModel(model)
    respuesta = modelo.generate_content(
        prompt,
        generation_config={"temperature": temperature},
    )
    return respuesta.text


def resumir_texto(texto: str, api_key: str) -> str:
    """Generate a concise summary of the provided text using Gemini."""
    prompt = (
        "Resume el siguiente texto en un párrafo claro y breve en el mismo idioma en que está escrito. "
        "Si es posible, usa viñetas o frases cortas para destacar los puntos principales.\n\n"
        f"{texto}"
    )
    return generar_texto(prompt, api_key)


def responder_desde_fragmentos(pregunta: str, chunks: list, api_key: str) -> str:
    """Answer a user question using transcript chunks and cite approximate timestamps."""
    if not chunks:
        return "No hay información disponible para responder esa pregunta."

    contexto = []
    for index, chunk in enumerate(chunks, start=1):
        title = chunk.get("title")
        timestamp = chunk.get("start_time") or "0:00"
        end_timestamp = chunk.get("end_time") or "0:00"
        title_part = f" (video: {title})" if title else ""
        contexto.append(
            f"Chunk {index}{title_part} [{timestamp} - {end_timestamp}]: {chunk.get('text', '')}"
        )

    prompt = (
        "Eres un asistente de preguntas y respuestas especializado en transcripciones de YouTube. "
        "Usa únicamente la información provista en los fragmentos a continuación. "
        "No inventes detalles ni información que no aparezca en los fragmentos. "
        "Si no hay suficiente información, di claramente que no puedes responder con certeza.\n\n"
        "Devuelve la respuesta en el siguiente formato exacto:\n"
        "Respuesta: <tu respuesta en un párrafo corto>\n"
        "Referencias:\n"
        "- [video: TÍTULO] [mm:ss - mm:ss]\n"
        "- [video: TÍTULO2] [mm:ss - mm:ss]\n\n"
        "Fragmentos disponibles:\n"
        f"{chr(10).join(contexto)}\n\n"
        f"Pregunta: {pregunta}\n"
        "Respuesta:"
    )

    return generar_texto(prompt, api_key)
