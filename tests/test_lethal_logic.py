
import unittest
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
# Add external/spirecomm to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'external', 'spirecomm'))

from src.connector.game_bridge import GameBridge
from spirecomm.spire.game import Game
from spirecomm.spire.card import Card, CardType, CardRarity
from spirecomm.spire.character import Player, Monster, Intent

class TestLethalLogic(unittest.TestCase):
    def setUp(self):
        self.bridge = GameBridge()
        self.bridge.game = Game()
        
        # Setup Player
        # 3 Energy
        self.bridge.game.player = Player(max_hp=80, current_hp=80, block=0, energy=3)
        
        # Setup Monster
        # 1 Monster, 11 HP, Intent: Attack (10 dmg)
        self.monster = Monster(
            name="Cultist",
            monster_id="Cultist",
            max_hp=11,
            current_hp=11,
            block=0,
            intent=Intent.ATTACK,
            half_dead=False,
            is_gone=False,
            move_adjusted_damage=10,
            move_hits=1
        )
        self.bridge.game.monsters = [self.monster]
        
        # Setup Hand
        # 2 Strikes (6 dmg each, 1 cost)
        # 1 Defend (5 block, 1 cost)
        self.strike1 = Card(
            card_id="Strike_R",
            name="Strike",
            card_type=CardType.ATTACK,
            rarity=CardRarity.BASIC,
            cost=1,
            uuid="strike_1",
            is_playable=True
        )
        self.strike2 = Card(
            card_id="Strike_R",
            name="Strike",
            card_type=CardType.ATTACK,
            rarity=CardRarity.BASIC,
            cost=1,
            uuid="strike_2",
            is_playable=True
        )
        self.defend = Card(
            card_id="Defend_R",
            name="Defend",
            card_type=CardType.SKILL,
            rarity=CardRarity.BASIC,
            cost=1,
            uuid="defend_1",
            is_playable=True
        )
        self.bridge.game.hand = [self.strike1, self.strike2, self.defend]

    def test_strike_should_outscore_defend_when_lethal(self):
        """
        Scenario: Monster has 11 HP and is attacking.
        Hand: 2 Strikes (6 dmg each) + 1 Defend.
        Expected: Strikes should have higher score than Defend because 2 Strikes = 12 dmg > 11 HP (Lethal).
        """
        recommendations = self.bridge.calculate_recommendation()
        
        strike_score = recommendations.get(self.strike1.uuid)
        defend_score = recommendations.get(self.defend.uuid)
        
        print(f"DEBUG: Strike Score: {strike_score}")
        print(f"DEBUG: Defend Score: {defend_score}")
        
        # Current flawed logic likely gives Defend > Strike
        # We want Strike > Defend
        self.assertGreater(strike_score, defend_score, f"Strike score ({strike_score}) should be > Defend score ({defend_score}) in combo lethal scenario")

    def test_defend_should_outscore_strike_when_not_lethal(self):
        # Scenario: Monster 20 HP (not lethal), 10 damage incoming.
        # Hand: Strike (6), Strike (6), Defend (5).
        # Expected: Defend should be prioritized to block damage.
        
        # Update monster HP to be survive combo (6+6=12 < 20)
        self.monster.current_hp = 20
        self.monster.max_hp = 20
        # Update monster damage to be threatening
        self.monster.move_adjusted_damage = 10
        self.monster.intent = Intent.ATTACK
        
        recommendations = self.bridge.calculate_recommendation()
        
        strike_score = recommendations.get(self.strike1.uuid, 0)
        defend_score = recommendations.get(self.defend.uuid, 0)
        
        print(f"DEBUG (Non-Lethal): Strike Score: {strike_score}")
        print(f"DEBUG (Non-Lethal): Defend Score: {defend_score}")
        
        self.assertGreater(defend_score, strike_score, f"Defend score ({defend_score}) should be > Strike score ({strike_score}) when not lethal and taking damage")

if __name__ == '__main__':
    unittest.main()
