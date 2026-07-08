# Transcriptor de YouTube

Aplicación Flask para transcribir videos de YouTube con timestamps, chunking y soporte de análisis/consulta.

## Arquitectura

1. `app.py`
   - Endpoint `/` para recibir la URL de YouTube y mostrar la transcripción.
   - Endpoint `/resumir` para generar un resumen usando Gemini.

2. `services/youtube_service.py`
   - Extrae el `video_id` de la URL.
   - Intenta primero `youtube-transcript-api` para obtener subtítulos.
   - Si no hay subtítulos, descarga audio con `yt-dlp` y transcribe con `faster-whisper`.
   - Normaliza la salida en segmentos `{ text, start, end }`.
   - Chunking por tiempo y palabras con `start_time` y `end_time`.

3. `services/gemini_service.py`
   - Genera resúmenes con Gemini.
   - Tiene helper para respuestas que citan timestamps aproximados.

4. `services/retrieval_service.py`
   - Usa Chroma local para indexar embeddings.
   - Permite búsqueda de similaridad y metadatos de chunks.

## Requisitos

- Python 3.x
- Flask
- `youtube-transcript-api`
- `google-generativeai`
- `yt-dlp` (opcional, para fallback cuando no hay subtítulos)
- `faster-whisper` (opcional, para fallback cuando no hay subtítulos)
- `chromadb` (opcional, para vector store local)
- `sentence-transformers` (opcional, para embeddings locales)

## Configuración

1. Crear un archivo `.env` en la raíz con:

```env
GOOGLE_API_KEY=tu_api_key_aqui
```

2. Instalar dependencias y ejecutar la app:

```bash
python3 app.py
```

## Uso

- Pegar la URL de YouTube en la pantalla principal.
- Seleccionar el idioma si hay subtítulos disponibles.
- Ver la transcripción en texto completo o con timestamps.
- Usar el botón `RESUMIR CON IA` para generar un resumen.

## Notas

- Los timestamps en la respuesta son aproximados al chunk de 30-60 segundos.
- El fallback a Whisper solo se activa si no hay subtítulos detectados.
- La indexación con Chroma está pensada para escalar a varios videos o episodios.
- Si querés usar la funcionalidad de retrieval/QA, necesitás indexar los chunks y llamar al modelo con el prompt que incluya los timestamps.

## Tests

Ejecutar los tests unitarios con:

```bash
python3 -m unittest
```
