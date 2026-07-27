import subprocess
from pathlib import Path


def burn_subtitles(
    input_video: str | Path,
    subtitle_file: str | Path,
    output_video: str | Path,
) -> Path:
    input_video = Path(input_video).resolve()
    subtitle_file = Path(subtitle_file).resolve()
    output_video = Path(output_video).resolve()

    working_directory = subtitle_file.parent

    subtitle_filter = (
        f"ass={subtitle_file.name}"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-vf",
        subtitle_filter,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(output_video),
    ]

    process = subprocess.run(
        command,
        cwd=working_directory,
        capture_output=True,
        text=True,
    )

    if process.returncode != 0:
        raise RuntimeError(
            "FFmpeg processing failed:\n"
            f"{process.stderr}"
        )

    return output_video