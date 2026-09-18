"""
Mòdul de Publicació del Briefing Matinal a Discord (10:00 CEST)
"""

import os
import sys
import datetime
from typing import Optional
import pytz
import logging

# Assegurar paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import config
from bot.notifier import notifier
from bot.contract_resolver import resolve_active_contract
from bot.macro_calendar import get_day_trading_status

logger = logging.getLogger("DailyBriefing")

def generate_and_send_briefing(target_date: Optional[datetime.date] = None, is_startup: bool = False) -> bool:
    """
    Genera i envia el missatge del Briefing Matinal a Discord.
    is_startup: Si és True, afegeix un badge d'inici de servei a Railway.
    """
    tz_madrid = pytz.timezone("Europe/Madrid")
    if target_date is None:
        target_date = datetime.datetime.now(tz_madrid).date()

    day_info = get_day_trading_status(target_date)
    active_contract = resolve_active_contract(symbol_base=config.symbol_base)

    prefix = "🚀 [RAILWAY STARTUP] " if is_startup else ""
    title = f"{prefix}{day_info['badge']} — {day_info['date_str']}"
    
    desc = (
        f"### 🚦 VEREDICTE DEL DIA: **{day_info['badge']}**\n\n"
        f"**📅 CONTEXT MACRO**: {day_info['headline']}\n"
        f"**🕒 FINESTRA OPERATIVA**: `{day_info['time_window']}`\n"
        f"**📦 CONTRACTE ACTIU CME**: `{active_contract}`\n"
        f"**⚙️ MODE DEL BOT**: `{config.bot_mode.upper()}` (TP: {config.tp_points} pts | SL: {config.sl_points} pts)\n\n"
        f"**📋 INSTRUCCIONS DEL PROTOCOL**:\n"
        f"{day_info['instructions']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ _Filtre de Risc CME Globex • Estratègia NQ Zones 2026/2027_"
    )

    logger.info(f"Enviant Briefing ({day_info['status']}) per al dia {day_info['date_str']} a Discord...")
    notifier.send(title, desc, color=day_info["color_name"])
    return True

if __name__ == "__main__":
    print("📢 Enviant Briefing de diagnòstic a Discord...")
    generate_and_send_briefing()
