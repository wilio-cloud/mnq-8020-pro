import unittest
import os
import sys

# Assegurar imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.risk_manager import risk_manager
from bot.config import config

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        # Assegurar configuració neta per als tests
        config.bot_mode = "funded"
        config.auto_scale = True
        config.evaluation_contracts = 8

    def test_position_sizing(self):
        config.bot_mode = "funded"
        config.auto_scale = True

        # 1. Saldo inicial de 1.000$ -> 1 MNQ
        self.assertEqual(risk_manager.calculate_contracts(1000.0), 1)
        self.assertEqual(risk_manager.calculate_contracts(1500.0), 1)
        self.assertEqual(risk_manager.calculate_contracts(2199.0), 1)

        # 2. Saldo de 2.200$ -> 2 MNQ
        self.assertEqual(risk_manager.calculate_contracts(2200.0), 2)
        self.assertEqual(risk_manager.calculate_contracts(3000.0), 2)

        # 3. Saldo de 3.500$ -> 3 MNQ
        self.assertEqual(risk_manager.calculate_contracts(3500.0), 3)

        # 4. Saldo de 4.800$ -> 4 MNQ
        self.assertEqual(risk_manager.calculate_contracts(4800.0), 4)
        self.assertEqual(risk_manager.calculate_contracts(7000.0), 4)

    def test_evaluation_mode_sizing(self):
        # En mode avaluació ha de retornar els contractes d'avaluació (ex: 8 MNQ fix)
        config.bot_mode = "evaluation"
        config.evaluation_contracts = 8
        self.assertEqual(risk_manager.calculate_contracts(1000.0), 8)
        self.assertEqual(risk_manager.calculate_contracts(50000.0), 8)

    def test_margin_validation(self):
        # Amb 1.000$ i 1 MNQ (100$ marge + 300$ buffer = 400$) ha de ser vàlid
        self.assertTrue(risk_manager.validate_margin(1000.0, 1))

        # Amb 350$ i 1 MNQ (necessita 400$), ha de rebutjar
        self.assertFalse(risk_manager.validate_margin(350.0, 1))

if __name__ == "__main__":
    unittest.main()
