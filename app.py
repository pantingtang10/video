import streamlit as st
import cv2
import numpy as np
import os
import random
from moviepy.editor import (
    ImageClip, CompositeVideoClip, TextClip, AudioFileClip
)
# 注意：v1.0.3 常用这种导入方式
from moviepy.video.fx.all import fadein, fadeout, resize
import tempfile
from pathlib import Path

# =================== 页面配置 ===================
st.set_page_config(page_title="耿耿生日祝福视频生成", layout="wide")
st.title("🎂 Q版漫画生日祝福视频生成器")

# =================== 临时文件夹 ===================
# 建议使用 streamlit 自己的 session_state 或固定临时路径
TEMP = Path(tempfile.gettempdir()) / "birthday_app"
TEMP.mkdir(exist_ok=True)
IMAGE_FOLDER = TEMP / "images"
IMAGE_FOLDER.mkdir(exist_ok=True)

# =================== 上传文件 ===================
st.subheader("1️⃣ 上传资源")
col1, col2 = st.columns(2)
with col1:
    uploaded_imgs = st.file_uploader("上传照片 (JPG/PNG)", type=["jpg","jpeg","png"], accept_multiple_files=True)
with col2:
    uploaded_audio = st.file_uploader("上传背景音乐 (MP3)", type=["mp3","wav"])

# =================== 视频参数 ===================
VIDEO_DURATION = 140 # 脚本总长约 128s+12s
W, H = 720, 1280 # 建议 720p 提高云端生成速度

# 脚本内容保持不变...
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
    {"time": 128, "dur": 12, "text": "生日快乐 ✨ 前程似锦 ✨ 未来可期"},
]

def process_image(img_path):
    img = cv2.imread(img_path)
    img = cv2.resize(img, (W, H))
    
    # 卡通化处理...
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img, 9, 250, 250)
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    
    # 关键点：OpenCV 是 BGR，MoviePy 需要 RGB
    cartoon_rgb = cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB)
    return cartoon_rgb

# 生成按钮逻辑
if st.button("✨ 开始生成视频"):
    if not uploaded_imgs or not uploaded_audio:
        st.error("请先上传照片和音乐！")
    else:
        with st.spinner("正在努力渲染视频，约需 1-2 分钟..."):
            try:
                # 处理图片路径
                img_paths = []
                for f in uploaded_imgs:
                    p = IMAGE_FOLDER / f.name
                    with open(p, "wb") as fw: fw.write(f.read())
                    img_paths.append(str(p))

                audio_p = TEMP / "bgm.mp3"
                with open(audio_p, "wb") as fw: fw.write(uploaded_audio.read())

                scene_clips = []
                for i, seg in enumerate(script):
                    pick = random.choice(img_paths)
                    img_array = process_image(pick)
                    
                    # 使用 1.0.3 语法：set_duration, set_start
                    clip = ImageClip(img_array).set_duration(seg["dur"]).set_start(seg["time"])
                    clip = clip.set_position(('center', 'center'))
                    clip = fadein(clip, 1).fadeout(1)
                    scene_clips.append(clip)

                video = CompositeVideoClip(scene_clips, size=(W, H))

                # 字幕处理 (注意：Linux 环境 SimHei 可能会失效，建议上传一个 ttf 字体文件到 GitHub)
                text_clips = []
                for seg in script:
                    txt = TextClip(
                        seg["text"],
                        fontsize=45,
                        color='white',
                        font='DejaVu-Sans-Bold', # 使用 Linux 通用字体防止报错
                        stroke_color='black',
                        stroke_width=1
                    ).set_start(seg["time"]).set_duration(seg["dur"]).set_position(('center', 0.8))
                    text_clips.append(txt)

                final_video = CompositeVideoClip([video] + text_clips)
                
                audio = AudioFileClip(str(audio_p)).set_duration(final_video.duration)
                final_video = final_video.set_audio(audio)

                out_path = str(TEMP / "output.mp4")
                # 使用 libx264 编码以确保浏览器兼容
                final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")

                st.success("视频生成成功！")
                with open(out_path, "rb") as f:
                    st.download_button("📥 下载祝福视频", f, "birthday_video.mp4")
                st.video(out_path)

            except Exception as e:
                st.error(f"生成失败: {e}")
