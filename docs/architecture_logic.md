# 核心架构与算法逻辑 (Architecture & Algorithm Logic)

## 1. 系统总体架构 (System Architecture)

本系统采用 **双进程 + TCP 通信** 架构，实现了游戏逻辑与 UI 展示的解耦。

### 数据流向 (Data Flow)
```mermaid
graph LR
    A[Slay the Spire (Game)] -- Stdin/Stdout --> B[Python Backend (GameBridge)]
    B -- TCP Socket (Port 9999) --> C[Python Frontend (Overlay UI)]
    B -- Stdin/Stdout --> A
```

1.  **游戏端 (Java)**: 通过 `CommunicationMod` 将当前游戏状态 (GameState) 序列化为 JSON，写入标准输出 (Stdout)。
2.  **后端 (Python)**: `GameBridge` (继承自 `Coordinator`) 监听标准输入 (Stdin)，解析 JSON 数据。
3.  **决策层**: `GameBridge` 调用内部评分引擎，为手牌中的每一张卡打分。
4.  **通信层**: 评分结果再次序列化为 JSON，通过 TCP Socket 推送到 `localhost:9999`。
5.  **前端 (Python)**: `Overlay UI` 接收数据，在游戏窗口上方绘制推荐建议。

---

## 2. 评分引擎逻辑 (Scoring Engine Logic)

目前的决策逻辑位于 `src/connector/game_bridge.py` 的 `calculate_recommendation` 方法中。它是一个**启发式规则引擎 (Heuristic Rule-Based Engine)**。

### 核心评分公式

对于每一张卡牌 $C$，其基础得分 $S(C)$ 计算如下：

$$ S(C) = BaseScore(Type) + Bonus(Context) $$

#### A. 基础分 (Base Score)
*   **攻击牌 (Attack)**: 10 分
*   **技能牌 (Skill)**: 10 分
*   **能力牌 (Power)**: 20 分 (通常能力牌价值较高)
*   **状态/诅咒 (Status/Curse)**: -10 分

#### B. 斩杀检测 (Lethal Detection)
这是最高优先级的逻辑。

1.  **单卡斩杀 (Single Card Lethal)**:
    如果 $Damage(C) \ge HP(Monster)$，则 $Score += 50$。
    *逻辑*: 如果一张牌能秒杀怪物，它的价值极大。

2.  **组合斩杀 (Combo Lethal)**:
    如果 $Sum(Damage(Hand)) \ge HP(Monster)$，则所有参与攻击的卡牌 $Score += 40$。
    *逻辑*: 如果所有攻击牌加起来能秒杀怪物，那么每一张攻击牌都至关重要，哪怕单张伤害不足。
    *修复记录*: 解决了“11血怪，2张打击(6+6)却推荐防御”的 Bug。

#### C. 防御逻辑 (Defense Logic)
*   **需要格挡 (Need Block)**:
    如果 $IncomingDamage > CurrentBlock$，则防御牌 $Score += 15$。
*   **溢出惩罚**: 如果格挡已经足够，防御牌得分不再增加。

#### D. 特殊修正 (Special Modifiers)
*   **AOE (范围攻击)**: 如果场上怪物数量 > 1 且卡牌是 AOE 类型， $Score += 10$。
*   **成长性 (Scaling)**: 
    *   力量 (Strength): $Score += 5 \times StrengthGain$
    *   敏捷 (Dexterity): $Score += 5 \times DexterityGain$
*   **易伤 (Vulnerable)**: 如果能施加易伤，$Score += 8$。
*   **虚弱 (Weak)**: 如果怪物意图是攻击且能施加虚弱，$Score += 8$。

---

## 3. 游戏流控制 (Game Flow Control)

### 自动/手动开始 (Auto/Manual Start)
为了给予用户更多控制权，我们在 `GameBridge` 中实现了 `auto_start` 开关：
*   **默认状态**: `False` (手动模式)。
*   **实现方式**: 重写 `get_next_action_out_of_game` 方法。
    *   当 `auto_start=False` 时，返回 `NullAction`，系统处于待机状态，等待用户手动点击游戏菜单。
    *   当 `auto_start=True` 时，返回 `StartGameAction`，自动进入游戏。

### 自动打牌 (Auto Play)
*   **默认状态**: `False` (辅助模式)。
*   **实现方式**: 在 `get_next_action_in_game` 中检查 `self.auto_play`。
    *   如果为 `False`，仅计算评分并更新 UI，不发送打牌指令。
    *   如果为 `True`，根据最高分卡牌自动发送 `PlayCardAction` (待实现完善)。

---

## 4. 关键类设计 (Key Classes)

### `GameBridge` (src/connector/game_bridge.py)
*   **`receive_game_state_update(state)`**: 接收游戏状态回调。
*   **`calculate_recommendation()`**: 核心算法实现。
*   **`get_next_action_out_of_game()`**: 处理游戏外逻辑（如自动/手动开始）。

### `OverlayWindow` (src/ui/overlay_ui.py)
*   使用 `PySide6` 实现。
*   `setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)`: 保持置顶且无边框。
*   `setAttribute(Qt.WA_TranslucentBackground)`: 背景透明。
*   `DataReceiver`: `QThread` 子类，防止网络 I/O 阻塞 UI 渲染。

## 5. 调试与扩展
*   **日志**: 所有日志输出到 `stderr`，避免污染 `stdout` (因为 `stdout` 被用于与游戏通信)。
*   **Mock**: 使用 `tests/mock_game_feed.py` 模拟游戏数据流，方便在不启动游戏的情况下调试 UI 和算法。
