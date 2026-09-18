import os
import json
import datetime
from datetime import timezone
import logging
import time
from typing import Optional, Dict, Any
import pytz

from bot.config import config
from bot.tradovate_client import tradovate_client
from bot.contract_resolver import resolve_active_contract
from bot.zone_calculator import zone_calculator
from bot.risk_manager import risk_manager
from bot.notifier import notifier
from bot.daily_briefing import generate_and_send_briefing
from bot.macro_calendar import get_macro_event_for_date

logger = logging.getLogger("Strategy")

class LondonZonesStrategy:
    def __init__(self):
        self.tz = pytz.timezone(config.timezone)
        self.tz_madrid = pytz.timezone("Europe/Madrid")
        self.current_trading_date: Optional[datetime.date] = None
        self.state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "daily_state.json")
        self.briefing_sent: bool = False
        self.orders_placed: bool = False
        self.amber_cleaned: bool = False
        self.eod_cleaned: bool = False
        
        # Estat diari
        self.active_symbol: Optional[str] = None
        self.london_high: Optional[float] = None
        self.london_low: Optional[float] = None
        self.asia_high: Optional[float] = None
        self.asia_low: Optional[float] = None
        self.short_order_id: Optional[int] = None
        self.long_order_id: Optional[int] = None
        self.asia_short_order_id: Optional[int] = None
        self.asia_long_order_id: Optional[int] = None

    def load_state(self, today: datetime.date) -> bool:
        """Carrega l'estat des del fitxer de persistència si correspon a la jornada d'avui."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("date") == str(today):
                        self.orders_placed = data.get("orders_placed", False)
                        self.amber_cleaned = data.get("amber_cleaned", False)
                        self.eod_cleaned = data.get("eod_cleaned", False)
                        self.active_symbol = data.get("active_symbol")
                        self.london_high = data.get("london_high")
                        self.london_low = data.get("london_low")
                        self.short_order_id = data.get("short_order_id")
                        self.long_order_id = data.get("long_order_id")
                        logger.info(f"💾 Estat recuperat de disc per a {today}: orders_placed={self.orders_placed}")
                        return True
        except Exception as e:
            logger.warning(f"Error carregant estat de disc: {e}")
        return False

    def save_state(self):
        """Desa l'estat actual al disc."""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            data = {
                "date": str(self.current_trading_date),
                "orders_placed": bool(self.orders_placed),
                "amber_cleaned": bool(self.amber_cleaned),
                "eod_cleaned": bool(self.eod_cleaned),
                "active_symbol": str(self.active_symbol) if self.active_symbol is not None else None,
                "london_high": float(self.london_high) if isinstance(self.london_high, (int, float)) else None,
                "london_low": float(self.london_low) if isinstance(self.london_low, (int, float)) else None,
                "short_order_id": int(self.short_order_id) if isinstance(self.short_order_id, int) else None,
                "long_order_id": int(self.long_order_id) if isinstance(self.long_order_id, int) else None,
                "updated_at": datetime.datetime.now(timezone.utc).isoformat()
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Error desant estat de disc: {e}")

    def reset_for_new_day(self, today: datetime.date):
        """Reinicia l'estat per a una nova jornada operativa."""
        self.current_trading_date = today
        self.briefing_sent = False
        self.orders_placed = False
        self.amber_cleaned = False
        self.eod_cleaned = False
        self.active_symbol = None
        self.london_high = None
        self.london_low = None
        self.asia_high = None
        self.asia_low = None
        self.short_order_id = None
        self.long_order_id = None
        self.asia_short_order_id = None
        self.asia_long_order_id = None

        # 1. Intentar carregar estat persistent si el bot s'ha reiniciat durant el dia
        self.load_state(today)

        # 2. Si no estava marcat com a col·locat, consultar el broker directament si hi ha credencials
        if not self.orders_placed and config.user and config.password and config.bot_mode != "macro_only":
            try:
                if tradovate_client.authenticate():
                    if tradovate_client.has_orders_or_fills_today(today):
                        logger.info(f"🛡️ Activitat prèvia detectada a Tradovate per al dia {today}. Marcant orders_placed = True.")
                        self.orders_placed = True
                        self.save_state()
            except Exception as e:
                logger.warning(f"Error consultant ordres prèvies a Tradovate: {e}")

        logger.info(f"🔄 Estat establert per a la jornada: {today} (orders_placed: {self.orders_placed})")

    def on_london_close(self, now: datetime.datetime):
        """
        Es crida exactament a les 05:00 EDT (11:00 CEST) quan finalitza la sessió de Londres.
        Calcula els nivells institucionals i col·loca les dues ordres OSO a Tradovate.
        """
        if self.orders_placed:
            logger.info("Les ordres d'avui ja han estat col·locades prèviament.")
            return

        today = now.date()
        # Verificar que sigui dia laborable (dilluns=0 a divendres=4)
        if today.weekday() >= 5:
            logger.info(f"Cap de setmana detectat ({today}). Mercat CME tancat.")
            return

        # Si estem en mode només macro o no hi ha credencials, no intentar enviar ordres al broker
        if config.bot_mode == "macro_only" or not config.user:
            logger.info("ℹ️ Mode Només-Macro actiu o credencials no configurades. Ordres no enviades al broker.")
            self.orders_placed = True
            self.save_state()
            return

        # 1. Assegurar autenticació
        is_auth = tradovate_client.authenticate()
        if not is_auth and config.tradovate_env == "live":
            notifier.send("ERROR CRÍTIC TRADOVATE", "No s'ha pogut autenticar amb Tradovate!", color="danger")
            return

        # 2. Resoldre el contracte actiu (ex: MNQU6, MNQZ6)
        self.active_symbol = resolve_active_contract(tradovate_client, config.symbol_base)
        logger.info(f"Símbol operatiu seleccionat: {self.active_symbol}")

        # 3. Consultar saldo i calcular mida de posició
        cash_balance = tradovate_client.get_cash_balance()
        contracts = risk_manager.calculate_contracts(cash_balance)
        
        if not risk_manager.validate_margin(cash_balance, contracts):
            logger.error("Risc: Marge insuficient. Ordres no enviades.")
            return

        # Double-check Tradovate broker history directament abans de col·locar
        if tradovate_client.has_orders_or_fills_today(today):
            logger.info(f"🛡️ Tradovate ja té ordres o execucions registrades per a {today}. Ometent col·locació repetida.")
            self.orders_placed = True
            self.save_state()
            return

        # 4. Calcular London High i London Low
        self.london_high, self.london_low = zone_calculator.calculate_london_range(
            date=today,
            tradovate_client=tradovate_client,
            symbol=self.active_symbol
        )

        if self.london_high is None or self.london_low is None:
            err = f"❌ Error: No s'han pogut determinar els nivells de Londres per al dia {today}."
            logger.error(err)
            notifier.send("ERROR DE ZONES", err, color="danger")
            return

        # 5. Càlcul de preus de l'estratègia (TP Dinàmic segons cota NQ, SL Invariant 60 pts)
        # Regla quantitativa validada: NQ < 21.000 pts -> TP 8 pts; NQ >= 21.000 pts -> TP 10 pts
        dynamic_tp = 8.0 if self.london_high < 21000.0 else config.tp_points
        dynamic_sl = config.sl_points

        # Zona Alta Londres: Sell Limit @ High
        short_entry = self.london_high
        short_tp = round(short_entry - dynamic_tp, 2)
        short_sl = round(short_entry + dynamic_sl, 2)

        # Zona Baixa Londres: Buy Limit @ Low
        long_entry = self.london_low
        long_tp = round(long_entry + dynamic_tp, 2)
        long_sl = round(long_entry - dynamic_sl, 2)

        # 🛡️ SANITY GUARD DE PREU DE MERCAT (Evitar ompliment instantani a mercat)
        curr_price = tradovate_client.get_current_market_price(config.symbol_base)
        can_place_short = True
        can_place_long = True

        if curr_price is not None:
            logger.info(f"Preu actual de mercat ({config.symbol_base}): {curr_price:.2f}")
            if curr_price >= short_entry:
                logger.warning(
                    f"⚠️ SANITY GUARD: Preu actual ({curr_price:.2f}) >= Short Entry ({short_entry:.2f}). "
                    f"El mercat ja ha trencat a l'alça! Ometent Sell Limit per evitar conversió a ordre a mercat immediata."
                )
                can_place_short = False
            if curr_price <= long_entry:
                logger.warning(
                    f"⚠️ SANITY GUARD: Preu actual ({curr_price:.2f}) <= Long Entry ({long_entry:.2f}). "
                    f"El mercat ja ha trencat a la baixa! Ometent Buy Limit per evitar conversió a ordre a mercat immediata."
                )
                can_place_long = False

        # 6. Si estem en Mode Avaluació, calcular també nivells d'Àsia (Àsia Filtrada >= 11:00 CEST)
        is_eval_mode = config.bot_mode == "evaluation"
        asia_msg = ""
        if is_eval_mode and config.evaluation_include_asia:
            self.asia_high, self.asia_low = zone_calculator.calculate_asia_range(
                date=today,
                tradovate_client=tradovate_client,
                symbol=self.active_symbol
            )
            if self.asia_high and self.asia_low:
                asia_short_tp = round(self.asia_high - dynamic_tp, 2)
                asia_short_sl = round(self.asia_high + dynamic_sl, 2)
                asia_long_tp = round(self.asia_low + dynamic_tp, 2)
                asia_long_sl = round(self.asia_low - dynamic_sl, 2)
                asia_msg = (
                    f"\n\n🌏 **ZONES D'ÀSIA FILTRADA (≥ 11:00 CEST)**:\n"
                    f"🔴 **SHORT (Asia High)**: `{self.asia_high:.2f}` (TP: `{asia_short_tp:.2f}`, SL: `{asia_short_sl:.2f}`)\n"
                    f"🟢 **LONG (Asia Low)**:   `{self.asia_low:.2f}` (TP: `{asia_long_tp:.2f}`, SL: `{asia_long_sl:.2f}`)"
                )

        # 7. Col·locació d'ordres OSO a Tradovate
        regime_str = "< 21.000 pts (TP 8 pts)" if self.london_high < 21000.0 else "≥ 21.000 pts (TP 10 pts)"
        mode_badge = f"🎯 [MODE AVALUACIÓ FAST-PASS: {contracts} MNQ]" if is_eval_mode else f"🛡️ [MODE FUNDED CONSERVADOR: {contracts} MNQ]"
        
        short_status_text = f"`{short_entry:.2f}`\n   • Take Profit: `{short_tp:.2f}` (+{dynamic_tp:.1f} pts)\n   • Stop Loss:   `{short_sl:.2f}` (-{dynamic_sl:.1f} pts)" if can_place_short else f"~~{short_entry:.2f}~~ *(Omesa: preu de mercat ja per sobre)*"
        long_status_text = f"`{long_entry:.2f}`\n   • Take Profit: `{long_tp:.2f}` (+{dynamic_tp:.1f} pts)\n   • Stop Loss:   `{long_sl:.2f}` (-{dynamic_sl:.1f} pts)" if can_place_long else f"~~{long_entry:.2f}~~ *(Omesa: preu de mercat ja per sota)*"

        notifier.send(
            f"{mode_badge} ZONES CALCULADES",
            f"**Data**: {today}\n"
            f"**Contracte**: `{self.active_symbol}`\n"
            f"**Règim NQ**: `{regime_str}`\n\n"
            f"🔴 **SHORT (London High)**: {short_status_text}\n\n"
            f"🟢 **LONG (London Low)**: {long_status_text}"
            f"{asia_msg}\n\n"
            f"🎯 _Ordres límit col·locades amb protecció de creuament._",
            color="info"
        )

        # Enviar Short OSO Londres si és segur
        if can_place_short:
            short_res = tradovate_client.place_bracket_order(
                symbol=self.active_symbol,
                action="Sell",
                qty=contracts,
                entry_price=short_entry,
                tp_price=short_tp,
                sl_price=short_sl
            )
            if short_res:
                self.short_order_id = short_res.get("orderId")

        # Enviar Long OSO Londres si és segur
        if can_place_long:
            long_res = tradovate_client.place_bracket_order(
                symbol=self.active_symbol,
                action="Buy",
                qty=contracts,
                entry_price=long_entry,
                tp_price=long_tp,
                sl_price=long_sl
            )
            if long_res:
                self.long_order_id = long_res.get("orderId")

        # Enviar OSO Àsia si estem en mode Avaluació
        if is_eval_mode and config.evaluation_include_asia and self.asia_high and self.asia_low:
            # Asia Short OSO
            a_s_res = tradovate_client.place_bracket_order(
                symbol=self.active_symbol,
                action="Sell",
                qty=contracts,
                entry_price=self.asia_high,
                tp_price=round(self.asia_high - dynamic_tp, 2),
                sl_price=round(self.asia_high + dynamic_sl, 2)
            )
            if a_s_res:
                self.asia_short_order_id = a_s_res.get("orderId")

            # Asia Long OSO
            a_l_res = tradovate_client.place_bracket_order(
                symbol=self.active_symbol,
                action="Buy",
                qty=contracts,
                entry_price=self.asia_low,
                tp_price=round(self.asia_low + dynamic_tp, 2),
                sl_price=round(self.asia_low - dynamic_sl, 2)
            )
            if a_l_res:
                self.asia_long_order_id = a_l_res.get("orderId")

        self.orders_placed = True
        self.save_state()
        logger.info(f"✅ Ordres OSO ({mode_badge}) col·locades correctament al mercat.")

    def on_eod_close(self, now: datetime.datetime):
        """
        Es crida a les 16:55 EDT (22:55 CEST) per netejar ordres pendents i tancar qualsevol posició.
        """
        if self.eod_cleaned:
            return

        logger.info("⏰ Executant protocol de tancament EOD CME (16:55 EDT)...")
        
        # 1. Cancel·lar totes les ordres pendents
        canceled = tradovate_client.cancel_all_pending_orders()
        
        # 2. Tancar/aplanar posicions obertes
        tradovate_client.close_all_positions(symbol=self.active_symbol)

        # 3. Consultar balanç final
        final_balance = tradovate_client.get_cash_balance()

        notifier.send(
            "🌙 TANCAMENT EOD CME (16:55 EDT)",
            f"**Jornada completada**: {now.date()}\n"
            f"• Ordres límit no tocades cancel·lades: {canceled}\n"
            f"• Posicions aplanades (Flatten) abans de l'overnight.",
            color="warning"
        )

        self.eod_cleaned = True
        self.save_state()

    def process_tick(self, now: Optional[datetime.datetime] = None):
        """
        Rutina periòdica d'avaluació segons l'hora actual (America/New_York).
        """
        if now is None:
            now = datetime.datetime.now(self.tz)

        today = now.date()

        # Nou dia?
        if self.current_trading_date != today:
            self.reset_for_new_day(today)

        hour = now.hour
        minute = now.minute

        # 0. Briefing Matinal a Discord a les 10:00 CEST (dilluns a divendres)
        now_madrid = now.astimezone(self.tz_madrid) if now else datetime.datetime.now(self.tz_madrid)
        if now_madrid.date().weekday() < 5:
            if now_madrid.hour == 10 and not self.briefing_sent:
                generate_and_send_briefing(now_madrid.date())
                self.briefing_sent = True

        macro = get_macro_event_for_date(today)
        is_fomc = macro and macro.get("type") == "FOMC"
        is_amber = macro and macro.get("severity") == "AMBER"

        # 1. Moment de col·locació d'ordres
        # Finestra estricta d'execució de Londres: 05:00 a 05:30 EDT (11:00 a 11:30 CEST)
        is_london_time = (hour == config.london_end_hour and config.london_end_minute <= minute <= 30)
        is_past_london_window = (hour > config.london_end_hour) or (hour == config.london_end_hour and minute > 30)
        can_trade_now = not (is_fomc and now_madrid.hour >= 18) and (hour < config.eod_close_hour)

        if not self.orders_placed:
            if is_london_time and can_trade_now:
                self.on_london_close(now)
            elif is_past_london_window:
                # Si el bot es connecta més tard de les 05:30 EDT, verificar broker
                if tradovate_client.has_orders_or_fills_today(today):
                    logger.info(f"🛡️ Jornada en curs: activitat prèvia d'avui ({today}) detectada a Tradovate. Marcant orders_placed = True.")
                else:
                    logger.info(f"⏰ Finestra operativa de Londres superada ({hour:02d}:{minute:02d} EDT). No es col·loquen noves ordres intradia.")
                self.orders_placed = True
                self.save_state()

        # 2. Cancel·lació de protecció en dies AMBER (CPI / NFP) a les 14:20 CEST si no s'ha omplert l'ordre
        if is_amber and (now_madrid.hour > 14 or (now_madrid.hour == 14 and now_madrid.minute >= 20)):
            if self.orders_placed and not self.amber_cleaned:
                logger.info("⚠️ Notícia AMBER detectada: Cancel·lant ordres límit pendents abans de les 14:30...")
                tradovate_client.cancel_all_pending_orders()
                notifier.send(
                    "⚠️ CANCEL·LACIÓ PRE-NOTÍCIA (14:20 CEST)",
                    f"**Esdeveniment**: {macro.get('name')}\n"
                    f"• Ordres límit no tocades retirades abans de la publicació de dades (14:30).\n"
                    f"• Prevenció de fuetades de liquiditat i slippage violent.",
                    color="warning"
                )
                self.amber_cleaned = True

        # 3. Tancament anticipat per a dies de FOMC (18:00 CEST)
        if is_fomc and now_madrid.hour >= 18:
            if not self.eod_cleaned:
                logger.info("⏰ Tancament anticipat de seguretat FOMC a les 18:00 CEST...")
                self.on_eod_close(now)

        # 4. Tancament EOD estàndard CME (16:55 EDT)
        if hour == config.eod_close_hour and minute >= config.eod_close_minute:
            if not self.eod_cleaned:
                self.on_eod_close(now)

strategy = LondonZonesStrategy()
