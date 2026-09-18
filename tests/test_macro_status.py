import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.macro_calendar import get_day_trading_status

def test_weekend_status():
    saturday = datetime.date(2026, 9, 19)
    sunday = datetime.date(2026, 9, 20)
    
    sat_res = get_day_trading_status(saturday)
    assert sat_res["status"] == "NOT_OPERABLE"
    assert sat_res["is_weekend"] is True
    assert "CAP DE SETMANA" in sat_res["badge"]

    sun_res = get_day_trading_status(sunday)
    assert sun_res["status"] == "NOT_OPERABLE"
    assert sun_res["is_weekend"] is True

def test_holiday_status():
    christmas = datetime.date(2026, 12, 25)
    res = get_day_trading_status(christmas)
    assert res["status"] == "NOT_OPERABLE"
    assert res["is_holiday"] is True
    assert "FESTIU CME" in res["badge"]

def test_fomc_full_shutdown():
    fomc_sep = datetime.date(2026, 12, 16)
    res = get_day_trading_status(fomc_sep)
    assert res["status"] == "NOT_OPERABLE"
    assert res["severity"] == "RED"
    assert "ALTA PERILLOSITAT" in res["badge"]

def test_fomc_standard_restricted():
    fomc_standard = datetime.date(2026, 11, 5)
    res = get_day_trading_status(fomc_standard)
    assert res["status"] == "RESTRICTED"
    assert res["severity"] == "RED"
    assert "FOMC" in res["badge"]
    assert "18:00 CEST" in res["instructions"]

def test_amber_nfp_restricted():
    nfp = datetime.date(2026, 10, 2)
    res = get_day_trading_status(nfp)
    assert res["status"] == "RESTRICTED"
    assert res["severity"] == "AMBER"
    assert "PRECAUCIÓ" in res["badge"]

def test_clean_green_day():
    clean_day = datetime.date(2026, 9, 17)
    res = get_day_trading_status(clean_day)
    assert res["status"] == "OPERABLE"
    assert res["severity"] == "GREEN"
    assert "LLUM VERDA" in res["badge"]

if __name__ == "__main__":
    test_weekend_status()
    test_holiday_status()
    test_fomc_full_shutdown()
    test_fomc_standard_restricted()
    test_amber_nfp_restricted()
    test_clean_green_day()
    print("✅ Tots els tests de test_macro_status han passat correctament!")
