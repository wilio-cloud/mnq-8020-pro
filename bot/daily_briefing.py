"""
Mòdul de Publicació del Briefing Matinal a Discord (10:00 CEST) - Estratègia 80/20 NY Open
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
    Genera i envia un informe concís i net a Discord sobre l'operabilitat del dia per a l'estratègia 80/20 NY Open.
    Sense text sobrant ("palla"), directe als paràmetres i estat clau.
    """
    tz_madrid = pytz.timezone("Europe/Madrid")
    if target_date is None:
        target_date = datetime.datetime.now(tz_madrid).date()

    day_info = get_day_trading_status(target_date)
    active_contract = resolve_active_contract(symbol_base=config.symbol_base)

    startup_prefix = "🚀 [RAILWAY] " if is_startup else ""
    title = f"{startup_prefix}🎯 80/20 NY OPEN · {day_info['date_str']}"

    # Text concís, net i directe al gra (sense "palla")
    desc = (
        f"### {day_info['badge']}\n\n"
        f"📅 **Data**: `{day_info['date_str']}`\n"
        f"📦 **Contracte Actiu**: `{active_contract}`\n"
        f"📰 **Macro**: {day_info['headline']}\n\n"
        f"⏰ **Obertura NY**: `15:30 CEST` (09:30 EDT)\n"
        f"🎯 **Setup**: Zones 20 / 80 (Màx. 1 Trade)\n"
        f"🛡️ **Bracket OCO**: TP `+{config.tp_points:.0f} pts` | SL `-{config.sl_points:.0f} pts`"
    )

    logger.info(f"Enviant Briefing 80/20 NY Open ({day_info['status']}) per al dia {day_info['date_str']} a Discord...")
    notifier.send(title, desc, color=day_info["color_name"])
    return True

if __name__ == "__main__":
    print("📢 Enviant Briefing de diagnòstic a Discord...")
    generate_and_send_briefing()

