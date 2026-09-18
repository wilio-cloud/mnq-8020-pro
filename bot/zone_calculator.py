import datetime
import logging
from typing import Tuple, Optional
import pandas as pd
import pytz
import yfinance as yf
from bot.config import config

logger = logging.getLogger("ZoneCalculator")

class ZoneCalculator:
    def __init__(self):
        self.tz = pytz.timezone(config.timezone)

    def calculate_london_range(
        self,
        date: Optional[datetime.date] = None,
        tradovate_client = None,
        symbol: str = "MNQ"
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calcula el màxim (London High) i el mínim (London Low) de la sessió de Londres
        (02:00 a 05:00 EDT / America/New_York) per a la data indicada.
        """
        if date is None:
            now_ny = datetime.datetime.now(self.tz)
            date = now_ny.date()

        logger.info(f"Calculant rang de Londres per a la data: {date} (02:00 - 05:00 EDT)...")

        # 1. Intentar obtenir dades directes via Tradovate si hi ha client connectat
        high_low = self._fetch_from_tradovate(tradovate_client, symbol, date)
        if high_low[0] is not None and high_low[1] is not None:
            logger.info(f"✅ Nivells de Londres obtinguts via Tradovate: High={high_low[0]:.2f}, Low={high_low[1]:.2f}")
            return high_low

        # 2. Resilient Live Provider: yfinance CME Globex futures ('MNQ=F' o 'NQ=F')
        high_low = self._fetch_from_yfinance(date)
        if high_low[0] is not None and high_low[1] is not None:
            logger.info(f"✅ Nivells de Londres obtinguts via CME Live Feed: High={high_low[0]:.2f}, Low={high_low[1]:.2f}")
            return high_low

        logger.error(f"❌ No s'han pogut calcular els nivells de Londres per a {date}.")
        return None, None

    def calculate_asia_range(
        self,
        date: Optional[datetime.date] = None,
        tradovate_client = None,
        symbol: str = "MNQ"
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Calcula el màxim (Asia High) i el mínim (Asia Low) de la sessió d'Àsia
        (20:00 a 00:00 EDT) prèvia a la sessió del dia indicat.
        """
        if date is None:
            now_ny = datetime.datetime.now(self.tz)
            date = now_ny.date()

        logger.info(f"Calculant rang d'Àsia per a la sessió: {date} (20:00 - 00:00 EDT)...")
        prev_day = date - datetime.timedelta(days=1)

        tickers_to_try = ["MNQ=F", "NQ=F"]
        for t in tickers_to_try:
            try:
                ticker = yf.Ticker(t)
                df = ticker.history(period="5d", interval="1m")
                if df.empty:
                    continue

                if df.index.tz is None:
                    df.index = df.index.tz_localize("UTC").tz_convert(self.tz)
                else:
                    df.index = df.index.tz_convert(self.tz)

                mask = (
                    (df.index.date == prev_day) &
                    (df.index.hour >= config.asia_start_hour)
                )
                asia_bars = df[mask]
                if len(asia_bars) >= 10:
                    asia_high = float(asia_bars["High"].max())
                    asia_low = float(asia_bars["Low"].min())
                    asia_high = round(round(asia_high / config.tick_size) * config.tick_size, 2)
                    asia_low = round(round(asia_low / config.tick_size) * config.tick_size, 2)
                    logger.info(f"✅ Nivells d'Àsia obtinguts: High={asia_high:.2f}, Low={asia_low:.2f}")
                    return asia_high, asia_low
            except Exception as e:
                logger.debug(f"Error consultant {t} per Àsia: {e}")

        logger.warning(f"⚠️ No s'han pogut calcular els nivells d'Àsia per a {date}.")
        return None, None

    def _fetch_from_yfinance(self, target_date: datetime.date) -> Tuple[Optional[float], Optional[float]]:
        """Obté les barres d'1 minut de NQ/MNQ des de CME Globex via yfinance."""
        tickers_to_try = ["MNQ=F", "NQ=F"]
        for t in tickers_to_try:
            try:
                ticker = yf.Ticker(t)
                df = ticker.history(period="5d", interval="1m")
                if df.empty:
                    continue

                # Assegurar timezone America/New_York
                if df.index.tz is None:
                    df.index = df.index.tz_localize("UTC").tz_convert(self.tz)
                else:
                    df.index = df.index.tz_convert(self.tz)

                # Filtrar per sessió de Londres (02:00:00 <= hora < 05:00:00) de la data objectiu
                mask = (
                    (df.index.date == target_date) &
                    (df.index.hour >= config.london_start_hour) &
                    (df.index.hour < config.london_end_hour)
                )
                london_bars = df[mask]

                if len(london_bars) >= 10:  # Almenys 10 barres per confirmar dades vàlides
                    london_high = float(london_bars["High"].max())
                    london_low = float(london_bars["Low"].min())
                    
                    # Arrodonir al tick de 0.25
                    london_high = round(round(london_high / config.tick_size) * config.tick_size, 2)
                    london_low = round(round(london_low / config.tick_size) * config.tick_size, 2)
                    return london_high, london_low
            except Exception as e:
                logger.debug(f"Error consultant {t}: {e}")

        return None, None

    def _fetch_from_tradovate(
        self,
        client,
        symbol: str,
        target_date: datetime.date
    ) -> Tuple[Optional[float], Optional[float]]:
        """Placeholder per a la consulta per socket de Tradovate si està configurat."""
        # Si no hi ha client o no està autenticat, retorna None
        if not client or not client.access_token:
            return None, None
        return None, None

zone_calculator = ZoneCalculator()
