import sys
import io
import os

# 将项目根目录添加到 sys.path
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# 强制标准输出使用 UTF-8，防止在 Windows 控制台中出现编码错误
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 将 external 目录添加到路径，以便导入其中的库
# 必须在导入 spirecomm 之前执行
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'external', 'spirecomm'))

from spirecomm.communication.coordinator import Coordinator
from src.connector.game_bridge import GameBridge

def main():
    print("Spire AI Master is starting...", file=sys.stderr)
    
    # 1. 初始化我们的 Bridge Agent
    # 它会自动启动 Socket Server 监听 9999 端口
    agent = GameBridge()
    
    # 2. 初始化 SpireComm 的协调器
    # Coordinator 负责从 stdin 读取游戏发来的 JSON，并写入 stdout
    coordinator = Coordinator()
    
    # 3. 注册我们的 Agent
    # 当游戏状态更新时，coordinator 会调用 agent.get_next_action_in_game()
    coordinator.signal_ready()
    coordinator.register_command_error_callback(agent.handle_error)
    coordinator.register_state_change_callback(agent.get_next_action_in_game)
    coordinator.register_out_of_game_callback(agent.get_next_action_out_of_game)

    # 4. 阻塞运行
    # 使用 coordinator.run() 来维持主循环，它会正确处理 stdin/stdout
    print("Agent is ready and listening on port 9999 for UI connections...", file=sys.stderr)
    try:
        coordinator.run()
    except Exception as e:
        print(f"CRITICAL ERROR in Coordinator: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR in main: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
