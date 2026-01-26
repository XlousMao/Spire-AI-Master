# Spire AI Master 项目总结文档

## 1. 项目概述
本项目是一个针对《杀戮尖塔》(Slay the Spire) 的 AI 辅助决策工具。旨在通过实时分析游戏状态，为玩家提供出牌建议，而不是完全接管游戏。
项目采用 **混合架构**：
- **后端 (Python)**: 负责与游戏通信、解析状态、执行决策逻辑。
- **前端 (PySide6)**: 提供现代化的 Overlay UI，置顶显示推荐信息。

## 2. 核心架构

### 2.1 数据流向
```mermaid
graph LR
    Game[Slay the Spire (CommunicationMod)] -- Stdout (JSON) --> Coordinator[SpireComm Coordinator]
    Coordinator -- Update --> Agent[GameBridge Agent]
    Agent -- Logic --> Recommender[Recommendation Engine]
    Agent -- Socket (TCP 9999) --> UI[Overlay UI (PySide6)]
```

### 2.2 关键组件
*   **CommunicationMod**: 游戏内的 Java Mod，负责将游戏状态通过标准输出 (Stdout) 发送给外部程序，并从标准输入 (Stdin) 接收指令。
*   **SpireComm (External Lib)**: Python 库，封装了与 CommunicationMod 的通信协议。
*   **GameBridge (`src/connector/game_bridge.py`)**:
    *   继承自 `SimpleAgent`。
    *   **职责**: 接收游戏状态，运行推荐算法，通过 Socket 广播数据。
    *   **特性**: 支持“观察模式”（不发送指令），支持自动打牌暂停。
*   **Overlay UI (`src/ui/overlay_ui.py`)**:
    *   基于 PySide6。
    *   **特性**: 无边框、半透明、置顶、实时刷新。
    *   **交互**: 接收 TCP 9999 端口的 JSON 数据并渲染列表。

## 3. 核心功能

### 3.1 推荐引擎 (Heuristic Engine)
位于 `GameBridge.calculate_recommendation`，参考了 Bottled AI 的逻辑：
1.  **斩杀优先 (Lethal)**: 如果能击杀敌人，攻击牌评分极高。
2.  **AOE 识别**: 面对多个敌人时，AOE 卡牌（如 Whirlwind）评分大幅提升。
3.  **力量成长 (Strength Scaling)**: 拥有力量 Buff 时，多段攻击牌（如 Twin Strike）评分提升。
4.  **智能防御**:
    *   如果敌人意图是攻击且玩家有生命危险 -> 防御牌评分极高。
    *   如果敌人不攻击 (Buff/Debuff) -> 防御牌评分归零。

### 3.2 两种模式
*   **辅助模式 (默认)**: `auto_play = False`, `auto_start = False`。AI 只分析不操作，玩家手动打牌。
*   **自动模式**: 可通过代码开关开启。AI 自动接管游戏。

## 4. 运行指南

### 前置条件
1.  安装 Python 3.10+。
2.  安装依赖: `pip install PySide6`。
3.  游戏内安装 **CommunicationMod** 并配置为启动 `start.bat` 或手动启动。

### 启动步骤
1.  **启动游戏**: 打开 Slay the Spire。
2.  **启动后端**:
    ```bash
    python src/main.py
    ```
    *注意：后端会等待游戏连接。*
3.  **启动 UI**:
    ```bash
    python src/ui/overlay_ui.py
    ```
    *UI 会自动连接到后端的 9999 端口。*

## 5. 目录结构
```
Spire-AI-Master/
├── external/           # 外部依赖 (spirecomm)
├── src/
│   ├── connector/      # 核心逻辑 (GameBridge)
│   ├── ui/             # 前端界面 (Overlay UI)
│   └── main.py         # 后端入口
├── tests/              # 测试脚本 (Mock Data)
└── docs/               # 文档
```
