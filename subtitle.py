from pathlib import Path
from typing import Any


def hex_to_ass_style_colour(hex_colour: str) -> str:
    """
    Convert #RRGGBB to ASS style colour:
    &H00BBGGRR
    """
    colour = hex_colour.lstrip("#")

    red = colour[0:2]
    green = colour[2:4]
    blue = colour[4:6]

    return f"&H00{blue}{green}{red}"


def hex_to_ass_override_colour(hex_colour: str) -> str:
    """
    Convert #RRGGBB to ASS inline override colour:
    &HBBGGRR&
    """
    colour = hex_colour.lstrip("#")

    red = colour[0:2]
    green = colour[2:4]
    blue = colour[4:6]

    return f"&H{blue}{green}{red}&"


def format_ass_timestamp(seconds: float) -> str:
    total_centiseconds = max(
        0,
        round(seconds * 100),
    )

    hours = total_centiseconds // 360000
    minutes = (
        total_centiseconds % 360000
    ) // 6000
    remaining_seconds = (
        total_centiseconds % 6000
    ) // 100
    centiseconds = total_centiseconds % 100

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{remaining_seconds:02d}."
        f"{centiseconds:02d}"
    )


def escape_ass_text(text: str) -> str:
    return (
        text.replace("\\", r"\\")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def calculate_word_timings(
    words: list[str],
    start_time: float,
    end_time: float,
) -> list[tuple[float, float]]:
    """
    Estimate timing based on word length.

    Longer words receive slightly more screen time.
    """
    if not words:
        return []

    duration = max(
        0.1,
        end_time - start_time,
    )

    weights = [
        max(1, len(word.strip(".,!?")))
        for word in words
    ]

    total_weight = sum(weights)

    timings: list[tuple[float, float]] = []

    current_time = start_time

    for index, weight in enumerate(weights):
        word_duration = (
            duration * weight / total_weight
        )

        word_start = current_time

        if index == len(words) - 1:
            word_end = end_time
        else:
            word_end = current_time + word_duration

        timings.append(
            (
                word_start,
                word_end,
            )
        )

        current_time = word_end

    return timings


def build_kinetic_line(
    words: list[str],
    active_index: int,
    highlight_colour: str,
    pop_scale: int,
    animation_duration_ms: int,
) -> str:
    rendered_words: list[str] = []

    for index, word in enumerate(words):
        safe_word = escape_ass_text(word)

        if index == active_index:
            active_word = (
                "{"
                f"\\c{highlight_colour}"
                "\\b1"
                f"\\fscx{pop_scale}"
                f"\\fscy{pop_scale}"
                f"\\t(0,{animation_duration_ms},"
                "\\fscx100\\fscy100)"
                "}"
                f"{safe_word}"
                "{\\rKinetic}"
            )

            rendered_words.append(active_word)
        else:
            rendered_words.append(safe_word)

    return " ".join(rendered_words)


def create_kinetic_ass_file(
    segments: list[dict[str, Any]],
    output_path: str | Path,
    normal_colour: str = "#FFFFFF",
    highlight_colour: str = "#FFFF00",
    font_size: int = 52,
    pop_scale: int = 118,
    animation_duration_ms: int = 180,
) -> Path:
    output_path = Path(output_path)

    normal_style_colour = (
        hex_to_ass_style_colour(normal_colour)
    )

    active_override_colour = (
        hex_to_ass_override_colour(
            highlight_colour
        )
    )

    header = f"""[Script Info]
Title: Dynamic Kinetic Captions
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kinetic,Arial,{font_size},{normal_style_colour},{normal_style_colour},&H00000000,&H70000000,-1,0,0,0,100,100,0,0,1,4,1,2,45,45,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines: list[str] = []

    for segment in segments:
        start_time = float(segment["start"])
        end_time = float(segment["end"])
        words = segment["text"].split()

        if not words:
            continue

        word_timings = calculate_word_timings(
            words=words,
            start_time=start_time,
            end_time=end_time,
        )

        for active_index, timing in enumerate(
            word_timings
        ):
            word_start, word_end = timing

            kinetic_text = build_kinetic_line(
                words=words,
                active_index=active_index,
                highlight_colour=(
                    active_override_colour
                ),
                pop_scale=pop_scale,
                animation_duration_ms=(
                    animation_duration_ms
                ),
            )

            dialogue_lines.append(
                "Dialogue: 0,"
                f"{format_ass_timestamp(word_start)},"
                f"{format_ass_timestamp(word_end)},"
                "Kinetic,,0,0,0,,"
                f"{kinetic_text}"
            )

    output_path.write_text(
        header + "\n".join(dialogue_lines),
        encoding="utf-8",
    )

    return output_path