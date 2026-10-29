# 自动剪辑工作台

本地运行的单视频剪辑工作台：从原片读取演员原声时间码，以正确脚本生成字幕和括号小字，叠加警示 PNG、调色并导出浏览器预览及 SRT。原始视频和模型文件不应提交到 GitHub。

## Windows 安装

1. 安装 Python 3.10 或更新版本。
2. 首次运行双击 `setup_asr.bat` 安装本地语音识别依赖。
3. 双击 `start.bat` 启动只监听本机 `127.0.0.1:8765` 的识别服务。
4. 打开 `batch-edit.html`。需要时在页面刷新。
5. 选演员原片、粘贴正确脚本，点“识别原声时间”，检查字幕时间和小字，再点页面顶部“生成视频”。

首次语音识别会下载 faster-whisper small 模型。字幕正文使用脚本，识别结果只帮助估算时间；演员口误仍保留在原声中。需要修正发音时，请替换原声或另加配音。

## 本机依赖

- Python 3.10+
- `requirements.txt` 中的 faster-whisper
- FFmpeg/FFprobe（可选，放入 PATH 后可供环境检查及参考视频拆解使用）
- 剪映（可选；当前导出预览视频和 SRT，不自动创建剪映原生草稿）

## 仓库内容

- `batch-edit.html`, `batch-edit.js`, `batch-edit.css`：单视频工作台
- `batch_edit_service.py`：本机语音识别服务
- `start.bat`, `setup_asr.bat`, `requirements.txt`：Windows 启动和安装文件
- `使用说明.md`, `skills/`：工作流说明

原片、素材库、模型缓存、`work/` 和 `final/` 输出目录由 `.gitignore` 排除。换电脑后从 GitHub 克隆源代码，再按本说明安装即可；媒体文件需要在新电脑本地重新选择。

