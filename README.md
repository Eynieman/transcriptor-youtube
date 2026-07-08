# Transcriptor de YouTube

Aplicación web desarrollada con Flask para transcribir videos de YouTube, visualizar subtítulos con marcas de tiempo, generar resúmenes con IA y responder preguntas sobre el contenido del video.

## Funcionalidades principales

- Ingresá una URL de YouTube y obtené la transcripción del video.
- Elegí el idioma disponible cuando el video incluye subtítulos.
- Visualizá la transcripción en formato de texto completo o con timestamps.
- Generá resúmenes automáticos utilizando Gemini.
- Consultá el contenido del video mediante preguntas naturales, con respuestas basadas en la transcripción.
- Si no existen subtítulos, la app puede recurrir a la transcripción por audio mediante Whisper.

## Estructura del proyecto

- app.py: punto de entrada de la aplicación y lógica de las rutas principales.
- services/youtube_service.py: obtención de subtítulos, transcripción por audio y preparación de fragmentos.
- services/gemini_service.py: generación de resúmenes y respuestas a preguntas.
- services/retrieval_service.py: motor opcional de recuperación semántica con Chroma y embeddings.
- templates/index.html: interfaz web principal.

## Requisitos

- Python 3.9 o superior
- Flask
- youtube-transcript-api
- google-generativeai
- yt-dlp (opcional, para transcripción por audio)
- faster-whisper (opcional, para transcripción por audio)
- chromadb (opcional, para retrieval local)
- sentence-transformers (opcional, para embeddings locales)

## Instalación

1. Crear y activar un entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

3. Configurar la API key de Google en un archivo .env en la raíz del proyecto:

```env
GOOGLE_API_KEY=tu_api_key_aqui
```

## Ejecución

Iniciá la aplicación con cualquiera de los siguientes comandos:

```bash
python3 app.py
```

o

```bash
./run.sh
```

La interfaz estará disponible en http://127.0.0.1:5000/.

## Uso

1. Pegá la URL del video en el formulario principal.
2. Seleccioná el idioma si el video ofrece subtítulos disponibles.
3. Elegí si querés ver la transcripción completa o con marcas de tiempo.
4. Utilizá el botón de resumen para obtener una síntesis con IA.
5. Escribí una pregunta sobre el video para recibir una respuesta basada en la transcripción.

## Notas importantes

- Las funciones de resumen y preguntas requieren una API key válida de Gemini.
- Si no hay subtítulos disponibles, la app intenta transcribir el audio con Whisper.
- La funcionalidad de retrieval con Chroma es opcional y requiere instalar las dependencias adicionales.
- Los timestamps son aproximados y sirven como referencia para navegar la transcripción.

## Pruebas

Para ejecutar las pruebas unitarias:

```bash
python3 -m unittest
```
