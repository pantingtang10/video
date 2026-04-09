import streamlit as st
import cv2
import numpy as np
import os
import random
from moviepy.editor import (
    ImageClip, CompositeVideoClip, TextClip,
    AudioFileClip, VideoFileClip, concatenate_videoclips
)
from moviepy.video.fx.all import fadein, fadeout, resize
import tempfile
from pathlib import Path

# ------------------------------------------------
# 页面配置
# ------------------------------------------------
st.set_page_config(page_title="生日祝福视频生成", layout="wide")
st.title("🎂 耿耿 · 闺蜜青春生日视频（2分30秒）")
st.caption("自动漫画风｜运镜动画｜字幕｜无水印｜可下载")

# ------------------------------------------------
# 临时文件夹
# ------------------------------------------------
TEMP = Path(tempfile.mkdtemp())
IMG_FOLDER = TEMP / "images"
IMG_FOLDER.mkdir(exist_ok=True)

# ------------------------------------------------
# 上传图片
# ------------------------------------------------
st.divider()
st.subheader("1️⃣ 上传照片（可多张）")
uploaded_imgs = st.file_uploader(
    "JPG / PNG", type=["jpg", "jpeg", "png"], accept_multiple_files=True
)

img_paths = []
for f in uploaded_imgs:
    save_path = IMG_FOLDER / f.name
    with open(save_path, "wb") as fw:
        fw.write(f.read())
    img_paths.append(str(save_path))

# ------------------------------------------------
# 上传音频 / 视频自动转音频
# ------------------------------------------------
st.divider()
st.subheader("2️⃣ 上传背景音乐（支持 mp3 / wav / mp4）")
uploaded_media = st.file_uploader("音频或视频文件", type=["mp3", "wav", "mp4"])

audio_path = None
if uploaded_media:
    temp_file = TEMP / uploaded_media.name
    with open(temp_file, "wb") as fw:
        fw.write(uploaded_media.read())

    # 如果是视频，自动提取音频
    if temp_file.suffix.lower() == ".mp4":
        vid = VideoFileClip(str(temp_file))
        audio_path = TEMP / "bgm.mp3"
        vid.audio.write_audiofile(str(audio_path))
        vid.close()
        os.remove(temp_file)
    else:
        audio_path = temp_file

# ------------------------------------------------
# 视频参数（2分30秒 = 150秒）
# ------------------------------------------------
VIDEO_DURATION = 150
W, H = 1080, 1920
OUTPUT_VIDEO = TEMP / "birthday_video.mp4"

# ------------------------------------------------
# 文案脚本（精简治愈版）
# ------------------------------------------------
script = [
    {"t": 0, "dur": 5, "text": "2017年9月｜渭南师范\n我们相遇"},
    {"t": 5, "dur": 5, "text": "四年同窗，三餐四季，朝夕相伴"},
    {"t": 10, "dur": 5, "text": "一起上课，一起熬夜，一起成长"},
    {"t": 15, "dur": 5, "text": "从渭师出发，各自奔赴远方"},
    {"t": 20, "dur": 6, "text": "如今读研、工作、散落各地"},
    {"t": 26, "dur": 6, "text": "西安、广西，距离远，心很近"},
    {"t": 32, "dur": 6, "text": "研究生的路很难，但你一直很勇敢"},
    {"t": 38, "dur": 6, "text": "认真生活，认真发光，认真被爱"},
    {"t": 44, "dur": 7, "text": "我们约好一起看海、爬山、看日出"},
    {"t": 51, "dur": 7, "text": "一起疯、一起闹、一起变好"},
    {"t": 58, "dur": 7, "text": "愿你永远明亮，永远自由，永远被爱"},
    {"t": 65, "dur": 7, "text": "愿你研途顺利，万事胜意，平安喜乐"},
    {"t": 72, "dur": 8, "text": "去更远的地方，见更亮的光"},
    {"t": 80, "dur": 10, "text": "耿耿，生日快乐！🎂"},
    {"t": 90, "dur": 10, "text": "我们所有人祝你：越来越好！"},
    {"t": 100, "dur": 50, "text": "生日快乐 ✨ 前程似锦 ✨ 我们永远在"},
]

# ------------------------------------------------
# 图片漫画化 + 去水印
# ------------------------------------------------
def make_cartoon(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (W, H))

    # 去水印（模糊角落）
    h, w = img.shape[:2]
    img[h-140:, w-220:] = cv2.GaussianBlur(img[h-140:, w-220:], (27,27), 35)
    img[h-140:, :220] = cv2.GaussianBlur(img[h-140:, :220], (27,27), 35)

    # 漫画风格
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)

    # 暖色调提亮
    cartoon = cv2.convertScaleAbs(cartoon, alpha=1.25, beta=22)
    return cartoon

# ------------------------------------------------
# 温柔运镜
# ------------------------------------------------
def animate(clip, t):
    zoom = 1.0 + 0.03 * np.sin(t / 20)
    y_pos = 0.97 - 0.012 * np.sin(t / 17)
    return resize(clip, zoom).set_position(("center", y_pos))

# ------------------------------------------------
# 音频循环（兼容所有版本）
# ------------------------------------------------
def loop_audio(clip, duration):
    d = clip.duration
    if d >= duration:
        return clip.subclip(0, duration)
    count = int(duration / d) + 1
    combined = concatenate_videoclips([clip] * count)
    return combined.subclip(0, duration)

# ------------------------------------------------
# 生成视频
# ------------------------------------------------
st.divider()
st.subheader("3️⃣ 生成视频并下载")

if st.button("✨ 生成 2分30秒 生日视频"):
    if not img_paths:
        st.warning("请先上传照片")
        st.stop()
    if not audio_path:
        st.warning("请上传音频/视频")
        st.stop()

    with st.spinner("正在生成漫画视频，请稍等..."):
        # 图片轮播片段
        scenes = []
        used = []
        for seg in script:
            available = [p for p in img_paths if p not in used or len(used) > len(img_paths)*0.7]
            pick = random.choice(available if available else img_paths)
            used.append(pick)

            img = make_cartoon(pick)
            clip = ImageClip(img).with_duration(seg["dur"]).with_start(seg["t"])
            clip = clip.fl(animate)
            clip = fadein(clip, 0.7)
            clip = fadeout(clip, 0.7)
            scenes.append(clip)

        bg_clip = CompositeVideoClip(scenes).with_duration(VIDEO_DURATION)

        # 字幕
        text_clips = []
        for seg in script:
            try:
                txt = TextClip(
                    seg["text"], font="SimHei", fontsize=48,
                    color="white", stroke_color="black", stroke_width=1.2
                )
            except:
                txt = TextClip(
                    seg["text"], fontsize=48,
                    color="white", stroke_color="black", stroke_width=1.2
                )

            txt = txt.with_start(seg["t"]).with_duration(seg["dur"]).with_position(("center", 0.82))
            txt = fadein(txt, 1)
            txt = fadeout(txt, 1)
            text_clips.append(txt)

        # 音频
        bgm = AudioFileClip(str(audio_path))
        bgm = loop_audio(bgm, VIDEO_DURATION)
        bgm = bgm.volumex(0.17)
        bgm = fadein(bgm, 2)
        bgm = fadeout(bgm, 4)

        # 最终合成
        final = CompositeVideoClip([bg_clip] + text_clips).with_audio(bgm)
        final.write_videofile(
            str(OUTPUT_VIDEO),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            bitrate="5000k",
            threads=2
        )

        st.success("✅ 视频生成完成！")
        st.video(str(OUTPUT_VIDEO))

        # ————————————————————————————
        # 稳定下载按钮（真正可下载）
        # ————————————————————————————
        with open(OUTPUT_VIDEO, "rb") as f:
            st.download_button(
                label="💾 下载无水印视频",
                data=f,
                file_name="耿耿生日祝福视频.mp4",
                mime="video/mp4"
            )
