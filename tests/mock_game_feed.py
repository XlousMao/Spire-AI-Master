import json
import time
import sys

def mock_game_loop():
    """
    模拟 SpireComm 发送给 Agent 的 JSON 数据流。
    用于在没有启动游戏的情况下测试 UI 和 GameBridge 逻辑。
    """
    
    # 模拟手牌数据
    mock_states = [
        {
            "in_game": True,
            "ready_for_command": True,
            "game_state": {
                "room_phase": "COMBAT",
                "room_type": "MonsterRoom",
                "turn": 1,
                "act": 1,
                "floor": 1,
                "player": {
                    "max_hp": 80,
                    "current_hp": 72,
                    "block": 0,
                    "energy": 3,
                    "orbs": []
                },
                "monsters": [
                    {
                        "name": "Cultist",
                        "max_hp": 50,
                        "current_hp": 50,
                        "block": 0,
                        "intent": "ATTACK",
                        "move_adjusted_damage": 6,
                        "move_hits": 1,
                        "is_gone": False,
                        "half_dead": False
                    }
                ],
                "hand": [
                    {"uuid": "card1", "name": "Strike_R", "cost": 1, "type": "ATTACK", "is_playable": True, "card_id": "Strike_R"},
                    {"uuid": "card2", "name": "Defend_R", "cost": 1, "type": "SKILL", "is_playable": True, "card_id": "Defend_R"},
                    {"uuid": "card3", "name": "Bash", "cost": 2, "type": "ATTACK", "is_playable": True, "card_id": "Bash"},
                    {"uuid": "card4", "name": "Strike_R", "cost": 1, "type": "ATTACK", "is_playable": True, "card_id": "Strike_R"},
                    {"uuid": "card5", "name": "Defend_R", "cost": 1, "type": "SKILL", "is_playable": True, "card_id": "Defend_R"}
                ],
                "draw_pile": [],
                "discard_pile": [],
                "exhaust_pile": [],
                "choice_available": False,
                "screen_type": "NONE"
            },
            "available_commands": ["PLAY", "END"]
        }
    ]

    print("DEBUG: Mock Game Feeder Started. Sending data in 3 seconds...", file=sys.stderr)
    time.sleep(3)

    # 发送 "ready" 信号 (SpireComm 协议可能需要，但 SimpleAgent 主要通过 input() 读取 JSON)
    # SpireComm 的 Coordinator 会先发送 "ready"
    # 注意：不要发送纯文本 "ready" 给 Coordinator，因为它期望的是 JSON！
    # 如果发送非 JSON 字符串，Coordinator 会抛出 JSONDecodeError 并导致 main.py 崩溃。
    # print("ready")
    # sys.stdout.flush()

    while True:
        for state in mock_states:
            # 必须转换成 JSON 字符串并换行
            json_line = json.dumps(state)
            print(json_line)
            sys.stdout.flush()
            print(f"DEBUG: Sent mock state to stdout", file=sys.stderr)
            time.sleep(2)

if __name__ == "__main__":
    try:
        mock_game_loop()
    except KeyboardInterrupt:
        pass
