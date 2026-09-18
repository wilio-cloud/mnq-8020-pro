import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Assegurar que l'arrel del projecte és al sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import datetime
import logging
import signal
import time
import pytz

from bot.config import config
from bot.notifier import notifier
from bot.tradovate_client import tradovate_client
from bot.contract_resolver import resolve_active_contract
from bot.zone_calculator import zone_calculator
from bot.risk_manager import risk_manager
from bot.strategy import strategy
from bot.daily_briefing import generate_and_send_briefing
from bot.macro_calendar import get_day_trading_status

# Configuració de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("Main")

running = True

def signal_handler(signum, frame):
    global running
    logger.info("Senyal d'aturada rebut (SIGINT/SIGTERM). Aturant el bot amb seguretat...")
    running = False

def start_health_server(port: int):
    """
    Servidor HTTP ultra-lleuger per satisfer els healthchecks de Railway ($PORT).
    """
    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/health", "/status"):
                day_info = get_day_trading_status()
                active_contract = resolve_active_contract(tradovate_client, config.symbol_base)
                resp = {
                    "status": "healthy",
                    "service": "MNQ 80/20 NY Open & Macro Bot",
                    "strategy": "80/20 NY Open (15:30 CEST)",
                    "tp_points": config.tp_points,
                    "sl_points": config.sl_points,
                    "max_daily_trades": config.max_daily_trades,
                    "environment": config.tradovate_env.upper(),
                    "mode": config.bot_mode.upper(),
                    "active_contract": active_contract,
                    "date": day_info["date_str"],
                    "trading_status": day_info["status"],
                    "badge": day_info["badge"],
                    "headline": day_info["headline"],
                    "time_window": day_info["time_window"],
                    "timestamp": datetime.datetime.now(pytz.UTC).isoformat()
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(resp, ensure_ascii=False, indent=2).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            # Silenciar logs HTTP rutinaris
            pass

    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        logger.info(f"🌐 Servidor de Salut HTTP actiu al port {port} per a Railway.")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Error iniciant servidor de salut HTTP: {e}")

def run_health_check():
    """Verifica tots els components, connexions i paràmetres sense posar cap ordre."""
    print("=" * 70)
    print("🔍 DIAGNÒSTIC DE SALUT DEL BOT TRADOVATE MNQ ZONES")
    print("=" * 70)
    
    tz = pytz.timezone(config.timezone)
    now_ny = datetime.datetime.now(tz)
    tz_madrid = pytz.timezone("Europe/Madrid")
    now_madrid = datetime.datetime.now(tz_madrid)
    day_info = get_day_trading_status(now_madrid.date())

    print(f"🕒 Hora Actual (New York / CME): {now_ny.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"🕒 Hora Actual (Madrid / CEST):  {now_madrid.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"🚦 Estat Macro d'Avui:           {day_info['badge']}")
    print(f"📋 Context:                      {day_info['headline']}")
    print(f"🌐 Entorn Tradovate:             {config.tradovate_env.upper()}")
    print(f"🎯 Estratègia:                   Només Londres (TP: {config.tp_points} pts | SL: {config.sl_points} pts)")
    print(f"🛡️  Risc:                         1 MNQ per posició (Inici 1.000$)")
    
    # 1. Contracte actiu
    active_contract = resolve_active_contract(tradovate_client, config.symbol_base)
    print(f"📦 Contracte de futurs actiu:    {active_contract}")
    
    # 2. Test Tradovate Auth
    print("\n--- TEST DE CONNEXIÓ TRADOVATE ---")
    if config.user and config.password:
        auth_ok = tradovate_client.authenticate()
        if auth_ok:
            balance = tradovate_client.get_cash_balance()
            contracts = risk_manager.calculate_contracts(balance)
            print(f"✅ Autenticació:                 ÈXIT")
            print(f"💰 Saldo de compte:              ${balance:,.2f}")
            print(f"📊 Mida de posició:              {contracts} MNQ")
        else:
            print(f"❌ Autenticació:                 FALLIDA (comprova usuari i clau a .env)")
    else:
        print("⚠️  Credencials de broker no configurades (Mode només Alertes Macro)")

    # 3. Test Càlcul de Nivells de Londres
    print("\n--- TEST DE CÀLCUL DE ZONES (LONDRES) ---")
    test_date = now_ny.date()
    if now_ny.hour < 5:
        test_date = test_date - datetime.timedelta(days=1)
    
    high, low = zone_calculator.calculate_london_range(test_date)
    if high and low:
        print(f"✅ Dades de Londres ({test_date}): High = {high:.2f} | Low = {low:.2f} (Rang: {high-low:.2f} pts)")
    else:
        print(f"⚠️  No s'han pogut carregar les dades de Londres per a {test_date}")

    print("=" * 70)

def start_daemon():
    """Bucle principal d'execució contínua."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    tz = pytz.timezone(config.timezone)
    tz_madrid = pytz.timezone("Europe/Madrid")
    now_madrid = datetime.datetime.now(tz_madrid)

    # 1. Si Railway ens assigna un PORT, arrencar servidor HTTP en background
    port_env = os.getenv("PORT")
    if port_env:
        try:
            port = int(port_env)
            t = threading.Thread(target=start_health_server, args=(port,), daemon=True)
            t.start()
        except ValueError:
            logger.warning(f"PORT invàlid a l'entorn: {port_env}")

    # 2. Enviar Briefing d'Arrencada a Discord immediatament
    logger.info("Enviant estat inicial d'operabilitat macro a Discord...")
    generate_and_send_briefing(now_madrid.date(), is_startup=True)
    strategy.briefing_sent = True

    logger.info("Bot en marxa. Esperant les finestres operatives...")

    last_heartbeat = 0
    while running:
        try:
            now_ny = datetime.datetime.now(tz)
            strategy.process_tick(now_ny)

            # Heartbeat cada 30 minuts per confirmar que el procés està viu
            current_time = time.time()
            if current_time - last_heartbeat > 1800:
                logger.info(
                    f"💓 Heartbeat: Sistema actiu a les {now_ny.strftime('%H:%M:%S %Z')}. "
                    f"Ordres avui: {'SI' if strategy.orders_placed else 'NO'} | "
                    f"EOD netejat: {'SI' if strategy.eod_cleaned else 'NO'}"
                )
                last_heartbeat = current_time

            time.sleep(5)
        except Exception as e:
            logger.error(f"Error en bucle principal: {e}", exc_info=True)
            time.sleep(10)

    logger.info("Bot aturat correctament.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot Automatitzat Tradovate MNQ Zones & Macro")
    parser.add_argument("--check", action="store_true", help="Executa una comprovació de salut i diagnòstic sense enviar ordres")
    parser.add_argument("--trigger-now", action="store_true", help="Força el càlcul i col·locació d'ordres immediatament")
    parser.add_argument("--briefing", action="store_true", help="Envia el Briefing Macroeconòmic a Discord ara mateix")
    args = parser.parse_args()

    if args.check:
        run_health_check()
    elif args.trigger_now:
        tz = pytz.timezone(config.timezone)
        now = datetime.datetime.now(tz)
        print("⚡ Forçant col·locació de zones de Londres ara mateix...")
        strategy.on_london_close(now)
    elif args.briefing:
        print("📢 Enviant Briefing a Discord...")
        generate_and_send_briefing()
    else:
        start_daemon()
