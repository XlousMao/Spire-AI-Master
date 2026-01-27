# 项目结构说明 (Project Structure)

## 目录概览

```
Spire-AI-Master/
├── external/           # 第三方开源库 (需手动 Clone)
├── src/                # 核心源代码
│   ├── agents/         # [Python] AI 代理逻辑 (大脑)
│   ├── connector/      # [Python] 游戏通信层 (适配器)
│   ├── core/           # [Python] 核心数据结构与状态管理
│   ├── ui/             # [Python] PySide6 用户界面 (原 C++ 方案已废弃)
│   └── utils/          # [Python] 通用工具函数
├── docs/               # 项目文档
├── tests/              # 测试用例
├── scripts/            # 启动脚本
├── requirements.txt    # Python 依赖列表
└── main.py             # Python 服务入口 (AI Engine)
```

## 详细说明

### 1. external/ (第三方库)
这里存放需要修改源码或作为子模块引用的第三方项目。

**必须 (基础通信):**
*   **SpireComm**: 负责与 Slay the Spire 游戏进程通信 (Java <-> Python Stdin/Stdout)。
    *   本项目采用 **Vendoring** 方式（直接包含源码）而非 Git Submodule，以避免版本控制问题。

**参考库:**
*   **BottledAI**: 启发式算法参考 (Java项目)。

### 2. src/ (源代码)

本项目目前采用 **全 Python 架构** (Backend + Frontend)。

#### Python AI Engine (Backend)
*   **`main.py`**: 启动 Python 后端服务。
*   **`connector/`**: 
    *   `GameBridge`: 核心桥接类，继承自 SpireComm 的 `Coordinator`。
    *   职责：通过 Stdin/Stdout 接收 CommunicationMod 发来的游戏状态 -> 调用 AI 评分 -> 将结果通过 TCP Socket (Port 9999) 广播给 UI。
*   **`agents/`**: 
    *   目前实现为简单的规则引擎 (Rule-Based)，位于 `GameBridge.calculate_recommendation` 中。
    *   未来将扩展为独立的 Agent 类。

#### Python UI Overlay (Frontend)
*   **`ui/overlay_ui.py`**: 基于 PySide6 的透明置顶窗口。
    *   **DataReceiver**: 独立线程，连接 TCP 9999 端口接收后端数据。
    *   **OverlayWindow**: 无边框、半透明、鼠标穿透（可选）的悬浮窗，绘制在游戏窗口之上。
    *   **CardItemWidget**: 显示单张卡牌的推荐分数和理由。

### 3. 环境配置

#### Python 环境
```bash
pip install -r requirements.txt
```
主要依赖：
*   `pyside6`: UI 框架
*   `spirecomm`: 游戏通信 (需确保 `external/spirecomm` 在 PYTHONPATH 中)

---

## 架构演进记录

1.  **Phase 1 (Initial)**: 尝试 Python 后端 + C++ Qt 前端。
    *   *变更*: 由于跨语言联调复杂且 PySide6 功能已足够强大，放弃 C++ 前端方案，统一使用 Python。
2.  **Phase 2 (Current)**: Python 后端 (SpireComm) + Python 前端 (PySide6 Overlay)。
    *   实现了基于规则的打牌推荐。
    *   实现了斩杀识别 (Combo Lethal)。
    *   实现了自动/手动开始游戏切换。
