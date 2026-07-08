import re

from flask import Flask, jsonify, render_template, request

from config import get_google_api_key
from services.gemini_service import resumir_texto, responder_desde_fragmentos
from services.youtube_service import extraer_id, get_transcript, TranscriptError
from uuid import uuid4

app = Flask(__name__)


def rank_chunks_by_query(chunks, query, k=4):
    """Fallback ranking when chromadb retrieval is unavailable."""
    query_terms = [term for term in re.findall(r"\w+", query.lower()) if len(term) > 2]
    if not query_terms:
        return chunks[:k]

    term_set = set(query_terms)
    scored = []
    for chunk in chunks:
        text = chunk.get("text", "").lower()
        score = sum(text.count(term) for term in term_set)
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = [chunk for score, chunk in scored if score > 0]
    if not results:
        results = [chunk for _, chunk in scored[:k]]
    return results[:k]

@app.route("/", methods=["GET", "POST"])
def index():
    """Render the main page and handle transcript fetching from YouTube."""
    transcripcion = ""
    fragmentos_con_tiempo = []
    error = ""
    url = ""
    idiomas_disponibles = []
    idioma_elegido = ""
    pregunta = ""
    respuesta_pregunta = ""

    if request.method == "POST":
        url = request.form.get("url", "")
        idioma_elegido = request.form.get("idioma", "")
        pregunta = request.form.get("pregunta", "").strip()
        video_id = extraer_id(url)

        if not video_id:
            error = "URL invalida. Asegurate de pegar un link de YouTube correcto."
        else:
            try:
                resultado = get_transcript(url, idioma_elegido)
                transcripcion = resultado["transcripcion"]
                fragmentos_con_tiempo = resultado["fragmentos_con_tiempo"]
                idiomas_disponibles = resultado["idiomas_disponibles"]

                if pregunta:
                    top_chunks = []
                    try:
                        from services.retrieval_service import index_chunks, query
                        collection_name = f"yt_{video_id}_{uuid4().hex}"
                        try:
                            index_chunks(resultado["chunks"], collection_name=collection_name, persist=False)
                            hits = query(pregunta, k=4, collection_name=collection_name)
                            top_chunks = [
                                {
                                    "text": hit["text"],
                                    "title": hit["metadata"].get("title"),
                                    "start_time": hit["metadata"].get("start_time"),
                                    "end_time": hit["metadata"].get("end_time"),
                                }
                                for hit in hits
                            ]
                        except Exception:
                            top_chunks = rank_chunks_by_query(resultado["chunks"], pregunta, k=4)
                    except ImportError:
                        top_chunks = rank_chunks_by_query(resultado["chunks"], pregunta, k=4)

                    respuesta_pregunta = responder_desde_fragmentos(
                        pregunta,
                        top_chunks,
                        get_google_api_key(),
                    )
            except TranscriptError as e:
                error = f"No se pudo obtener la transcripcion. ({e})"
            except Exception as e:
                error = f"No se pudo obtener la transcripcion. ({e})"

    return render_template(
        "index.html",
        transcripcion=transcripcion,
        fragmentos_con_tiempo=fragmentos_con_tiempo,
        error=error,
        url=url,
        idiomas_disponibles=idiomas_disponibles,
        idioma_elegido=idioma_elegido,
        pregunta=pregunta,
        respuesta_pregunta=respuesta_pregunta,
    )

@app.route("/resumir", methods=["POST"])
def resumir():
    """Generate a summary from the submitted transcript using the configured API key."""
    data = request.get_json()
    transcripcion = data.get("transcripcion", "")
    if not transcripcion:
        return jsonify({"error": "No hay transcripcion para resumir."})

    api_key = get_google_api_key()
    if not api_key:
        return jsonify({
            "error": "No se encontró la API key de Google. Agrega tu clave en el archivo .env del proyecto."
        })

    try:
        resumen = resumir_texto(transcripcion, api_key)
        return jsonify({"resumen": resumen})
    except Exception as e:
        return jsonify({"error": f"No se pudo generar el resumen. ({e})"})

if __name__ == "__main__":
    app.run(debug=True)
