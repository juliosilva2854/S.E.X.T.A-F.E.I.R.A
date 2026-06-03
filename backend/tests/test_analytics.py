"""Regression tests para os endpoints de Analytics (Mavis/Sexta-Feira)."""
import requests

BASE = "http://localhost:8001/api/analytics"


def test_kpis():
    r = requests.get(f"{BASE}/kpis", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["total_dias"] > 0
    assert d["total_km"] > 0
    assert isinstance(d["top_destinos"], list)


def test_kpis_filtered_unidade():
    r = requests.get(f"{BASE}/kpis", params={"unidade": "SANTO AMARO"}, timeout=30)
    assert r.status_code == 200
    assert "filtro" in r.json()


def test_weekly():
    r = requests.get(f"{BASE}/weekly", params={"weeks": 12}, timeout=30)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_unidades():
    r = requests.get(f"{BASE}/unidades", timeout=30)
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_map_data_complete():
    """Garante que TODAS as unidades sejam geolocalizadas (cache populado)."""
    r = requests.get(f"{BASE}/map-data", params={"allow_remote": "true"}, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert len(d["points"]) == d["total_unidades"], f"unresolved: {d['unresolved']}"
    assert d["unresolved"] == [], f"unidades sem coordenada: {d['unresolved']}"
    for p in d["points"]:
        assert -90 <= p["lat"] <= 90 and -180 <= p["lng"] <= 180


def test_export_csv():
    r = requests.get(f"{BASE}/export", params={"format": "csv"}, timeout=30)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "attachment" in r.headers["content-disposition"]
    assert len(r.content) > 0


def test_export_xlsx():
    r = requests.get(f"{BASE}/export", params={"format": "xlsx"}, timeout=30)
    assert r.status_code == 200
    assert r.content[:2] == b"PK"  # zip/xlsx magic


def test_export_pdf():
    r = requests.get(f"{BASE}/export", params={"format": "pdf"}, timeout=30)
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_export_invalid_format():
    r = requests.get(f"{BASE}/export", params={"format": "xml"}, timeout=30)
    assert r.status_code == 400



def test_daily():
    r = requests.get(f"{BASE}/daily", timeout=30)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_heatmap_weekday():
    r = requests.get(f"{BASE}/heatmap", timeout=30)
    assert r.status_code == 200


def test_activities():
    r = requests.get(f"{BASE}/activities", timeout=30)
    assert r.status_code == 200


def test_monthly_12m():
    r = requests.get(f"{BASE}/monthly", params={"months": 12}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


def test_month_detail():
    # pega o primeiro mes do monthly e verifica detalhe
    monthly = requests.get(f"{BASE}/monthly", params={"months": 12}, timeout=30).json()
    if not monthly:
        return  # sem dados, skip
    month_key = monthly[0].get("mes") or monthly[0].get("month") or monthly[0].get("key")
    if not month_key:
        # tenta o YYYY-MM atual
        from datetime import datetime
        month_key = datetime.now().strftime("%Y-%m")
    r = requests.get(f"{BASE}/month/{month_key}", timeout=30)
    assert r.status_code == 200


def test_kpis_filters_full():
    """Aceita start, end, fuel_cost, km_per_liter."""
    r = requests.get(
        f"{BASE}/kpis",
        params={"start": "2024-01-01", "end": "2026-12-31", "fuel_cost": 6.0, "km_per_liter": 10.0},
        timeout=30,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["total_km"] >= 0


def test_export_content_disposition():
    for fmt, ct in [("csv", "text/csv"), ("xlsx", "spreadsheetml"), ("pdf", "application/pdf")]:
        r = requests.get(f"{BASE}/export", params={"format": fmt}, timeout=30)
        assert r.status_code == 200
        assert "attachment" in r.headers.get("content-disposition", "")
        assert ct in r.headers.get("content-type", "")
