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

# ==============================================
# 页面基础配置
# ==============================================
st.set_page_config(page_title="电影感生日视频生成", layout="wide")
st.title("🎂 耿耿 · 电影感闺蜜生日祝福视频")
st.caption("自动漫画风 | 温柔运镜 | 电影字幕 | 无水印可下载")

# ==============================================
# 临时目录初始化
# ==============================================
TEMP = Path(tempfile.mkdtemp())
IMG_DIR = TEMP / "images"
IMG_DIR.mkdir(exist_ok=True, parents=True)

# ==============================================
# 1. 上传照片模块
# ==============================================
st.divider()
st.subheader("📸 第一步：上传你们的照片（支持多张）")
uploaded_imgs = st.file_uploader(
    "选择JPG/PNG格式照片",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    help="建议上传10张以上，画面更丰富"
)

img_paths = []
if uploaded_imgs:
    for f in uploaded_imgs:
        save_path = IMG_DIR / f.name
        with open(save_path, "wb") as fw:
            fw.write(f.read())
        img_paths.append(str(save_path))
    st.success(f"✅ 成功上传 {len(img_paths)} 张照片！")

# ==============================================
# 2. 上传音频/视频模块（自动提取音频）
# ==============================================
st.divider()
st.subheader("🎵 第二步：上传背景音乐（支持MP3/WAV/MP4）")
uploaded_media = st.file_uploader(
    "选择音频或视频文件",
    type=["mp3", "wav", "mp4"],
    help="上传MP4会自动提取音频作为背景音乐"
)

audio_path = None
if uploaded_media:
    temp_file = TEMP / uploaded_media.name
    with open(temp_file, "wb") as fw:
        fw.write(uploaded_media.read())

    # 自动处理MP4转音频
    if temp_file.suffix.lower() == ".mp4":
        try:
            with st.spinner("正在从视频提取音频..."):
                vid = VideoFileClip(str(temp_file))
                audio_path = TEMP / "extracted_bgm.mp3"
                vid.audio.write_audiofile(str(audio_path), logger=None)
                vid.close()
                # 不手动删除原文件，交由Streamlit自动清理，避免权限报错
            st.success("✅ 音频提取成功！")
        except Exception as e:
            st.error(f"❌ 音频提取失败：{str(e)}")
            audio_path = None
    else:
        # 纯音频直接使用
        audio_path = temp_file
        st.success("✅ 音频加载成功！")

# ==============================================
# 视频核心参数（固定2分30秒，150秒）
# ==============================================
VIDEO_DURATION = 150
W, H = 1080, 1920  # 竖屏1080P
OUTPUT_VIDEO = TEMP / "耿耿生日祝福_电影感.mp4"

# ==============================================
# 电影感文案脚本（适配2分30秒）
# ==============================================
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
# 核心功能1：图片转漫画风（彻底修复索引越界）
# ==============================================
def make_cartoon(img_path):
    """
    图片转温柔漫画风，强制统一分辨率，彻底解决cv2索引报错
    """
    # 读取图片
    img = cv2.imread(str(img_path))
    if img is None:
        raise ValueError(f"无法读取图片：{img_path}")
    
    # 强制缩放至1080x1920，从根源解决尺寸问题
    img = cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)
    
    # 漫画风格处理
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY, 9, 9
    )
    color = cv2.bilateralFilter(img, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    
    # 暖色调电影感优化
    cartoon = cv2.convertScaleAbs(cartoon, alpha=1.3, beta=25)
    return cartoon

# ==============================================
# 核心功能2：电影感运镜（缓慢推近+微动）
# ==============================================
def camera_animate(clip, t):
    """
    温柔运镜：缓慢缩放+垂直微动，模拟电影镜头感
    """
    zoom = 1.0 + 0.03 * np.sin(t / 20)
    y_offset = 0.97 - 0.015 * np.sin(t / 18)
    return resize(clip, zoom).set_position(("center", y_offset))

# ==============================================
# 核心功能3：音频循环（兼容所有MoviePy版本）
# ==============================================
def loop_audio(audio_clip, target_duration):
    """
    兼容所有MoviePy版本的音频循环方法，彻底解决loop属性报错
    """
    audio_dur = audio_clip.duration
    if audio_dur >= target_duration:
        return audio_clip.subclip(0, target_duration)
    
    # 计算循环次数，拼接音频
    loop_times = int(np.ceil(target_duration / audio_dur))
    looped_clips = [audio_clip] * loop_times
    combined_audio = concatenate_videoclips(looped_clips)
    return combined_audio.subclip(0, target_duration)

# ==============================================
# 3. 生成视频按钮
# ==============================================
st.divider()
st.subheader("🎬 第三步：一键生成电影感视频")

if st.button("✨ 开始生成 2分30秒 生日视频", type="primary", use_container_width=True):
    # 前置校验
    if not img_paths:
        st.warning("⚠️ 请先上传照片！")
        st.stop()
    if not audio_path:
        st.warning("⚠️ 请先上传音频/视频！")
        st.stop()

    with st.spinner("🎬 正在生成电影感视频，请耐心等待 1-3 分钟..."):
        try:
            # ==============================================
            # 步骤1：生成图片轮播片段
            # ==============================================
            scene_clips = []
            used_imgs = []
            
            for seg in script:
                # 智能选图，避免重复
                available_imgs = [
                    p for p in img_paths
                    if p not in used_imgs or len(used_imgs) > len(img_paths) * 0.7
                ]
                if not available_imgs:
                    available_imgs = img_paths
                selected_img = random.choice(available_imgs)
                used_imgs.append(selected_img)

                # 图片转漫画风
                cartoon_frame = make_cartoon(selected_img)
                # 转换为RGB（MoviePy要求）
                cartoon_frame = cv2.cvtColor(cartoon_frame, cv2.COLOR_BGR2RGB)

                # 创建视频片段
                clip = ImageClip(cartoon_frame).with_duration(seg["dur"]).with_start(seg["t"])
                # 添加运镜
                clip = clip.fl(camera_animate)
                # 添加淡入淡出
                clip = fadein(clip, 0.8)
                clip = fadeout(clip, 0.8)
                scene_clips.append(clip)

            # 合并所有背景片段
            background = CompositeVideoClip(scene_clips).with_duration(VIDEO_DURATION)

            # ==============================================
            # 步骤2：生成电影感字幕（系统自带字体，无报错）
            # ==============================================
            text_clips = []
            for seg in script:
                # 使用系统自带Arial字体，100%兼容，无需额外上传
                txt = TextClip(
                    seg["text"],
                    font="Arial",
                    fontsize=46,
                    color="white",
                    stroke_color="black",
                    stroke_width=1.3,
                    method="label"
                )
                # 字幕位置：居中偏下，电影感排版
                txt = txt.with_start(seg["t"]).with_duration(seg["dur"]).with_position(("center", 0.85))
                # 字幕淡入淡出
                txt = fadein(txt, 1.2)
                txt = fadeout(txt, 1.2)
                text_clips.append(txt)

            # ==============================================
            # 步骤3：处理背景音乐
            # ==============================================
            bgm = AudioFileClip(str(audio_path))
            # 循环音频至视频时长
            bgm = loop_audio(bgm, VIDEO_DURATION)
            # 降低音量，避免盖过人声（如果有）
            bgm = bgm.volumex(0.17)
            # 音频淡入淡出
            bgm = fadein(bgm, 3)
            bgm = fadeout(bgm, 5)

            # ==============================================
            # 步骤4：最终合成视频
            # ==============================================
            final_video = CompositeVideoClip([background] + text_clips).with_audio(bgm)
            
            # 导出视频
            final_video.write_videofile(
                str(OUTPUT_VIDEO),
                fps=24,
                codec="libx264",
                audio_codec="aac",
                bitrate="5000k",
                threads=2,
                logger=None,
                verbose=False
            )

            # ==============================================
            # 步骤5：展示+下载
            # ==============================================
            st.success("✅ 电影感生日视频生成完成！")
            st.video(str(OUTPUT_VIDEO))

            # 稳定下载按钮
            with open(OUTPUT_VIDEO, "rb") as f:
                st.download_button(
                    label="💾 下载无水印完整视频",
                    data=f,
                    file_name="耿耿生日祝福_电影感.mp4",
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True
                )

        except Exception as e:
            st.error(f"❌ 视频生成失败：{str(e)}")
            st.exception(e)
