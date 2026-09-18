import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from unittest.mock import MagicMock, patch
import datetime
import pytz

from bot.strategy import LondonZonesStrategy

class TestAdaptiveStrategy(unittest.TestCase):
    def setUp(self):
        self.strat = LondonZonesStrategy()

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.risk_manager")
    @patch("bot.strategy.zone_calculator")
    @patch("bot.strategy.notifier")
    def test_dynamic_tp_under_21000(self, mock_notifier, mock_zone_calc, mock_risk_mgr, mock_client):
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        mock_client.get_current_market_price.return_value = 18450.0
        mock_client.get_cash_balance.return_value = 50000.0
        mock_risk_mgr.calculate_contracts.return_value = 5
        mock_risk_mgr.validate_margin.return_value = True
        
        # NQ a 18.000 pts (< 21.000) -> Ha d'aplicar TP 8 pts
        mock_zone_calc.calculate_london_range.return_value = (18500.0, 18400.0)
        
        now = datetime.datetime(2026, 9, 15, 5, 5, tzinfo=self.strat.tz)
        self.strat.on_london_close(now)
        
        # Comprovar crida de short bracket: entry=18500, tp=18492 (-8 pts), sl=18550 (+50 pts)
        mock_client.place_bracket_order.assert_any_call(
            symbol=self.strat.active_symbol,
            action="Sell",
            qty=5,
            entry_price=18500.0,
            tp_price=18492.0,
            sl_price=18550.0
        )

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.risk_manager")
    @patch("bot.strategy.zone_calculator")
    @patch("bot.strategy.notifier")
    def test_dynamic_tp_above_21000(self, mock_notifier, mock_zone_calc, mock_risk_mgr, mock_client):
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        mock_client.get_current_market_price.return_value = 29050.0
        mock_client.get_cash_balance.return_value = 50000.0
        mock_risk_mgr.calculate_contracts.return_value = 5
        mock_risk_mgr.validate_margin.return_value = True
        
        # NQ a 29.000 pts (>= 21.000) -> Ha d'aplicar TP 12 pts (config.tp_points)
        mock_zone_calc.calculate_london_range.return_value = (29100.0, 29000.0)
        
        now = datetime.datetime(2026, 9, 15, 5, 5, tzinfo=self.strat.tz)
        self.strat.on_london_close(now)
        
        mock_client.place_bracket_order.assert_any_call(
            symbol=self.strat.active_symbol,
            action="Sell",
            qty=5,
            entry_price=29100.0,
            tp_price=29088.0,
            sl_price=29150.0
        )

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.risk_manager")
    @patch("bot.strategy.zone_calculator")
    @patch("bot.strategy.notifier")
    def test_sanity_guard_prevents_marketable_orders(self, mock_notifier, mock_zone_calc, mock_risk_mgr, mock_client):
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        # Preu actual a 29500 -> Per sobre del Sell Limit a 29100
        mock_client.get_current_market_price.return_value = 29500.0
        mock_client.get_cash_balance.return_value = 50000.0
        mock_risk_mgr.calculate_contracts.return_value = 1
        mock_risk_mgr.validate_margin.return_value = True
        mock_zone_calc.calculate_london_range.return_value = (29100.0, 29000.0)

        now = datetime.datetime(2026, 9, 15, 5, 5, tzinfo=self.strat.tz)
        self.strat.on_london_close(now)

        # Comprovar que NO s'ha enviat cap ordre de Sell Limit perquè el preu està per sobre
        sell_calls = [c for c in mock_client.place_bracket_order.call_args_list if c.kwargs.get("action") == "Sell"]
        self.assertEqual(len(sell_calls), 0)

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.risk_manager")
    @patch("bot.strategy.zone_calculator")
    @patch("bot.strategy.notifier")
    def test_existing_broker_orders_blocks_duplicate(self, mock_notifier, mock_zone_calc, mock_risk_mgr, mock_client):
        mock_client.authenticate.return_value = True
        # Ja hi ha ordres/fills avui a Tradovate
        mock_client.has_orders_or_fills_today.return_value = True

        now = datetime.datetime(2026, 9, 15, 5, 5, tzinfo=self.strat.tz)
        self.strat.on_london_close(now)

        mock_client.place_bracket_order.assert_not_called()
        self.assertTrue(self.strat.orders_placed)

    @patch("bot.strategy.tradovate_client")
    @patch("bot.strategy.notifier")
    def test_amber_cancellation_at_1420(self, mock_notifier, mock_client):
        # 2026-10-02 és NFP (AMBER)
        mock_client.authenticate.return_value = True
        mock_client.has_orders_or_fills_today.return_value = False
        self.strat.reset_for_new_day(datetime.date(2026, 10, 2))
        self.strat.orders_placed = True
        self.strat.amber_cleaned = False
        
        # 14:25 CEST (8:25 EDT) -> Abans de 14:30 NFP -> Ha de cancel·lar ordres pendents
        now_edt = datetime.datetime(2026, 10, 2, 8, 25, tzinfo=self.strat.tz)
        self.strat.process_tick(now_edt)
        
        mock_client.cancel_all_pending_orders.assert_called_once()
        self.assertTrue(self.strat.amber_cleaned)

if __name__ == "__main__":
    unittest.main()
