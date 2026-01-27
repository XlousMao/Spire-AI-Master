import json
import threading
import socket
import logging
import sys
import time
from typing import Dict, Any

from spirecomm.ai.agent import SimpleAgent
from spirecomm.spire.card import CardType
from spirecomm.communication.action import PlayCardAction, EndTurnAction, Action

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NullAction(Action):
    """
    一个什么都不做的 Action，用于暂停自动打牌逻辑。
    Coordinator 执行它时不会发送任何指令给游戏。
    """
    def __init__(self):
        super().__init__(command="null", requires_game_ready=False)

    def execute(self, coordinator):
        # Do nothing
        pass

class GameBridge(SimpleAgent):
    """
    GameBridge 充当游戏逻辑和 UI 之间的中介。
    它继承自 SimpleAgent，因此可以直接从 spirecomm 获取游戏状态。
    它的核心职责是将清洗后的状态广播给 Socket Server。
    """

    def __init__(self, host='127.0.0.1', port=9999):
        super().__init__()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)
        self.client_socket = None
        self.running = True
        self.auto_play = False  # 默认关闭自动打牌
        self.auto_start = False # 默认关闭自动开始游戏
        
        # 启动 Socket 监听线程
        self.socket_thread = threading.Thread(target=self._accept_client, daemon=True)
        self.socket_thread.start()
        logger.info(f"GameBridge initialized. Listening on {host}:{port}")

    def _accept_client(self):
        """等待 UI 客户端连接"""
        while self.running:
            try:
                client, addr = self.server_socket.accept()
                logger.info(f"UI Client connected from {addr}")
                self.client_socket = client
            except Exception as e:
                logger.error(f"Socket accept error: {e}")

    def _broadcast_state(self, recommendation: Dict[str, Any]):
        """将当前状态和推荐操作打包发送给 UI"""
        if not self.client_socket:
            return

        # 提取当前游戏关键信息
        try:
            state_snapshot = {
                "hand": [
                    {
                        "uuid": card.uuid,
                        "name": card.name,
                        "cost": card.cost,
                        "type": str(card.type),
                        "recommendation_score": recommendation.get(card.uuid, 0)
                    }
                    for card in self.game.hand
                ],
                "player": {
                    "energy": self.game.player.energy,
                    "block": self.game.player.block,
                    "hp": self.game.player.current_hp,
                    "max_hp": self.game.player.max_hp
                },
                "monsters": [
                    {
                        "name": m.name,
                        "hp": m.current_hp,
                        "max_hp": m.max_hp,
                        "intent": str(m.intent),
                        "damage": m.move_adjusted_damage
                    }
                    for m in self.game.monsters if not m.is_gone
                ]
            }

            # 发送 JSON 数据，以换行符分隔
            data = json.dumps(state_snapshot) + "\n"
            self.client_socket.sendall(data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to send state: {e}")
            self.client_socket = None  # 断开连接处理


    def calculate_recommendation(self) -> Dict[str, int]:
        """
        基于 Bottled AI 逻辑的启发式推荐引擎。
        优先逻辑：
        1. 斩杀 (Lethal)
        2. 保命 (Survival)
        3. 高效 (Efficiency)
        4. AOE 识别 (AOE Check)
        5. 力量加成 (Strength Scaling)
        """
        recommendations = {}
        if not self.game or not self.game.hand:
            return recommendations

        # --- 1. 分析战场形势 (Analyze Battle State) ---
        player = self.game.player
        monsters = [m for m in self.game.monsters if not m.is_gone and not m.half_dead]
        monster_count = len(monsters)
        
        # 计算即将受到的总伤害
        incoming_damage = 0
        is_attacked = False
        for m in monsters:
            if m.intent.is_attack():
                is_attacked = True
                # 注意：move_adjusted_damage 是单次伤害，如果有多次攻击(move_hits)，需要乘算
                damage = m.move_adjusted_damage or 0
                hits = m.move_hits or 1
                incoming_damage += damage * hits
        
        # 计算需要的格挡
        needed_block = max(0, incoming_damage - player.block)
        is_in_danger = needed_block > 0
        is_critical = player.current_hp <= incoming_damage # 可能会死

        # 检查自身 Buff
        has_strength = False
        strength_amt = 0
        for p in player.powers:
            if p.power_id == "Strength":
                has_strength = True
                strength_amt = p.amount
                break
        
        # --- 2. 预计算：最大可造成伤害 (Pre-calculate Max Possible Damage) ---
        # 考虑能量限制和卡牌组合，计算当前回合能造成的最大伤害
        total_hand_damage = 0
        attack_cards = [c for c in self.game.hand if c.type == CardType.ATTACK]
        
        # 简单的背包问题解法 (Greedy approach for max damage)
        # 方案 A: 优先打出易伤牌 (Vulnerable Priority)
        damage_a = 0
        energy_a = player.energy
        has_vulnerable = False
        
        # 寻找易伤源
        vulnerable_cards = [c for c in attack_cards if "bash" in c.card_id.lower() or "terror" in c.card_id.lower() or "shockwave" in c.card_id.lower() or "uppercut" in c.card_id.lower() or "thunderclap" in c.card_id.lower() or "beam cell" in c.card_id.lower()]
        other_attacks = [c for c in attack_cards if c not in vulnerable_cards]
        
        if vulnerable_cards and energy_a >= vulnerable_cards[0].cost:
            vuln_card = vulnerable_cards[0]
            # 计算易伤牌伤害
            base_dmg = 6
            if "bash" in vuln_card.card_id.lower(): base_dmg = 8
            damage_a += base_dmg + strength_amt
            energy_a -= vuln_card.cost
            has_vulnerable = True
            
        # 填充剩余能量
        sorted_others = sorted(other_attacks, key=lambda c: 6 if "strike" in c.card_id.lower() else 5, reverse=True) # 简单按伤害排序
        for card in sorted_others:
            if energy_a >= card.cost:
                base_dmg = 6
                if "strike" in card.card_id.lower(): base_dmg = 6
                final_dmg = base_dmg + strength_amt
                if has_vulnerable:
                    final_dmg = int(final_dmg * 1.5)
                damage_a += final_dmg
                energy_a -= card.cost
                
        # 方案 B: 纯伤害最大化 (Pure Damage)
        # 简单按 D/C (Damage Per Cost) 排序? 或者直接按伤害高低填入
        # 这里简化为按伤害排序
        damage_b = 0
        energy_b = player.energy
        all_sorted = sorted(attack_cards, key=lambda c: 8 if "bash" in c.card_id.lower() else 6, reverse=True)
        for card in all_sorted:
            if energy_b >= card.cost:
                base_dmg = 6
                if "bash" in card.card_id.lower(): base_dmg = 8
                damage_b += base_dmg + strength_amt
                energy_b -= card.cost
                
        total_hand_damage = max(damage_a, damage_b)

        # 修正：考虑怪物格挡/蜷身 (Curl Up Adjustment)
        # 如果怪物有 Curl Up，总伤害需要减去 3 (假设我们会触发它)
        # 这里简单对所有怪物做保守估计
        for m in monsters:
             for p in m.powers:
                 if p.power_id == "Curl Up":
                     total_hand_damage -= p.amount

        # 检查是否对某个怪物有斩杀能力 (Total Lethal Check)
        # 如果总伤害足以杀死某个怪物，那么所有攻击牌的价值都应提升
        can_kill_monster_map = {} # monster_index -> boolean
        for m in monsters:
            if m.current_hp <= total_hand_damage:
                can_kill_monster_map[m.monster_index] = True

        # --- 3. 遍历手牌打分 ---
        for card in self.game.hand:
            score = 50 # 基础分
            
            # --- 基础属性修正 ---
            # 0费牌通常是好的润滑剂
            if card.cost == 0:
                score += 10
            # 费用过高惩罚
            elif card.cost >= 2:
                score -= 5
                
            # 能量不足直接 0 分
            if card.cost > player.energy:
                recommendations[card.uuid] = 0
                continue

            # --- 核心逻辑 ---
            
            # A. 攻击牌逻辑
            if card.type == CardType.ATTACK:
                estimated_damage = 6 # 默认值
                is_aoe = False
                is_multi_hit = False
                
                # 关键词检测
                lower_name = card.name.lower()
                lower_id = card.card_id.lower()
                
                # 易伤源识别 (Vulnerable Source)
                is_vulnerable_source = False
                vulnerable_keywords = ["bash", "terror", "shockwave", "uppercut", "thunderclap", "beam cell"]
                if any(k in lower_id for k in vulnerable_keywords):
                    is_vulnerable_source = True

                # AOE 加分
                if is_aoe and monster_count > 1:
                    score += 20 * monster_count # 怪物越多越强
                
                # 力量加成对多段攻击的加分
                if has_strength and is_multi_hit:
                    score += 10 + (strength_amt * 2) # 力量越高，多段攻击价值越高

                # 斩杀判断 (Lethal Logic)
                is_lethal_contributor = False
                
                # A. 单卡斩杀 (Single Card Lethal)
                estimated_damage = 6 # 默认值
                if "strike" in lower_id or "打击" in lower_name: estimated_damage = 6 + strength_amt
                elif "bash" in lower_id: estimated_damage = 8 + strength_amt
                
                single_card_lethal = False
                for m in monsters:
                    if m.current_hp <= estimated_damage:
                        single_card_lethal = True
                        break
                
                # B. 组合斩杀 (Combo Lethal)
                # 如果这张卡是攻击牌，且全队总伤害能造成击杀，这张卡就是斩杀组件
                combo_lethal = False
                for m in monsters:
                    if can_kill_monster_map.get(m.monster_index, False):
                        combo_lethal = True
                        break

                if single_card_lethal:
                    score += 50 # 单卡直接斩杀，极高优先级
                elif combo_lethal:
                    score += 40 # 组合斩杀组件，高优先级
                    
                    # 关键修正：如果是易伤源，且有后续伤害，给予额外加分以确保先手打出
                    if is_vulnerable_source and len(attack_cards) > 1:
                         score += 25 # 确保超过普通打击 (40 vs 40+25)
                         # 抵消高费用的惩罚
                         if card.cost >= 2:
                             score += 5
                else:
                    score += 10 # 普通攻击加分
                    
                    # 非斩杀情况下的易伤也很重要
                    if is_vulnerable_source and len(attack_cards) > 1:
                        score += 15

            # B. 防御牌逻辑
            elif card.type == CardType.SKILL:
                # 假设是防御牌 (包含 Defend, Block 等关键词)
                is_block_card = "Defend" in card.card_id or "Block" in card.name or "Wall" in card.name or "防御" in card.name
                if is_block_card:
                    if not is_attacked:
                        # 负面状态：如果敌人不攻击，防御牌分数归零
                        score = 0
                    elif is_in_danger:
                        score += 30 # 需要防御时，防御牌很重要
                        if is_critical:
                            score += 100 # 快死了，必须防御
                    else:
                        score -= 10 # 不需要防御时，防御牌价值降低
            
            # C. 能力牌逻辑
            elif card.type == CardType.POWER:
                score += 20 # 能力牌通常越早打越好
            
            recommendations[card.uuid] = min(100, max(0, score)) # 限制在 0-100
            
        return recommendations

    def get_next_action_in_game(self, game_state):
        # print(f"DEBUG: Received Game State, Hand size: {len(game_state.hand)}", file=sys.stderr)
        # 1. 让父类更新 self.game
        super().get_next_action_in_game(game_state)
        
        # 2. 计算推荐
        try:
            recommendations = self.calculate_recommendation()
            
            # 3. 广播给 UI
            self._broadcast_state(recommendations)
        except Exception as e:
            logger.error(f"Error in recommendation/broadcast: {e}")

        # 4. 自动打牌逻辑开关
        if not self.auto_play:
            # 暂停模式：不发送任何指令，或者发送空指令防止 Coordinator 崩溃
            # 为了防止 CPU 空转，稍微 sleep 一下
            time.sleep(0.5) 
            return NullAction()
            
        # 5. 原有逻辑（暂时保留，以便开启 auto_play 时使用）
        # 这里应该调用一个真正的决策函数，目前暂时返回 EndTurnAction
        if self.game.end_available:
             return EndTurnAction()
        return EndTurnAction()

    def get_next_action_out_of_game(self):
        """
        处理游戏外的状态（如菜单界面）。
        """
        if self.auto_start:
            return super().get_next_action_out_of_game()
        else:
            # 如果不自动开始，就什么都不做，等待用户手动操作
            time.sleep(1) # 避免疯狂轮询
            return NullAction()
