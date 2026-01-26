# 问题追踪与解决方案记录 (Bug Tracker)

本文档记录了项目开发过程中遇到的关键技术问题及其解决方案，供后续维护参考。

## 1. 编码问题 (Encoding Issue)
*   **现象**: 在 Windows 控制台 (PowerShell/CMD) 中运行 Python 脚本时，输出中文乱码或报错 `UnicodeEncodeError`。
*   **原因**: Windows 控制台默认编码可能是 GBK，而 Python 3 在某些环境下的 `sys.stdout` 默认编码不一致。
*   **解决**: 在 `main.py` 头部强制指定标准输出编码为 UTF-8：
    ```python
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    ```

## 2. 进程死锁 (Deadlock / Stdin Preemption)
*   **现象**: 后端启动后无响应，无法接收游戏数据。
*   **原因**: `main.py` 中写了一个 `while True` 循环手动调用 `coordinator.receive_game_state_update()`，但 `Coordinator` 内部已经开启了独立线程读取 `stdin`。两个读取操作发生了冲突（资源抢占），或者主线程死循环阻塞了回调执行。
*   **解决**: 移除主线程的手动循环，直接调用 `coordinator.run()`，它内部实现了优雅的阻塞和线程协调。

## 3. 协议字段缺失 (Protocol Mismatch)
*   **现象**: 使用 `mock_game_feed.py` 测试时，`GameBridge` 无法接收到动作更新。
*   **原因**: `mock_game_feed.py` 发送的 JSON 数据缺少 `in_game` 和 `ready_for_command` 字段。`Coordinator` 依赖这些字段判断是否触发回调。
*   **解决**: 补全 Mock 数据的 JSON 结构，使其符合 SpireComm 协议规范。

## 4. UI 异常吞没 (Silent UI Crash)
*   **现象**: 运行 `overlay_ui.py` 时，窗口一闪而过，没有任何报错信息。
*   **原因**: PySide6 应用程序在主事件循环前的错误往往不会打印到控制台，或者被系统直接终止。
*   **解决**: 添加全局异常捕获 (`try...except`)，并将错误堆栈打印到 `sys.stderr`，同时在出错时通过 `input()` 暂停程序以查看日志。

## 5. 端口混淆 (Port Confusion)
*   **现象**: 用户困惑为何有两个端口 (8493 和 9999)。
*   **解释**:
    *   **Port 8493**: 是 **CommunicationMod** 默认使用的 TCP 端口（如果它配置为 Socket 模式）。但在本项目中，我们通过标准输入输出 (Stdin/Stdout) 与游戏通信，不使用此端口。
    *   **Port 9999**: 是我们自定义的 **Socket Server** 端口，用于 Python 后端 (`main.py`) 与 Python 前端 (`overlay_ui.py`) 之间传输数据。

## 6. 自动开始游戏问题 (Auto-Start)
*   **现象**: 后端启动后会自动选择角色并开始游戏，导致停在第0层。
*   **原因**: `SimpleAgent` 默认的 `get_next_action_out_of_game` 方法会返回 `StartGameAction`。
*   **解决**: 在 `GameBridge` 中重写该方法，增加 `auto_start` 开关。当开关关闭时，返回 `NullAction` (不做任何操作)，等待用户手动开始。
