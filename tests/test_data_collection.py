import sys
import os
import unittest
from unittest.mock import MagicMock
import csv

# Add src and external/spirecomm to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'external', 'spirecomm')))

from src.connector.game_bridge import GameBridge
from spirecomm.spire.card import Card, CardType
from spirecomm.spire.character import Intent

class TestDataCollection(unittest.TestCase):
    def setUp(self):
        self.bridge = GameBridge(port=9998) # Use different port
        self.bridge.collect_data = True
        self.bridge.data_file = "tests/test_data.csv" # Use test file
        self.bridge._init_data_collection()

    def tearDown(self):
        self.bridge.running = False
        if self.bridge.server_socket:
            self.bridge.server_socket.close()
        if os.path.exists("tests/test_data.csv"):
            os.remove("tests/test_data.csv")

    def test_record_decision(self):
        # Mock Game State
        mock_game = MagicMock()
        mock_game.floor = 5
        mock_game.in_combat = True
        
        # Mock Player
        mock_player = MagicMock()
        mock_player.current_hp = 50
        mock_player.max_hp = 80
        mock_player.energy = 3
        mock_player.powers = []
        mock_game.player = mock_player

        # Mock Monsters
        mock_monster = MagicMock()
        mock_monster.current_hp = 20
        mock_monster.max_hp = 20
        mock_monster.intent = Intent.ATTACK
        mock_monster.move_adjusted_damage = 10
        mock_monster.move_hits = 1
        mock_monster.is_gone = False
        mock_monster.half_dead = False
        mock_game.monsters = [mock_monster]

        # Mock Hand
        card1 = MagicMock()
        card1.uuid = "uuid-1"
        card1.name = "Strike"
        card1.type = CardType.ATTACK
        card1.card_id = "Strike_R"
        
        card2 = MagicMock()
        card2.uuid = "uuid-2"
        card2.name = "Defend"
        card2.type = CardType.SKILL
        card2.card_id = "Defend_R"

        mock_game.hand = [card1, card2]
        
        self.bridge.game = mock_game

        # Mock Recommendations
        recommendations = {"uuid-1": 50, "uuid-2": 30}

        # Trigger Record
        self.bridge._record_decision_step(recommendations)

        # Verify File Content
        self.assertTrue(os.path.exists(self.bridge.data_file))
        with open(self.bridge.data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['floor'], '5')
            self.assertEqual(row['hp_ratio'], '0.62') # 50/80
            self.assertEqual(row['best_card_name'], 'Strike')
            self.assertEqual(row['incoming_damage'], '10')

        # Test Deduplication
        self.bridge._record_decision_step(recommendations)
        with open(self.bridge.data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 1) # Should still be 1

if __name__ == '__main__':
    unittest.main()
