import streamlit as st
import cv2
import numpy as np
import os
import random
from moviepy.editor import (
    ImageClip, CompositeVideoClip, TextClip,
    AudioFileClip
)
from moviepy.video.fx.all import fadein, fadeout, resize
import tempfile
from pathlib import Path

# =================== 页面配置 ===================
st.set_page_config(page_title="耿耿生日祝福视频生成", layout="wide")
st.title("🎂 5分钟 Q版漫画生日祝福视频生成器")
st.subheader("适配：渭南师范 · 四人闺蜜 · 研究生 · 青春回忆")

# =================== 临时文件夹 ===================
TEMP = Path(tempfile.mkdtemp())
IMAGE_FOLDER = TEMP / "images"
IMAGE_FOLDER.mkdir(exist_ok=True)

# =================== 上传图片 ===================
st.divider()
st.subheader("1️⃣ 上传你们的照片（可多张）")
uploaded_imgs = st.file_uploader("上传JPG/PNG", type=["jpg","jpeg","png"], accept_multiple_files=True)

img_paths = []
for f in uploaded_imgs:
    path = IMAGE_FOLDER / f.name
    with open(path, "wb") as fw:
        fw.write(f.read())
    img_paths.append(str(path))

# =================== 上传音乐 ===================
st.divider()
st.subheader("2️⃣ 上传背景音乐（mp3）")
uploaded_audio = st.file_uploader("上传音频", type=["mp3","wav","m4a"])
audio_path = None
if uploaded_audio:
    audio_path = TEMP / "bgm.mp3"
    with open(audio_path, "wb") as fw:
        fw.write(uploaded_audio.read())

# =================== 视频参数 ===================
VIDEO_DURATION = 300
W, H = 1080, 1920
OUTPUT_PATH = TEMP / "birthday_video.mp4"

# =================== 剧情脚本 ===================
script = [
    {"time": 0, "dur": 6, "text": "2017年9月｜渭南师范学院\n我们第一次相遇"},
    {"time": 6, "dur": 6, "text": "四年同窗，三餐四季，朝夕相伴"},
    {"time": 12, "dur": 6, "text": "一起上课，一起熬夜，一起成长"},
    {"time": 18, "dur": 6, "text": "从渭师出发，各自奔赴远方"},
    {"time": 24, "dur": 7, "text": "步入研究生生涯，继续闪闪发光"},
    {"time": 31, "dur": 7, "text": "求学之路虽难，你始终勇敢坚定"},
    {"time": 38, "dur": 7, "text": "认真生活，认真热爱，认真被爱"},
    {"time": 45, "dur": 7, "text": "即使相隔千里，我们从未走远"},
    {"time": 52, "dur": 7, "text": "西安、广西、各地求学与工作"},
    {"time": 59, "dur": 7, "text": "心在一起，就是最好的我们"},
    {"time": 66, "dur": 8, "text": "未来一起看海、爬山、看日出日落"},
    {"time": 74, "dur": 8, "text": "一起疯，一起闹，一起变成更好的人"},
    {"time": 82, "dur": 8, "text": "愿你永远明亮，永远自由，永远被爱"},
    {"time": 90, "dur": 8, "text": "愿你研途顺利，万事胜意，平安喜乐"},
    {"time": 98, "dur": 8, "text": "去更远的地方，见更亮的光"},
    {"time": 106, "dur": 10, "text": "耿耿，生日快乐！🎂"},
    {"time": 116, "dur": 12, "text": "我们所有人祝你：越来越好！"},
    {"time": 128, "dur": 172, "text": "生日快乐 ✨ 前程似锦 ✨ 未来可期"},
]

# =================== 图像处理：去水印 + Q版 ===================
def process_image(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (W, H))

    # 去水印：模糊角落
    h, w = img.shape[:2]
    img[h-120:, w-180:] = cv2.GaussianBlur(img[h-120:, w-180:], (25,25), 30)
    img[h-120:, :180] = cv2.GaussianBlur(img[h-120:, :180], (25,25), 30)

    # 卡通化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)

    cartoon = cv2.convertScaleAbs(cartoon, alpha=1.3, beta=20)
    return cartoon

# =================== 运镜动画 ===================
def animate_zoom(clip, t):
    zoom = 1.0 + 0.04 * np.sin(t / 20)
    y_pos = 0.97 - 0.015 * np.sin(t / 16)
    return resize(clip, zoom).set_position(("center", y_pos))

# =================== 生成按钮 ===================
st.divider()
st.subheader("3️⃣ 开始生成视频")

if st.button("✨ 生成 5 分钟生日祝福视频"):
    if not img_paths:
        st.warning("请先上传照片！")
        st.stop()
    if not audio_path:
        st.warning("请先上传音乐！")
        st.stop()

    with st.spinner("正在生成视频，请稍等 30 秒～2 分钟"):
        # 场景片段
        scene_clips = []
        used = []
        for seg in script:
            avail = [p for p in img_paths if p not in used or len(used) > len(img_paths)*0.7]
            pick = random.choice(avail if avail else img_paths)
            used.append(pick)

            img = process_image(pick)
            clip = ImageClip(img).with_duration(seg["dur"]).with_start(seg["time"])
            clip = clip.fl(animate_zoom)
            clip = fadein(clip, 1)
            clip = fadeout(clip, 1)
            scene_clips.append(clip)

        bg = CompositeVideoClip(scene_clips).with_duration(VIDEO_DURATION)

        # 字幕
        text_clips = []
        for seg in script:
            txt = TextClip(
                seg["text"],
                font="SimHei",
                fontsize=52,
                color="white",
                stroke_color="black",
                stroke_width=1.5
            ).with_start(seg["time"]).with_duration(seg["dur"]).with_position(("center", 0.82))
            txt = fadein(txt, 1.2)
            txt = fadeout(txt, 1.2)
            text_clips.append(txt)

        # 音频
        audio = AudioFileClip(str(audio_path)).with_duration(VIDEO_DURATION)
        audio = audio.volumex(0.18)
        audio = fadein(audio, 3)
        audio = fadeout(audio, 6)
