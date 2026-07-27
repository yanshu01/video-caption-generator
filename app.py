import tempfile
from pathlib import Path

import streamlit as st

from subtitle import create_kinetic_ass_file
from transcribe import VideoTranscriber
from video_editor import burn_subtitles


st.set_page_config(
    page_title="AI Video Caption Generator",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 AI Video Caption Generator")

st.write(
    "Upload a short MP4 video and generate a new video "
    "with animated kinetic captions."
)

MAX_FILE_SIZE_MB = 50

uploaded_file = st.file_uploader(
    "Upload an MP4 video",
    type=["mp4"],
)

st.subheader("Caption Style")

colour_column_1, colour_column_2 = st.columns(2)

with colour_column_1:
    normal_colour = st.color_picker(
        "Normal caption colour",
        value="#FFFFFF",
    )

with colour_column_2:
    highlight_colour = st.color_picker(
        "Highlighted word colour",
        value="#FFFF00",
    )

font_size = st.slider(
    "Caption font size",
    min_value=12,
    max_value=45,
    value=24,
    step=1,
)

st.subheader("Caption Animation")

pop_scale = st.slider(
    "Active word zoom",
    min_value=105,
    max_value=140,
    value=118,
    step=1,
)

animation_duration = st.slider(
    "Pop animation duration",
    min_value=80,
    max_value=350,
    value=180,
    step=10,
)

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(
            f"Maximum file size is {MAX_FILE_SIZE_MB} MB."
        )
        st.stop()

    st.video(uploaded_file)

    if st.button(
        "Generate Captions",
        type="primary",
        use_container_width=True,
    ):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                input_video_path = (
                    temp_path / "input_video.mp4"
                )

                subtitle_path = (
                    temp_path / "captions.ass"
                )

                output_video_path = (
                    temp_path / "captioned_video.mp4"
                )

                input_video_path.write_bytes(
                    uploaded_file.getbuffer()
                )

                with st.spinner(
                    "Transcribing the video..."
                ):
                    transcriber = VideoTranscriber(
                        model_size="medium"
                    )

                    segments, language = (
                        transcriber.transcribe(
                            input_video_path
                        )
                    )

                if not segments:
                    st.error(
                        "No speech was detected in the video."
                    )
                    st.stop()

                create_kinetic_ass_file(
                    segments=segments,
                    output_path=subtitle_path,
                    normal_colour=normal_colour,
                    highlight_colour=highlight_colour,
                    font_size=font_size,
                    pop_scale=pop_scale,
                    animation_duration_ms=animation_duration,
                )

                with st.spinner(
                    "Adding animated captions to the video..."
                ):
                    burn_subtitles(
                        input_video=input_video_path,
                        subtitle_file=subtitle_path,
                        output_video=output_video_path,
                    )

                output_video_bytes = (
                    output_video_path.read_bytes()
                )

                subtitle_bytes = (
                    subtitle_path.read_bytes()
                )

                st.success(
                    "Captions generated successfully. "
                    f"Detected language: {language}"
                )

                st.video(output_video_bytes)

                st.download_button(
                    label="Download Captioned Video",
                    data=output_video_bytes,
                    file_name="captioned_video.mp4",
                    mime="video/mp4",
                    use_container_width=True,
                )

                st.download_button(
                    label="Download ASS Subtitle File",
                    data=subtitle_bytes,
                    file_name="captions.ass",
                    mime="text/plain",
                    use_container_width=True,
                )

                with st.expander(
                    "View generated captions"
                ):
                    for segment in segments:
                        start_time = segment["start"]
                        end_time = segment["end"]
                        caption_text = segment["text"]

                        st.write(
                            f"[{start_time:.2f}s - "
                            f"{end_time:.2f}s] "
                            f"{caption_text}"
                        )

        except FileNotFoundError:
            st.error(
                "FFmpeg was not found. Install it using: "
                "`brew install ffmpeg`"
            )

        except Exception as error:
            st.error(
                f"Processing failed: {error}"
            )