# Decontam 产品需求文档（MVP）

> **版本**：v0.1  
> **状态**：草案  
> **目标**：开发一款本地运行的视频去水印桌面工具

## 一、核心功能
- [ ] 支持 MP4、MOV、AVI 等常见格式
- [ ] 手动框选水印区域（矩形）
- [ ] 使用 OpenCV 或 AI 模型修复背景
- [ ] 输出无损质量视频
- [ ] 图形化界面（Tauri + React）

## 二、技术栈
- 前端：Tauri + React
- 后端：Python（通过 Tauri 调用）
- 核心算法：
  - 阶段1：FFmpeg + OpenCV（inpaint）
  - 阶段2：轻量级 U-Net 模型（ONNX 格式）
- 依赖：FFmpeg, OpenCV-Python, ONNX Runtime

## 三、MVP 路径
| 步骤 | 目标 |
|------|------|
| 1 | 实现命令行版去水印脚本（输入路径、坐标、输出路径） |
| 2 | 封装为 Python 函数，供 Tauri 调用 |
| 3 | 设计前端界面：上传、预览、框选、导出 |
| 4 | 打包为独立桌面应用（Windows） |

## 四、测试素材
- `assets/sample-watermarked.mp4`（带水印）
- `assets/sample-clean.mp4`（原始视频，用于对比）

## 五、性能要求
- GTX1060 上，1080p 视频处理速度 > 15fps
- 内存占用 < 2GB
- 模型大小 < 1GB

> ✅ 本项目遵循《YDS AI公司建设与项目实施完整方案（V1.0）》