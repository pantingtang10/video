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
st.set_page_config(page_title="电影感生日视频", layout="wide")
st.title("🎂 耿耿 · 电影感闺蜜生日祝福")
st.caption("自动漫画风 | 运镜 | 电影字幕 | 可下载")

# ------------------------------------------------
# 临时目录
# ------------------------------------------------
TEMP = Path(tempfile.mkdtemp())
IMG_DIR = TEMP / "images"
IMG_DIR.mkdir(exist_ok=True)

# ------------------------------------------------
# 上传图片
# ------------------------------------------------
st.divider()
st.subheader("1️⃣ 上传照片")
uploaded_imgs = st.file_uploader(
    "JPG / PNG", type=["jpg", "jpeg", "png"], accept_multiple_files=True
)

img_paths = []
for f in uploaded_imgs:
    p = IMG_DIR / f.name
    with open(p, "wb") as fw:
        fw.write(f.read())
    img_paths.append(str(p))

# ------------------------------------------------
# 上传音频 / MP4自动转音频
# ------------------------------------------------
st.divider()
st.subheader("2️⃣ 上传背景音乐（支持 mp3 / mp4）")
uploaded_media = st.file_uploader("音频或视频文件", type=["mp3", "wav", "mp4"])

audio_path = None
if uploaded_media:
    temp_file = TEMP / uploaded_media.name
    with open(temp_file, "wb") as fw:
        fw.write(uploaded_media.read())

    if temp_file.suffix.lower() == ".mp4":
        vid = VideoFileClip(str(temp_file))
        audio_path = TEMP / "bgm.mp3"
        vid.audio.write_audiofile(str(audio_path))
        vid.close()
        os.remove(temp_file)
    else:
        audio_path = temp_file

# ------------------------------------------------
# 视频参数
# ------------------------------------------------
VIDEO_DURATION = 150
W, H = 1080, 1920
OUT_VIDEO = TEMP / "movie_video.mp4"

# ------------------------------------------------
# 电影感文案
# ------------------------------------------------
script = [
    {"t": 0, "dur": 6, "text": "2017年秋天，我们在渭南师范遇见"},
    {"t": 6, "dur": 6, "text": "四年时光，三餐与四季，朝夕相伴"},
    {"t": 12, "dur": 6, "text": "一起上课，一起熬夜，一起成长"},
    {"t": 18, "dur": 6, "text": "后来我们各自出发，奔赴不同的远方"},
    {"t": 24, "dur": 6, "text": "有人读研，有人工作，有人继续追梦"},
    {"t": 30, "dur": 6, "text": "研究生的路很难，但你一直很勇敢"},
    {"t": 36, "dur": 6, "text": "认真生活，认真发光，认真被爱"},
    {"t": 42, "dur": 6, "text": "西安、广西，距离很远，心却很近"},
    {"t": 48, "dur": 7, "text": "我们约好，要一起看海、看日出、看世界"},
    {"t": 55, "dur": 7, "text": "一起疯，一起闹，一起变成更好的人"},
    {"t": 62, "dur": 7, "text": "愿你永远明亮，永远自由，永远被爱包围"},
    {"t": 69, "dur": 7, "text": "愿你研途顺利，万事胜意，平安喜乐"},
    {"t": 76, "dur": 7, "text": "去更远的地方，见更亮的光"},
    {"t": 83, "dur": 9, "text": "耿耿，生日快乐。"},
    {"t": 92, "dur": 9, "text": "我们所有人，都在为你祝福。"},
    {"t": 101, "dur": 49, "text": "生日快乐 · 前程似锦 · 我们永远都在"},
]

# ------------------------------------------------
# 图片 → 漫画温柔风
# ------------------------------------------------
def make_cartoon(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (W, H))

    # 去水印（角落模糊）
    h, w = img.shape[:2]
    img[h-150:, w-250:] = cv2.GaussianBlur(img[h-150:, w-250:], (30,30), 40)
    img[h-150:, :250] = cv2.GaussianBlur(img[h-150:, :250], (30,30), 40)

    # 漫画效果
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)

    # 暖色调电影感
    cartoon = cv2.convertScaleAbs(cartoon, alpha=1.3, beta=25)
    return cartoon

# ------------------------------------------------
# 电影运镜：缓慢推近 + 微动
# ------------------------------------------------
def camera_move(clip, t):
    zoom = 1.0 + 0.03 * np.sin(t / 20)
    y_off = 0.97 - 0.015 * np.sin(t / 18)
    return resize(clip, zoom).set_position(("center", y_off))

# ------------------------------------------------
# 音频循环（不报错版本）
# ------------------------------------------------
def loop_music(audio_clip, target_duration):
    dur = audio_clip.duration
    if dur >= target_duration:
        return audio_clip.subclip(0, target_duration)
    loops = int(target_duration / dur) + 1
    combined = concatenate_videoclips([audio_clip] * loops)
    return combined.subclip(0, target_duration)

# ------------------------------------------------
# 生成视频
# ------------------------------------------------
st.divider()
st.subheader("3️⃣ 生成电影感视频")

if st.button("✨ 开始生成"):
    if not img_paths:
        st.warning("请先上传照片")
        st.stop()
    if not audio_path:
        st.warning("请上传音频/视频")
        st.stop()

    with st.spinner("正在生成电影感视频... 1–2分钟"):
        # 图片轮播
        scenes = []
        used = []
        for seg in script:
            avail = [p for p in img_paths if p not in used or len(used) > len(img_paths)*0.7]
            pick = random.choice(avail if avail else img_paths)
            used.append(pick)

            frame = make_cartoon(pick)
            c = ImageClip(frame).with_duration(seg["dur"]).with_start(seg["t"])
            c = c.fl(camera_move)
            c = fadein(c, 0.8)
            c = fadeout(c, 0.8)
            scenes.append(c)

        bg = CompositeVideoClip(scenes).with_duration(VIDEO_DURATION)

        # ------------------------------
        # 电影字幕（自带字体，不报错）
        # ------------------------------
        text_clips = []
        for seg in script:
            txt = TextClip(
                seg["text"],
                font="Arial",
                fontsize=46,
                color="white",
                stroke_color="black",
                stroke_width=1.3
            )
            txt = txt.with_start(seg["t"]).with_duration(seg["dur"]).with_position(("center", 0.85))
            txt = fadein(txt, 1.2)
            txt = fadeout(txt, 1.2)
            text_clips.append(txt)

        # 音频
        bgm = AudioFileClip(str(audio_path))
        bgm = loop_music(bgm, VIDEO_DURATION)
        bgm = bgm.volumex(0.17)
        bgm = fadein(bgm, 3)
        bgm = fadeout(bgm, 5)

        # 合成
        final = CompositeVideoClip([bg] + text_clips).with_audio(bgm)
        final.write_videofile(
            str(OUT_VIDEO),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            bitrate="5000k",
            threads=2
        )

        st.success("✅ 电影感视频完成！")
        st.video(str(OUT_VIDEO))

        # 下载
        with open(OUT_VIDEO, "rb") as f:
            st.download_button(
                "💾 下载无水印视频",
                data=f,
                file_name="耿耿生日祝福_电影感.mp4",
                mime="video/mp4"
            )
