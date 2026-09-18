import logging
from bot.config import config

logger = logging.getLogger("RiskManager")

class RiskManager:
    def __init__(self):
        self.day_margin_per_mnq = 100.0  # Marge intradia estàndard a Tradovate
        self.min_cash_buffer = 300.0      # Coixí mínim de seguretat absolut

    def calculate_contracts(self, cash_balance: float) -> int:
        """
        Calcula el nombre de contractes MNQ basat en el capital actual
        i els llindars d'escalat de drawdown.
        """
        if config.bot_mode == "evaluation":
            qty = config.evaluation_contracts
            logger.info(f"🎯 [MODE AVALUACIÓ FAST-PASS] Sizing fix: {qty} MNQ (Capital: ${cash_balance:,.2f})")
            return qty

        if not config.auto_scale:
            return config.initial_contracts

        if cash_balance >= config.scale_threshold_4:
            qty = 4
        elif cash_balance >= config.scale_threshold_3:
            qty = 3
        elif cash_balance >= config.scale_threshold_2:
            qty = 2
        else:
            qty = 1

        logger.info(f"🛡️ [MODE FUNDED] Capital: ${cash_balance:,.2f} | Posició calculada: {qty} MNQ")
        return qty

    def validate_margin(self, cash_balance: float, contracts: int) -> bool:
        """
        Comprova que hi hagi prou marge al compte per obrir la posició sense perill
        de liquidació automàtica per part del broker.
        """
        required_margin = contracts * self.day_margin_per_mnq
        total_needed = required_margin + self.min_cash_buffer

        if cash_balance < total_needed:
            err_msg = (
                f"⚠️ Marge insuficient! Saldo disponible: ${cash_balance:,.2f}, "
                f"Requerit per operar ({contracts} MNQ + coixí): ${total_needed:,.2f}."
            )
            logger.error(err_msg)
            return False

        return True

risk_manager = RiskManager()
