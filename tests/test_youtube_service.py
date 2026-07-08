import unittest

from services.youtube_service import (
    chunk_segments,
    extraer_id,
    segundos_a_tiempo,
    _normalize_segments,
)


class YoutubeServiceTests(unittest.TestCase):
    def test_extraer_id_valid(self):
        self.assertEqual(
            extraer_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_extraer_id_short_url(self):
        self.assertEqual(
            extraer_id("https://youtu.be/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_extraer_id_invalid(self):
        self.assertIsNone(extraer_id("https://example.com/watch?v=123"))

    def test_segundos_a_tiempo_mmss(self):
        self.assertEqual(segundos_a_tiempo(75), "1:15")
        self.assertEqual(segundos_a_tiempo(599), "9:59")

    def test_segundos_a_tiempo_hhmmss(self):
        self.assertEqual(segundos_a_tiempo(3661), "1:01:01")

    def test_normalize_segments_sorts_and_filters(self):
        source = [
            {"text": "Second", "start": 5.0, "end": 7.0},
            {"text": "", "start": 1.0, "end": 2.0},
            {"text": "First", "start": 1.0, "end": 3.0},
        ]
        normalized = _normalize_segments(source)
        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized[0]["text"], "First")
        self.assertEqual(normalized[1]["text"], "Second")

    def test_chunk_segments_creates_chunks(self):
        segments = [
            {"text": "Hola", "start": 0.0, "end": 2.0},
            {"text": "mundo", "start": 2.0, "end": 4.0},
            {"text": "esto es", "start": 4.0, "end": 7.0},
            {"text": "una prueba", "start": 7.0, "end": 10.0},
        ]
        chunks = chunk_segments(segments, video_id="abc123", title="Test", target_seconds=5, max_words=100, overlap_segments=1)
        self.assertGreaterEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["video_id"], "abc123")
        self.assertEqual(chunks[0]["title"], "Test")
        self.assertEqual(chunks[0]["start_time"], "0:00")
        self.assertEqual(chunks[0]["end_time"], "0:07")
        self.assertIn("Hola", chunks[0]["text"])


if __name__ == "__main__":
    unittest.main()
