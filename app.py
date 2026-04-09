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

            # 创建视频片段（MoviePy 1.0.3兼容方法）
            clip = ImageClip(cartoon_frame).set_duration(seg["dur"]).set_start(seg["t"])
            # 添加运镜（原生方法，无报错）
            clip = add_camera_zoom(clip, seg["dur"])
            # 添加淡入淡出
            clip = fadein(clip, 0.8)
            clip = fadeout(clip, 0.8)
            scene_clips.append(clip)

        # 合并所有背景片段
        background = CompositeVideoClip(scene_clips).set_duration(VIDEO_DURATION)

        # ==============================================
        # 步骤2：生成电影感字幕（系统自带字体）
        # ==============================================
        text_clips = []
        for seg in script:
            # 使用系统自带Arial字体，100%兼容
            txt = TextClip(
                seg["text"],
                font="Arial",
                fontsize=46,
                color="white",
                stroke_color="black",
                stroke_width=1.3,
                method="label"
            )
            # 兼容MoviePy 1.0.3的方法
            txt = txt.set_start(seg["t"]).set_duration(seg["dur"]).set_position(("center", 0.85))
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
        # 降低音量
        bgm = bgm.volumex(0.17)
        # 音频淡入淡出
        bgm = fadein(bgm, 3)
        bgm = fadeout(bgm, 5)

        # ==============================================
        # 步骤4：最终合成视频
        # ==============================================
        final_video = CompositeVideoClip([background] + text_clips).set_audio(bgm)
        
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
        st.exception(e)为什么一直出错，修改最终版本
