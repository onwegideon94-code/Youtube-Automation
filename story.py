
from pathlib import Path
import random
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioClip,
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
)

OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

# Original story templates. Edit these to create new stories.
STORIES = [
    {
        "title": "The Stranger Who Remembered Her",
        "scenes": [
            ("She thought the most beautiful love stories only happened in movies.",
             "But one rainy evening, a stranger offered her his umbrella."),
            ("They met again at the same little café the following week.",
             "He remembered her name, her favorite tea, and her quiet smile."),
            ("Months passed, and friendship slowly became something deeper.",
             "He never promised her the world. He simply showed up."),
            ("One evening, she took his hand and whispered,",
             "'I think home is no longer a place. It's wherever you are.'"),
        ],
    },
    {
        "title": "A Message at Midnight",
        "scenes": [
            ("She had almost given up on finding someone who understood her.",
             "Then a simple message arrived: 'Did you get home safely?'"),
            ("Their conversations grew longer every night.",
             "They shared old dreams, fears, laughter, and little hopes."),
            ("When they finally met, neither needed a perfect speech.",
             "A nervous smile said what words could not."),
            ("He held out his hand. She reached for it.",
             "Sometimes, a new beginning starts with one small question."),
        ],
    },
]


def make_voice(text, path):
    """Generate narration offline using an installed system voice."""
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 155)
    engine.save_to_file(text, str(path))
    engine.runAndWait()


def make_scene(line1, line2, index, total, out_path):
    """Render one vertical scene with a gradient and readable text."""
    width, height = 720, 1280
    y = np.linspace(0, 1, height)[:, None, None]
    top = np.array([29, 18, 54])[None, None, :]
    bottom = np.array([132, 47, 88])[None, None, :]
    gradient = top * (1 - y) + bottom * y
    gradient = np.repeat(gradient, width, axis=1).astype("uint8")

    image = Image.fromarray(gradient, "RGB")
    draw = ImageDraw.Draw(image)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    try:
        title_font = ImageFont.truetype(bold_path, 46)
        body_font = ImageFont.truetype(font_path, 36)
        small_font = ImageFont.truetype(font_path, 25)
    except OSError:
        title_font = body_font = small_font = ImageFont.load_default()

    draw.text((40, 55), "A LITTLE LOVE STORY", font=small_font,
              fill=(255, 205, 222))

    # A simple decorative heart, drawn using text.
    draw.text((290, 300), "♥", font=title_font, fill=(255, 180, 205))

    wrapped = textwrap.wrap(line1, width=27)
    y_text = 475
    for line in wrapped:
        box = draw.textbbox((0, 0), line, font=title_font)
        x = (width - (box[2] - box[0])) // 2
        draw.text((x, y_text), line, font=title_font, fill="white")
        y_text += 62

    wrapped2 = textwrap.wrap(line2, width=34)
    y_text += 45
    for line in wrapped2:
        box = draw.textbbox((0, 0), line, font=body_font)
        x = (width - (box[2] - box[0])) // 2
        draw.text((x, y_text), line, font=body_font,
                  fill=(255, 225, 235))
        y_text += 50

    draw.text((40, 1205), f"PART {index + 1} / {total}",
              font=small_font, fill=(255, 205, 222))
    image.save(out_path)


def main():
    story = random.choice(STORIES)
    all_lines = [line for pair in story["scenes"] for line in pair]
    narration = " ".join(all_lines)

    (OUTPUT / "script.txt").write_text(
        story["title"] + "\n\n" + narration, encoding="utf-8"
    )
    (OUTPUT / "metadata.txt").write_text(
        story["title"] + " #Shorts\n\n"
        "An original short story about connection, kindness, and love.\n"
        "#LoveStory #Romance #Shorts",
        encoding="utf-8",
    )

    voice_path = OUTPUT / "narration.wav"
    make_voice(narration, voice_path)

    audio = AudioFileClip(str(voice_path))
    scene_files = []

    try:
        for i, (line1, line2) in enumerate(story["scenes"]):
            path = OUTPUT / f"scene_{i + 1}.png"
            make_scene(line1, line2, i, len(story["scenes"]), path)
            scene_files.append(path)

        # Give each scene an equal share of the narration.
        duration = audio.duration / len(scene_files)
        clips = [
            ImageClip(str(path)).with_duration(duration)
            for path in scene_files
        ]
        video = concatenate_videoclips(clips, method="compose")
        video = video.with_audio(audio)
        video.write_videofile(
            str(OUTPUT / "review_me.mp4"),
            fps=24,
            codec="libx264",
            audio_codec="aac",
        )
        video.close()
    finally:
        audio.close()

    print("Draft ready: output/review_me.mp4")
    print("Read output/script.txt and output/metadata.txt before publishing.")


if __name__ == "__main__":
    from moviepy import ImageClip
    main()
