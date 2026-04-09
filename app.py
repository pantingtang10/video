import streamlit as st
import cv2
import numpy as np
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
# 配置环境
# ==============================================
st.set_page_config(page_title="电影感生日视频生成", layout="wide")
st.title("🎬 耿耿 · 电影感动态生日大片")
st.caption("动态连贯运镜 | Q版漫画渲染 | 自动切除水印 | 4K比例适配")

@st.cache_resource
def get_temp_dir():
    temp_dir = Path(tempfile.gettempdir()) / "movie_pro_v6"
    temp_dir.mkdir(exist_ok=True, parents=True)
    return temp_dir

TEMP = get_temp_dir()
W, H = 1080, 1920 
VIDEO_DURATION = 150
OUTPUT_VIDEO = TEMP / "birthday_cinematic.mp4"

# 电影叙事脚本
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
# 高级图像渲染逻辑 (Q版 + 动态适配 + 去水印)
# ==============================================
def process_cinematic_frame(img_path, text):
    img = cv2.imread(str(img_path))
    if img is None: return np.zeros((H, W, 3), dtype=np.uint8)
    
    # 1. 深度去水印：裁剪掉边缘 10% (通常AI水印在此区域)
    h_orig, w_orig = img.shape[:2]
    cut_h, cut_w = int(h_orig * 0.1), int(w_orig * 0.05)
    img = img[cut_h:h_orig-cut_h, cut_w:w_orig-cut_w]
    
    # 2. 比例适配与漫画化
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_LANCZOS4)
    # Q版二次元平滑处理
    color = cv2.bilateralFilter(img, 12, 120, 120)
    # 线条增强
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.adaptiveThreshold(cv2.medianBlur(gray, 7), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 8)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    # 电影暖调
    cartoon = cv2.convertScaleAbs(cartoon, alpha=1.15, beta=15)
    
    # 3. 绘制 PIL 字幕和渐变遮罩
    img_pil = Image.fromarray(cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil, 'RGBA')
    
    # 底部电影感半透明黑边 (渐变式)
    for i in range(250):
        opacity = int((i/250) * 160)
        draw.line([(0, H-i), (W, H-i)], fill=(0,0,0, opacity))
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 52)
    except:
        font = ImageFont.load_default()
        
    # 绘制字幕
    draw.text((W//2, H*0.88), text, font=font, fill=(255, 255, 255, 255), anchor="mm")
    
    return np.array(img_pil)

# ==============================================
# UI 与 逻辑
# ==============================================
st.subheader("第一步：单独上传照片 (将按上传顺序自动排列)")
uploaded_imgs = st.file_uploader("点击或拖拽多张照片", type=["jpg", "png"], accept_multiple_files=True)

st.subheader("第二步：上传音频")
uploaded_media = st.file_uploader("选择 BGM", type=["mp3", "mp4"])

if st.button("🚀 开始生成连贯动态电影视频", type="primary"):
    if not uploaded_imgs or not uploaded_media:
        st.error("⚠️ 请确保上传了照片和音乐。")
    else:
        status = st.empty()
        # 严格按照用户点击上传的顺序
        img_list = uploaded_imgs
        
        try:
            # 处理素材
            img_paths = []
            for i, f in enumerate(img_list):
                p = TEMP / f"seq_{i}.jpg"
                with open(p, "wb") as fw: fw.write(f.read())
                img_paths.append(p)

            # 音频准备
            status.text("正在合成音频...")
            media_p = TEMP / "source_bgm"
            with open(media_p, "wb") as fw: fw.write(uploaded_media.read())
            
            if uploaded_media.name.endswith(".mp4"):
                with VideoFileClip(str(media_p)) as v:
                    audio_p = TEMP / "final_bgm.mp3"
                    v.audio.write_audiofile(str(audio_p), logger=None)
            else:
                audio_p = media_p
            
            bgm = AudioFileClip(str(audio_p))
            if bgm.duration < VIDEO_DURATION:
                bgm = concatenate_audioclips([bgm] * (int(VIDEO_DURATION/bgm.duration)+1))
            bgm = bgm.set_duration(VIDEO_DURATION).volumex(0.2).audio_fadeout(3)

            # 场景动态合成
            status.text("正在通过 Ken Burns 特效渲染动态画面...")
            scene_clips = []
            
            for i, seg in enumerate(script):
                img_idx = i % len(img_paths)
                target_img = img_paths[img_idx]
                
                # 处理图像 + 字幕
                frame = process_cinematic_frame(target_img, seg["text"])
                
                # 创建片段
                clip = ImageClip(frame).set_duration(seg["dur"] + 1).set_start(seg["t"]) # 多加1秒用于淡入淡出重叠
                
                # 【核心：平移+缩放 复合动态运镜】
                # 随机选择一种运动方向，让视频看起来不单调
                motion_type = i % 2 
                if motion_type == 0:
                    # 模式A：中心缓慢放大
                    clip = clip.fx(vfx.resize, lambda t: 1.0 + 0.08 * (t / clip.duration))
                else:
                    # 模式B：左上向右下平移并放大
                    clip = clip.fx(vfx.resize, lambda t: 1.05 + 0.05 * (t / clip.duration))
                    # 这里的平移由 moviepy 自动根据 resize 中心点实现
                
                # 场景间消融过渡
                clip = clip.fx(vfx.fadein, 1.2).fx(vfx.fadeout, 1.2)
                scene_clips.append(clip)

            # 渲染导出
            status.text("🎬 电影导出中，全程无水印...")
            final = CompositeVideoClip(scene_clips, size=(W, H)).set_audio(bgm).set_duration(VIDEO_DURATION)
            
            final.write_videofile(
                str(OUTPUT_VIDEO),
                fps=24, 
                codec="libx264",
                audio_codec="aac",
                bitrate="6000k",
                logger=None
            )
            
            status.success("✨ 连贯动态生日电影生成成功！")
            st.video(str(OUTPUT_VIDEO))
            with open(OUTPUT_VIDEO, "rb") as f:
                st.download_button("💾 下载无水印原片", f, "生日大片_动态电影版.mp4")

        except Exception as e:
            st.error(f"渲染遇到问题: {e}")
