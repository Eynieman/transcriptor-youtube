import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
)

try:
    from yt_dlp import YoutubeDL
except ImportError:
    YoutubeDL = None

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


class TranscriptError(Exception):
    pass


def extraer_id(url: str) -> Optional[str]:
    """Extract the YouTube video ID from a valid YouTube URL."""
    patron = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    resultado = re.search(patron, url)
    return resultado.group(1) if resultado else None


def segundos_a_tiempo(segundos: float) -> str:
    """Convert seconds into a readable HH:MM:SS or MM:SS format."""
    segundos = int(round(segundos))
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    if horas > 0:
        return f"{horas}:{minutos:02d}:{segs:02d}"
    return f"{minutos}:{segs:02d}"


def list_available_languages(video_id: str) -> List[Dict[str, object]]:
    """Return the available transcript languages and translation options."""
    try:
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.list(video_id)
    except (NoTranscriptFound, TranscriptsDisabled):
        return []

    idiomas_disponibles = []
    for transcript in transcript_list:
        idiomas_disponibles.append({
            "codigo": transcript.language_code,
            "nombre": transcript.language,
            "auto": transcript.is_generated,
            "traduccion": False,
        })

    try:
        primer_transcript = next(iter(transcript_list))
        for trad in getattr(primer_transcript, "translation_languages", []):
            idiomas_disponibles.append({
                "codigo": f"trad_{trad['language_code']}",
                "nombre": trad["language"],
                "auto": False,
                "traduccion": True,
            })
    except Exception:
        pass

    return idiomas_disponibles


def fetch_subtitle_segments(video_id: str, idioma_elegido: str) -> List[Dict[str, object]]:
    """Fetch subtitles from YouTubeTranscriptApi and normalize them into segments."""
    ytt = YouTubeTranscriptApi()
    transcript_list = ytt.list(video_id)

    if idioma_elegido.startswith("trad_"):
        target_language = idioma_elegido.replace("trad_", "")
        transcript = next(iter(transcript_list))
        fragmentos = transcript.translate(target_language).fetch()
    else:
        transcript = transcript_list.find_transcript([idioma_elegido])
        fragmentos = transcript.fetch()

    if not fragmentos:
        raise TranscriptError("No se encontraron subtítulos para el idioma solicitado.")

    return _normalize_segments(fragmentos)


def has_subtitles(video_id: str) -> bool:
    """Return whether the video has any subtitle tracks available."""
    return bool(list_available_languages(video_id))


def _download_audio(url: str, temp_dir: Path) -> Path:
    """Download audio from YouTube and return a local file path."""
    if YoutubeDL is None:
        raise TranscriptError("La dependencia yt-dlp no está instalada.")

    temp_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(temp_dir / "%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info:
        raise TranscriptError("No se pudo descargar el audio de YouTube.")

    if "requested_downloads" in info and info["requested_downloads"]:
        audio_path = Path(info["requested_downloads"][0].get("filepath", ""))
    else:
        audio_path = Path(info.get("filepath", ""))

    if not audio_path or not audio_path.exists():
        raise TranscriptError("El archivo de audio descargado no se encontró.")

    return audio_path


def _transcribe_audio_whisper(audio_path: Path, model_name: str = "small") -> List[Dict[str, object]]:
    """Transcribe audio using faster-whisper and return normalized segments."""
    if WhisperModel is None:
        raise TranscriptError("La dependencia faster-whisper no está instalada.")

    model = WhisperModel(model_name, device="auto")
    segments, _ = model.transcribe(str(audio_path), beam_size=5)

    return _normalize_segments([
        {
            "text": segment.text.strip(),
            "start": float(segment.start),
            "end": float(segment.end),
        }
        for segment in segments
        if getattr(segment, "text", "").strip()
    ])


def transcribe_audio_from_url(url: str) -> List[Dict[str, object]]:
    """Download audio from a YouTube URL and transcribe it with Whisper."""
    temp_dir = Path(tempfile.mkdtemp(prefix="yt_transcript_"))
    try:
        audio_path = _download_audio(url, temp_dir)
        return _transcribe_audio_whisper(audio_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _as_segment_dict(seg: object) -> Dict[str, object]:
    """Normalize a transcript segment object or dict into a standard dict."""
    if isinstance(seg, dict):
        text = seg.get("text", "")
        start = seg.get("start", 0)
        end = seg.get("end")
        duration = seg.get("duration", 0.0)
    else:
        text = getattr(seg, "text", "")
        start = getattr(seg, "start", 0)
        end = getattr(seg, "end", None)
        duration = getattr(seg, "duration", 0.0)

    if end is None:
        end = float(start or 0) + float(duration or 0.0)

    return {
        "text": str(text).strip(),
        "start": float(start or 0),
        "end": float(end or 0),
    }


def _normalize_segments(segments: List[object]) -> List[Dict[str, object]]:
    """Ensure transcript segments are sorted and contain valid times/text."""
    normalized = []
    for seg in segments:
        item = _as_segment_dict(seg)
        if item["text"] and item["end"] > item["start"]:
            normalized.append(item)
    return sorted(normalized, key=lambda item: item["start"])


def chunk_segments(
    segments: List[Dict[str, object]],
    video_id: Optional[str] = None,
    title: Optional[str] = None,
    target_seconds: int = 45,
    max_words: int = 250,
    overlap_segments: int = 2,
) -> List[Dict[str, object]]:
    """Group raw transcript segments into chunks with approximate timestamps."""
    if not segments:
        return []

    chunks = []
    current_chunk = []
    current_word_count = 0

    def emit_chunk(data):
        if not data:
            return
        chunk_text = " ".join([seg["text"] for seg in data])
        chunk = {
            "id": f"{video_id or 'video'}_{len(chunks) + 1}",
            "video_id": video_id,
            "title": title,
            "text": chunk_text,
            "start": data[0]["start"],
            "end": data[-1]["end"],
            "start_time": segundos_a_tiempo(data[0]["start"]),
            "end_time": segundos_a_tiempo(data[-1]["end"]),
            "word_count": sum(len(seg["text"].split()) for seg in data),
            "segment_count": len(data),
            "segments": data.copy(),
        }
        chunks.append(chunk)

    for segment in segments:
        if not current_chunk:
            current_chunk = []
            current_word_count = 0

        current_chunk.append(segment)
        current_word_count += len(segment["text"].split())
        chunk_duration = segment["end"] - current_chunk[0]["start"]

        if chunk_duration >= target_seconds or current_word_count >= max_words:
            emit_chunk(current_chunk)
            current_chunk = current_chunk[-overlap_segments:].copy() if overlap_segments else []
            current_word_count = sum(len(seg["text"].split()) for seg in current_chunk)

    if current_chunk:
        emit_chunk(current_chunk)

    return chunks


def get_video_title(url: str) -> Optional[str]:
    """Return the YouTube video title using yt-dlp info extraction."""
    if YoutubeDL is None:
        return None

    with YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info.get("title")
        except Exception:
            return None


def get_transcript(url: str, idioma_elegido: Optional[str] = None) -> Dict[str, object]:
    """Return normalized transcript data and a chunked pipeline-ready result."""
    video_id = extraer_id(url)
    if not video_id:
        raise TranscriptError("URL de YouTube no válida.")

    idiomas_disponibles = list_available_languages(video_id)
    segments = []

    if idioma_elegido:
        try:
            if has_subtitles(video_id):
                segments = fetch_subtitle_segments(video_id, idioma_elegido)
            else:
                segments = transcribe_audio_from_url(url)
        except TranscriptError:
            if not idiomas_disponibles:
                segments = transcribe_audio_from_url(url)
            else:
                raise

    transcripcion = " ".join([seg["text"] for seg in segments])
    fragmentos_con_tiempo = [
        {"tiempo": segundos_a_tiempo(seg["start"]), "texto": seg["text"]}
        for seg in segments
    ]
    title = get_video_title(url)
    chunks = chunk_segments(segments, video_id=video_id, title=title)

    return {
        "transcripcion": transcripcion,
        "fragmentos_con_tiempo": fragmentos_con_tiempo,
        "idiomas_disponibles": idiomas_disponibles,
        "video_id": video_id,
        "title": title,
        "chunks": chunks,
    }


def obtener_transcripcion(video_id: str, idioma_elegido: Optional[str] = None) -> Dict[str, object]:
    """Backward-compatible helper that accepts a video ID."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    return get_transcript(url, idioma_elegido)
