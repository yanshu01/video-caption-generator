from pathlib import Path
from typing import Any
import math

from faster_whisper import WhisperModel

from hinglish_converter import HinglishConverter


class VideoTranscriber:
    def __init__(self, model_size: str = "small") -> None:
        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
        )

        self.hinglish_converter = HinglishConverter()

    def split_into_timed_chunks(
        self,
        text: str,
        start_time: float,
        end_time: float,
        max_duration: float = 2.0,
    ) -> list[dict[str, Any]]:
        duration = end_time - start_time
        words = text.split()

        if not words:
            return []

        chunk_count = max(
            1,
            math.ceil(duration / max_duration),
        )

        # Avoid creating more chunks than words.
        chunk_count = min(chunk_count, len(words))

        words_per_chunk = math.ceil(
            len(words) / chunk_count
        )

        chunks: list[dict[str, Any]] = []

        for index in range(chunk_count):
            word_start = index * words_per_chunk
            word_end = min(
                word_start + words_per_chunk,
                len(words),
            )

            chunk_words = words[word_start:word_end]

            if not chunk_words:
                continue

            chunk_start = (
                start_time
                + (duration * index / chunk_count)
            )

            chunk_end = (
                start_time
                + (
                    duration
                    * (index + 1)
                    / chunk_count
                )
            )

            chunks.append(
                {
                    "start": round(chunk_start, 3),
                    "end": round(chunk_end, 3),
                    "text": " ".join(chunk_words),
                }
            )

        return chunks

    def transcribe(
        self,
        video_path: str | Path,
    ) -> tuple[list[dict[str, Any]], str]:
        segments_generator, _ = self.model.transcribe(
            str(video_path),
            language="hi",
            task="transcribe",
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 400,
            },
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
            initial_prompt=None,
        )

        transcription: list[dict[str, Any]] = []

        for segment in segments_generator:
            original_text = segment.text.strip()

            if not original_text:
                continue

            hinglish_text = (
                self.hinglish_converter.convert(
                    original_text
                )
            )

            if not hinglish_text:
                continue

            timed_chunks = self.split_into_timed_chunks(
                text=hinglish_text,
                start_time=float(segment.start),
                end_time=float(segment.end),
                max_duration=2.0,
            )

            transcription.extend(timed_chunks)

        return transcription, "Hinglish"