import streamlit as st
import cv2
import numpy as np
import os
import random
import tempfile
from pathlib import Path
from moviepy.editor import (
    ImageClip, CompositeVideoClip, 
    AudioFileClip, VideoFileClip, concatenate_audioclips
)
import moviepy.video.fx.all as vfx
from PIL import Image, ImageDraw, ImageFont

# ==============================================
# 页面配置
# ==============================================
st.set_page_config(page_title="电影感生日视频生成", layout="wide")
st.title("🎂 最终增强版 · 免 ImageMagick 渲染")
st.caption("采用 PIL 绘图引擎渲染字幕 | 彻底解决环境报错问题")

# 目录初始化
@st.cache_resource
def get_temp_dir():
    temp_dir = Path(tempfile.gettempdir()) / "bday_v4_final"
    temp_dir.mkdir(exist_ok=True, parents=True)
    return temp_dir

TEMP = get_temp_dir()
IMG_DIR = TEMP / "images"
IMG_DIR.mkdir(exist_ok=True, parents=True)

W, H = 1080, 1920 
VIDEO_DURATION = 150
OUTPUT_VIDEO = TEMP / "birthday_movie_final.mp4"

# 脚本配置
script = [
    {"t": 0, "dur": 6, "text": "2017年秋天，我们相遇"},
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

# ==============================================
# 核心渲染函数：漫画化 + 绘制电影字幕
# ==============================================
def process_frame_with_text(img_path, text):
    # 1. 漫画化处理
    img = cv2.imread(str(img_path))
    img = cv2.resize(img, (W, H))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    cartoon = cv2.convertScaleAbs(cartoon, alpha=1.1, beta=20)
    
    # 2. 使用 PIL 绘制高质量中文字幕 (替代 TextClip)
    # 将 OpenCV 图像转为 PIL 图像
    img_pil = Image.fromarray(cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    # 尝试加载字体 (Streamlit服务器一般自带简黑)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 45)
    except:
        font = ImageFont.load_default()
    
    # 绘制半透明黑边背景 (电影感)
    text_y = int(H * 0.85)
    # 粗略计算文字位置
    draw.text((W//2, text_y), text, font=font, fill=(255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(0,0,0))
    
    return np.array(img_pil)

# ==============================================
# UI
# ==============================================
uploaded_imgs = st.file_uploader("1. 上传照片", type=["jpg", "png"], accept_multiple_files=True)
uploaded_media = st.file_uploader("2. 上传音乐 (MP3/MP4)", type=["mp3", "mp4"])

if st.button("🚀 强制绕过环境限制，开始合成"):
    if not uploaded_imgs or not uploaded_media:
        st.error("素材不全！")
    else:
        status = st.empty()
        
        try:
            # 准备素材
            img_paths = [IMG_DIR / f"f_{i}.jpg" for i, f in enumerate(uploaded_imgs)]
            for p, f in zip(img_paths, uploaded_imgs):
                with open(p, "wb") as fw: fw.write(f.read())
            
            media_p = TEMP / "bgm_temp"
            with open(media_p, "wb") as fw: fw.write(uploaded_media.read())
            
            # 处理音频
            status.text("处理音频中...")
            if uploaded_media.name.lower().endswith(".mp4"):
                with VideoFileClip(str(media_p)) as v:
                    audio_p = TEMP / "ext.mp3"
                    v.audio.write_audiofile(str(audio_p), logger=None)
            else:
                audio_p = media_p
            
            bgm = AudioFileClip(str(audio_p))
            if bgm.duration < VIDEO_DURATION:
                bgm = concatenate_audioclips([bgm] * int(VIDEO_DURATION/bgm.duration + 1))
            bgm = bgm.set_duration(VIDEO_DURATION).volumex(0.2).audio_fadeout(3)

            # 合成场景 (直接把文字画在帧上)
            status.text("正在渲染每一帧并添加字幕...")
            scene_clips = []
            for i, seg in enumerate(script):
                img_p = random.choice(img_paths)
                # 这一步直接完成了：漫画滤镜 + 字幕添加
                frame = process_frame_with_text(img_p, seg["text"])
                
                clip = ImageClip(frame).set_duration(seg["dur"]).set_start(seg["t"])
                # 添加运镜
                clip = clip.fx(vfx.resize, lambda t: 1.0 + 0.05 * (t / clip.duration))
                clip = clip.fx(vfx.fadein, 0.8).fx(vfx.fadeout, 0.8)
                scene_clips.append(clip)
            
            # 最终导出
            status.text("🎬 正在最后导出 (150秒视频，请耐心等待)...")
            final = CompositeVideoClip(scene_clips, size=(W, H)).set_audio(bgm).set_duration(VIDEO_DURATION)
            
            final.write_videofile(
                str(OUTPUT_VIDEO),
                fps=18,  # 稍微降低fps提高合成速度
                codec="libx264",
                audio_codec="aac",
                logger=None
            )
            
            status.success("✅ 视频已生成！")
            st.video(str(OUTPUT_VIDEO))
            with open(OUTPUT_VIDEO, "rb") as f:
                st.download_button("💾 下载视频", f, "birthday.mp4")
                
        except Exception as e:
            st.error(f"失败了: {e}")
