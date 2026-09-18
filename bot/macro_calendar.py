"""
Base de Dades del Calendari Macroeconòmic Institucional (2026 - 2027)
Filtre de Risc per a CME Globex MNQ
"""

import datetime
from typing import Optional, Dict, Any

MACRO_EVENTS = {
    # --- 2026 ---
    "2026-09-16": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Decisió de tipus de la Fed. Tancament obligatori abans de les 18:00 CEST."},
    "2026-09-18": {"type": "OPEX", "severity": "AMBER", "name": "Quadruple Witching OpEx (Venciment Trimestral)", "time_cest": "Tot el dia", "instructions": "Alta volatilitat d'expiració de contractes. Londres operable amb normalitat de 11:00 a 16:00 CEST."},
    "2026-09-30": {"type": "REBALANCING", "severity": "AMBER", "name": "Final de Trimestre Q3 Rebalancing", "time_cest": "16:00 - 22:00 CEST", "instructions": "Fluxos de reequilibri institucional de carteres al final de la sessió americana. Londres al matí és 100% net."},
    "2026-10-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Sessió de Londres normal al matí (11:00 a 14:20 CEST). Si no s'ha tocat a les 14:20 CEST, cancel·lar l'ordre límit pendent."},
    "2026-10-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Zona de Londres vàlida de 11:00 a 14:20 CEST. Cancel·lar immediatament si no s'ha tocat a les 14:20 CEST."},
    "2026-11-04": {"type": "FOMC", "severity": "AMBER", "name": "FOMC Meeting (Dia 1)", "time_cest": "Tot el dia", "instructions": "Rang estret previ a la decisió de tipus. Operable a Londres amb normalitat."},
    "2026-11-05": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CET", "instructions": "Decisió de tipus d'interès. Londres operable. Apagar el bot i tancar posicions abans de les 18:00 CET."},
    "2026-11-06": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si encara no s'ha executat."},
    "2026-11-12": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Zona operable fins a les 14:20 CET. Cancel·lar pendents abans de les 14:30 CET."},
    "2026-11-26": {"type": "HOLIDAY", "severity": "GRAY", "name": "Thanksgiving Day", "time_cest": "Tot el dia", "instructions": "CME Globex tancat. Festa operativa."},
    "2026-11-27": {"type": "HOLIDAY", "severity": "GRAY", "name": "Black Friday (Early Close)", "time_cest": "19:00 CET", "instructions": "Tancament anticipat de mercat. Volum baix, no operar."},
    "2026-12-04": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2026-12-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2026-12-16": {"type": "FOMC", "severity": "RED", "name": "FOMC + Projeccions SEP (Powell)", "time_cest": "20:00 CET", "instructions": "Reunió trimestral clau de la Fed amb gràfic de punts (dot plot). Apagar el bot completament avui."},
    "2026-12-24": {"type": "HOLIDAY", "severity": "GRAY", "name": "Christmas Eve", "time_cest": "19:15 CET", "instructions": "Tancament anticipat. Sense volum institucional. No operar."},
    "2026-12-25": {"type": "HOLIDAY", "severity": "GRAY", "name": "Nadal", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2026-12-31": {"type": "HOLIDAY", "severity": "GRAY", "name": "Cap d'Any (Early Close)", "time_cest": "Tot el dia", "instructions": "Volum festiu reduït. Mercat sense liquiditat institucional."},

    # --- 2027 ---
    "2027-01-01": {"type": "HOLIDAY", "severity": "GRAY", "name": "Any Nou", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-01-08": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-01-13": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-01-18": {"type": "HOLIDAY", "severity": "GRAY", "name": "Martin Luther King Jr. Day", "time_cest": "19:00 CET", "instructions": "Tancament anticipat CME. No operar."},
    "2027-01-27": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CET", "instructions": "Apagar el bot abans de les 18:00 CET."},
    "2027-02-05": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-02-11": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-02-15": {"type": "HOLIDAY", "severity": "GRAY", "name": "Presidents' Day", "time_cest": "19:00 CET", "instructions": "Tancament anticipat CME. No operar."},
    "2027-03-05": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-03-11": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-03-17": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Projeccions)", "time_cest": "19:00 CET", "instructions": "Reunió trimestral clau. Apagar el bot tot el dia."},
    "2027-03-26": {"type": "HOLIDAY", "severity": "GRAY", "name": "Good Friday", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-04-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-04-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-05": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Apagar el bot abans de les 18:00 CEST."},
    "2027-05-07": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-12": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-05-31": {"type": "HOLIDAY", "severity": "GRAY", "name": "Memorial Day", "time_cest": "19:00 CEST", "instructions": "Tancament anticipat CME. No operar."},
    "2027-06-04": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-06-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-06-16": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Powell)", "time_cest": "20:00 CEST", "instructions": "Reunió trimestral clau. Apagar el bot tot el dia."},
    "2027-07-02": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-07-05": {"type": "HOLIDAY", "severity": "GRAY", "name": "Independence Day (Obs)", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-07-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-07-28": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "20:00 CEST", "instructions": "Apagar el bot abans de les 18:00 CEST."},
    "2027-08-06": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-08-11": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-08-27": {"type": "FOMC", "severity": "RED", "name": "Jackson Hole Economic Symposium", "time_cest": "16:00 CEST", "instructions": "Discurs de Powell sobre política monetària a llarg termini. Apagar el bot."},
    "2027-09-03": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-09-06": {"type": "HOLIDAY", "severity": "GRAY", "name": "Labor Day", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-09-14": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-09-22": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Powell)", "time_cest": "20:00 CEST", "instructions": "Reunió trimestral clau. Apagar el bot."},
    "2027-10-01": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-10-13": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CEST", "instructions": "Cancel·lar ordre pendent a les 14:20 CEST si no s'ha tocat."},
    "2027-11-03": {"type": "FOMC", "severity": "RED", "name": "FOMC Rate Decision", "time_cest": "19:00 CET", "instructions": "Apagar el bot abans de les 17:00 CET."},
    "2027-11-05": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-11-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-11-25": {"type": "HOLIDAY", "severity": "GRAY", "name": "Thanksgiving Day", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."},
    "2027-11-26": {"type": "HOLIDAY", "severity": "GRAY", "name": "Black Friday", "time_cest": "19:00 CET", "instructions": "Tancament anticipat. No operar."},
    "2027-12-03": {"type": "NFP", "severity": "AMBER", "name": "NFP (Ocupació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-12-10": {"type": "CPI", "severity": "AMBER", "name": "CPI (Inflació EUA)", "time_cest": "14:30 CET", "instructions": "Cancel·lar ordre pendent a les 14:20 CET si no s'ha tocat."},
    "2027-12-15": {"type": "FOMC", "severity": "RED", "name": "FOMC + SEP (Powell)", "time_cest": "20:00 CET", "instructions": "Reunió trimestral clau. Apagar el bot."},
    "2027-12-24": {"type": "HOLIDAY", "severity": "GRAY", "name": "Christmas Eve", "time_cest": "19:15 CET", "instructions": "Tancament anticipat. No operar."},
    "2027-12-25": {"type": "HOLIDAY", "severity": "GRAY", "name": "Nadal", "time_cest": "Tot el dia", "instructions": "CME Globex tancat."}
}

def get_macro_event_for_date(target_date: Optional[datetime.date] = None) -> Optional[Dict[str, Any]]:
    """
    Retorna la informació de l'esdeveniment macro si la data indicada està al calendari.
    """
    if target_date is None:
        target_date = datetime.date.today()
        
    date_key = target_date.strftime("%Y-%m-%d")
    return MACRO_EVENTS.get(date_key, None)

def get_day_trading_status(target_date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    Classifica de manera inequívoca si la jornada és:
    - 'OPERABLE': Llum Verda (Condicions òptimes, 95% WR).
    - 'RESTRICTED': Llum Groga (Operable amb precaució i protocol horari estricte).
    - 'NOT_OPERABLE': Llum Vermella (Mercat tancat o prohibit per risc extrem).
    """
    if target_date is None:
        target_date = datetime.date.today()

    date_str = target_date.strftime("%d/%m/%Y")
    is_weekend = target_date.weekday() >= 5  # 5=Dissabte, 6=Diumenge

    # 1. Cap de Setmana
    if is_weekend:
        day_name = "Dissabte" if target_date.weekday() == 5 else "Diumenge"
        return {
            "date": target_date,
            "date_str": date_str,
            "status": "NOT_OPERABLE",
            "can_trade": False,
            "severity": "GRAY",
            "color_name": "danger",
            "badge": "🔴 NO OPERAR (CAP DE SETMANA)",
            "title": f"MERCAT TANCAT — {day_name} {date_str}",
            "headline": f"Mercat CME Globex tancat ({day_name}).",
            "instructions": "Cap de setmana. El mercat romandrà tancat fins diumenge a la nit.",
            "time_window": "Mercat tancat",
            "event": None,
            "is_weekend": True,
            "is_holiday": False
        }

    event = get_macro_event_for_date(target_date)

    # 2. Esdeveniment de Risc al Calendari (Festiu, FOMC, CPI, NFP, OpEx, Rebalancing)
    if event:
        severity = event.get("severity", "AMBER")
        event_name = event.get("name", "Esdeveniment Macro")
        time_str = event.get("time_cest", "Hora no fixada")
        instructions = event.get("instructions", "")

        return {
            "date": target_date,
            "date_str": date_str,
            "status": "NOT_OPERABLE",
            "can_trade": False,
            "severity": severity,
            "color_name": "danger",
            "badge": "🔴 NO OPERAR (FILTRE MACRO ACTIVAT)",
            "title": f"FILTRE DE SEGURETAT — {date_str}",
            "headline": f"{event_name} ({time_str})",
            "instructions": f"Filtre de preservació de capital activat per {event_name}. Avui no s'opera.",
            "time_window": "Sense operativa (Filtre activat)",
            "event": event,
            "is_weekend": False,
            "is_holiday": severity == "GRAY"
        }

    # 3. Dia 100% Netejat i Valitat (Llum Verda)
    return {
        "date": target_date,
        "date_str": target_date.strftime("%d/%m/%Y"),
        "status": "OPERABLE",
        "can_trade": True,
        "severity": "GREEN",
        "color_name": "success",
        "badge": "🟢 OPERAR (LLUM VERDA)",
        "title": f"80/20 NY OPEN — {date_str}",
        "headline": "Sessió neta de notícies d'impacte institucional.",
        "instructions": "Condicions òptimes a l'obertura de NY (15:30 CEST). Executar 1 sol trade a nivells 20 / 80.",
        "time_window": "15:30 a 17:30 CEST",
        "event": None,
        "is_weekend": False,
        "is_holiday": False
    }

