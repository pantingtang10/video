import streamlit as st
import cv2
import numpy as np
import os
import random
from moviepy.editor import (
    ImageClip, CompositeVideoClip, TextClip, AudioFileClip, VideoFileClip
)
from moviepy.video.fx.all import fadein, fadeout, resize
import tempfile
from pathlib import Path

# =================== 页面配置 ===================
st.set_page_config(page_title="耿耿生日祝福视频生成", layout="wide")
st.title("🎂 全自动漫画版生日视频生成器")
st.info("支持上传 MP4/MP3 音乐，所有图片将自动转换为 Q 版漫画风格。")

# =================== 路径初始化 ===================
TEMP = Path(tempfile.gettempdir()) / "birthday_v2"
TEMP.mkdir(exist_ok=True)

# =================== 1️⃣ 资源上传 ===================
st.subheader("1️⃣ 上传素材")
col1, col2 = st.columns(2)

with col1:
    uploaded_imgs = st.file_uploader("上传照片 (多张)", type=["jpg","jpeg","png"], accept_multiple_files=True)

with col2:
    # 增加了 mp4 支持
    uploaded_audio_file = st.file_uploader("上传背景音乐或视频", type=["mp3","wav","mp4","m4a"])

# =================== 视频参数 ===================
W, H = 720, 1280  # 竖屏 720P，兼顾画质与生成速度
VIDEO_DURATION = 140 # 脚本总长约 140 秒

# 剧情脚本保持不变
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

# =================== 2️⃣ 漫画化处理函数 ===================
def cartoonize_image(img_stream):
    # 读取图片
    file_bytes = np.asarray(bytearray(img_stream.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, 1)
    img = cv2.resize(img, (W, H))

    # 1. 边缘检测
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)

    # 2. 双边滤波（平滑颜色，保留边缘）
    color = cv2.bilateralFilter(img, 9, 250, 250)

    # 3. 合并
    cartoon = cv2.bitwise_and(color, color, mask=edges)
    
    # 4. 增强色彩饱和度
    cartoon = cv2.convertScaleAbs(cartoon, alpha=1.2, beta=15)
    
    # 5. 转换 BGR 为 RGB (MoviePy 需要 RGB)
    return cv2.cvtColor(cartoon, cv2.COLOR_BGR2RGB)

# =================== 3️⃣ 生成逻辑 ===================
if st.button("✨ 一键生成全漫画生日视频"):
    if not uploaded_imgs:
        st.error("请至少上传一张照片！")
    elif not uploaded_audio_file:
        st.error("请上传背景音乐（MP3）或包含音频的视频（MP4）！")
    else:
        try:
            with st.spinner("第一步：正在将所有照片转换为漫画风格..."):
                cartoon_images = []
                for img_file in uploaded_imgs:
                    # 重新读取流，防止多次操作报错
                    img_file.seek(0)
                    cartoon_images.append(cartoonize_image(img_file))
                st.toast(f"成功转换 {len(cartoon_images)} 张图片！")

            with st.spinner("第二步：正在渲染 5 分钟祝福视频..."):
                # 处理音频
                audio_ext = uploaded_audio_file.name.split('.')[-1].lower()
                audio_tmp_path = str(TEMP / f"temp_audio.{audio_ext}")
                with open(audio_tmp_path, "wb") as f:
                    f.write(uploaded_audio_file.read())

                if audio_ext == "mp4":
                    audio_clip = VideoFileClip(audio_tmp_path).audio
                else:
                    audio_clip = AudioFileClip(audio_tmp_path)
                
                # 循环音频直到覆盖视频长度
                audio_clip = audio_clip.loop(duration=VIDEO_DURATION).volumex(0.3)

                # 生成场景片段
                scene_clips = []
                for i, seg in enumerate(script):
                    # 循环选取处理好的漫画图片
                    img_array = cartoon_images[i % len(cartoon_images)]
                    
                    clip = ImageClip(img_array).set_duration(seg["dur"]).set_start(seg["time"])
                    
                    # 简单的缩放运镜效果
                    clip = clip.set_position(('center', 'center'))
                    clip = fadein(clip, 1).fadeout(1)
                    scene_clips.append(clip)

                # 生成文字片段
                text_clips = []
                for seg in script:
                    txt = TextClip(
                        seg["text"],
                        fontsize=40,
                        color='white',
                        font='DejaVu-Sans-Bold', # Linux 环境默认字体
                        stroke_color='black',
                        stroke_width=1,
                        method='caption',
                        size=(W*0.8, None)
                    ).set_start(seg["time"]).set_duration(seg["dur"]).set_position(('center', 0.75))
                    text_clips.append(txt)

                # 合成最终视频
                final_video = CompositeVideoClip(scene_clips + text_clips, size=(W, H))
                final_video = final_video.set_audio(audio_clip)
                final_video = final_video.set_duration(VIDEO_DURATION)

                out_path = str(TEMP / "birthday_cartoon_final.mp4")
                final_video.write_videofile(out_path, fps=24, codec="libx264", audio_codec="aac")

                st.success("🎉 视频生成完成！")
                with open(out_path, "rb") as f:
                    st.download_button("📥 下载我的漫画版生日视频", f, "birthday_video.mp4")
                st.video(out_path)

        except Exception as e:
            st.error(f"发生错误: {str(e)}")
            st.info("提示：如果是字体报错，请在仓库上传 simhei.ttf 并修改代码中的 font 参数。")
