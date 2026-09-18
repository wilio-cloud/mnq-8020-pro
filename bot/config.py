import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Carregar fitxer .env si existeix
load_dotenv()

@dataclass
class BotConfig:
    # Entorn
    tradovate_env: str = os.getenv("TRADOVATE_ENV", "demo").lower()
    
    # Credencials Tradovate
    user: str = os.getenv("TRADOVATE_USER", "")
    password: str = os.getenv("TRADOVATE_PASS", "")
    app_id: str = os.getenv("TRADOVATE_APP_ID", "MNQZonesBot")
    app_version: str = os.getenv("TRADOVATE_APP_VERSION", "1.0")
    cid: Optional[str] = os.getenv("TRADOVATE_CID", None)
    sec: str = os.getenv("TRADOVATE_SEC", "")
    
    # Compte
    account_id: Optional[int] = int(os.getenv("TRADOVATE_ACCOUNT_ID")) if os.getenv("TRADOVATE_ACCOUNT_ID") else None
    account_spec: Optional[str] = os.getenv("TRADOVATE_ACCOUNT_SPEC", None)
    
    # Paràmetres estratègia
    symbol_base: str = os.getenv("SYMBOL_BASE", "MNQ")
    tp_points: float = float(os.getenv("TP_POINTS", "10.0"))
    sl_points: float = float(os.getenv("SL_POINTS", "60.0"))
    tick_size: float = 0.25
    point_value: float = 2.0  # 1 punt MNQ = $2 USD
    
    # Risc i Escalat
    bot_mode: str = os.getenv("BOT_MODE", "funded").lower()  # 'funded', 'evaluation' o 'macro_only'
    initial_contracts: int = int(os.getenv("INITIAL_CONTRACTS", "1"))
    evaluation_contracts: int = int(os.getenv("EVALUATION_CONTRACTS", "8"))  # Opció A: 8 MNQ Turbo Fast-Pass
    evaluation_include_asia: bool = os.getenv("EVALUATION_INCLUDE_ASIA", "true").lower() in ("true", "1", "yes")
    evaluation_min_entry_hour: int = int(os.getenv("EVALUATION_MIN_ENTRY_HOUR", "5"))  # 05:00 EDT (11:00 CEST)
    auto_scale: bool = os.getenv("AUTO_SCALE", "true").lower() in ("true", "1", "yes")
    scale_threshold_2: float = float(os.getenv("SCALE_THRESHOLD_2_CONTRACTS", "2200.0"))
    scale_threshold_3: float = float(os.getenv("SCALE_THRESHOLD_3_CONTRACTS", "3500.0"))
    scale_threshold_4: float = float(os.getenv("SCALE_THRESHOLD_4_CONTRACTS", "4800.0"))
    
    # Horaris (EDT / America/New_York)
    timezone: str = "America/New_York"
    asia_start_hour: int = int(os.getenv("ASIA_START_HOUR", "20"))
    asia_end_hour: int = int(os.getenv("ASIA_END_HOUR", "0"))
    london_start_hour: int = int(os.getenv("LONDON_START_HOUR", "2"))
    london_start_minute: int = int(os.getenv("LONDON_START_MINUTE", "0"))
    london_end_hour: int = int(os.getenv("LONDON_END_HOUR", "5"))
    london_end_minute: int = int(os.getenv("LONDON_END_MINUTE", "0"))
    eod_close_hour: int = int(os.getenv("EOD_CLOSE_HOUR", "16"))
    eod_close_minute: int = int(os.getenv("EOD_CLOSE_MINUTE", "55"))
    
    # Alertes
    discord_webhook_url: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL", None)
    telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN", None)
    telegram_chat_id: Optional[str] = os.getenv("TELEGRAM_CHAT_ID", None)

    @property
    def base_url(self) -> str:
        if self.tradovate_env == "live":
            return "https://live.tradovateapi.com/v1"
        return "https://demo.tradovateapi.com/v1"

    @property
    def ws_url(self) -> str:
        if self.tradovate_env == "live":
            return "wss://live.tradovateapi.com/v1/websocket"
        return "wss://demo.tradovateapi.com/v1/websocket"

    @property
    def md_ws_url(self) -> str:
        if self.tradovate_env == "live":
            return "wss://md.tradovateapi.com/v1/websocket"
        return "wss://md-demo.tradovateapi.com/v1/websocket"

config = BotConfig()
