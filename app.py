import streamlit as st
import cv2
import numpy as np
import os
import random
import tempfile
from pathlib import Path
from moviepy.editor import (
    ImageClip, CompositeVideoClip, TextClip,
    AudioFileClip, VideoFileClip, concatenate_audioclips
)
import moviepy.video.fx.all as vfx

# ==============================================
# 页面基础配置
# ==============================================
st.set_page_config(page_title="电影感生日视频生成", layout="wide")
st.title("🎂 耿耿 · 电影感闺蜜生日祝福视频")
st.caption("最终修复版 | 解决了 size 属性报错与音频循环冲突")

# ==============================================
# 临时目录初始化
# ==============================================
@st.cache_resource
def get_temp_dir():
    temp_dir = Path(tempfile.gettempdir()) / "bday_v3_gen"
    temp_dir.mkdir(exist_ok=True, parents=True)
    return temp_dir

TEMP = get_temp_dir()
IMG_DIR = TEMP / "images"
IMG_DIR.mkdir(exist_ok=True, parents=True)

# 视频配置
VIDEO_DURATION = 150
W, H = 1080, 1920 
OUTPUT_VIDEO = TEMP / "final_birthday_video.mp4"

# 电影感文案脚本
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

def make_cartoon(img_path):
    img = cv2.imread(str(img_path))
    if img is None: return None
    img = cv2.resize(img, (W, H))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    cartoon = cv2.convertScaleAbs(cartoon, alpha=1.2, beta=15)
    return cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB)

# ==============================================
# UI 界面
# ==============================================
col1, col2 = st.columns(2)
with col1:
    uploaded_imgs = st.file_uploader("1. 上传你们的照片", type=["jpg", "png"], accept_multiple_files=True)
with col2:
    uploaded_media = st.file_uploader("2. 上传背景音乐 (MP3/MP4)", type=["mp3", "mp4"])

if st.button("✨ 一键生成 2分30秒 纪念视频", type="primary"):
    if not uploaded_imgs or not uploaded_media:
        st.error("⚠️ 请先上传照片和音频！")
    else:
        status = st.empty()
        progress = st.progress(0)
        
        try:
            # 1. 准备素材
            img_paths = []
            for i, f in enumerate(uploaded_imgs):
                p = IMG_DIR / f"temp_{i}.jpg"
                with open(p, "wb") as fw: fw.write(f.read())
                img_paths.append(p)

            media_p = TEMP / uploaded_media.name
            with open(media_p, "wb") as fw: fw.write(uploaded_media.read())
            
            # 2. 处理音频 (针对 1.0.3 的稳定性优化)
            status.text("正在处理音频...")
            if uploaded_media.name.lower().endswith(".mp4"):
                with VideoFileClip(str(media_p)) as v:
                    audio_p = TEMP / "extracted_audio.mp3"
                    v.audio.write_audiofile(str(audio_p), logger=None)
            else:
                audio_p = media_p

            bgm = AudioFileClip(str(audio_p))
            if bgm.duration < VIDEO_DURATION:
                # 正确的音频循环方法
                n_loops = int(np.ceil(VIDEO_DURATION / bgm.duration))
                bgm = concatenate_audioclips([bgm] * n_loops)
            bgm = bgm.set_duration(VIDEO_DURATION).volumex(0.2).audio_fadein(2).audio_fadeout(3)

            # 3. 合成场景
            status.text("正在生成动画片段 (共16个场景)...")
            scene_clips = []
            for i, seg in enumerate(script):
                img_p = random.choice(img_paths)
                frame = make_cartoon(img_p)
                
                # 兼容 1.0.3 的运镜逻辑，避免 size 报错
                clip = ImageClip(frame).set_duration(seg["dur"]).set_start(seg["t"])
                clip = clip.fx(vfx.resize, lambda t: 1.0 + 0.04 * (t / clip.duration))
                clip = clip.fx(vfx.fadein, 1.0).fx(vfx.fadeout, 1.0)
                scene_clips.append(clip)
                progress.progress(int((i+1)/len(script) * 80))

            # 4. 字幕处理
            status.text("正在合成电影感字幕...")
            text_clips = []
            try:
                for seg in script:
                    txt = TextClip(
                        seg["text"], font="Arial", fontsize=50, color='white',
                        method='caption', size=(W*0.8, None), align='Center'
                    ).set_start(seg["t"]).set_duration(seg["dur"]).set_position(('center', H*0.82))
                    text_clips.append(txt.fx(vfx.fadein, 0.5).fx(vfx.fadeout, 0.5))
            except:
                st.warning("⚠️ 环境缺少 ImageMagick，将生成无字幕版本。")

            # 5. 渲染
            status.text("🎬 正在最终渲染，请勿刷新页面...")
            final = CompositeVideoClip(scene_clips + text_clips, size=(W, H))
            final = final.set_audio(bgm).set_duration(VIDEO_DURATION)
            
            final.write_videofile(
                str(OUTPUT_VIDEO),
                fps=20, 
                codec="libx264",
                audio_codec="aac",
                threads=4,
                logger=None
            )
            
            progress.progress(100)
            status.success("✅ 视频生成成功！")
            st.video(str(OUTPUT_VIDEO))
            
            with open(OUTPUT_VIDEO, "rb") as f:
                st.download_button("💾 点击下载无水印原片", f, "耿耿生日纪念.mp4", "video/mp4")

        except Exception as e:
            st.error(f"❌ 生成失败: {str(e)}")
            st.info("建议：如果报错 'ImageMagick'，请确保你在 GitHub 仓库根目录放了 packages.txt 文件。")

# --- 代码结束，请确保下方没有任何多余文字 ---
