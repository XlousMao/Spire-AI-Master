# 项目结构说明 (Project Structure)

## 目录概览

```
Spire-AI-Master/
├── external/           # 第三方开源库 (需手动 Clone)
├── src/                # 核心源代码
│   ├── agents/         # [Python] AI 代理逻辑 (大脑)
│   ├── connector/      # [Python] 游戏通信层 (适配器)
│   ├── core/           # [Python] 核心数据结构与状态管理
│   ├── ui/             # [C++] Qt6 用户界面工程
│   └── utils/          # [Python] 通用工具函数
├── docs/               # 项目文档
├── tests/              # 测试用例
├── scripts/            # 启动脚本
├── requirements.txt    # Python 依赖列表
└── main.py             # Python 服务入口 (AI Engine)
```

## 详细说明

### 1. external/ (第三方库)
这里存放需要修改源码或作为子模块引用的第三方项目。请在此目录下运行以下命令来获取必要的依赖：

**必须 (基础通信):**
```bash
# SpireComm: 负责与 Slay the Spire 游戏进程通信 (Java <-> Python)
cd external
git clone git@github.com:ForgottenArbiter/spirecomm.git
```

**可选 (参考逻辑/模型):**
```bash
# BottledAI: 启发式算法参考 (Java项目，主要看逻辑)
git clone https://github.com/BoardEngineer/BottledAI.git

# SLAI-the-Spire: 深度强化学习模型参考
git clone https://github.com/upper-institute/slai-the-spire.git
```

### 2. src/ (源代码)

由于采用了 **Python AI 后端 + C++ Qt 前端** 的架构，代码分为两部分：

#### Python 部分 (AI Engine)
*   **`connector/`**: 负责与 `spirecomm` 对接，同时作为 Socket Server 与 C++ UI 通信。
    *   目标: 接收游戏状态 -> 清洗数据 -> 发送给 UI。
*   **`core/`**: 定义 Python 侧的数据结构。
*   **`agents/`**: AI 决策逻辑 (RuleBased / DQN)。
*   **`main.py`**: 启动 Python 后端服务。

#### C++ 部分 (UI Frontend)
*   **`ui/`**: 独立的 CMake/QMake 工程。
    *   包含 `CMakeLists.txt` 或 `.pro` 文件。
    *   **Socket Client**: 连接 Python 后端，接收 JSON 格式的状态数据并渲染。
    *   **Overlay**: 透明置顶窗口实现。

### 3. 环境配置

#### Python 环境
```bash
pip install -r requirements.txt
```

#### C++ 环境
*   **Qt 6.x**: 请安装 Qt 6 开发环境 (建议使用 Qt Creator)。
*   **Compiler**: MSVC (Windows) 或 GCC/Clang。
*   **CMake**: 构建工具。

---

## 开发路线图 (Roadmap)

1.  **Phase 1 (本周)**:
    *   [Python] 跑通 `spirecomm`，获取游戏数据。
    *   [Python] 搭建简单的 Socket Server，广播游戏状态。
    *   [C++] 写一个简单的 Qt 窗口，连接 Socket 并显示文本信息。
2.  **Phase 2**: 实现 `RuleBasedAgent`，能自动打出费用允许的攻击牌。
3.  **Phase 3**: 完善 C++ 界面，绘制精美的卡牌建议 UI。
