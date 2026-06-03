"""
mavis.skills.finance — Cotações (USD/EUR/cripto) sem API key e cálculos financeiros.
"""
import urllib.request
import urllib.parse
import json
from typing import Dict, Any, List


def forex(base: str = "USD", quote: str = "BRL") -> Dict[str, Any]:
    """Cotação via awesomeapi (gratuito, sem key)."""
    try:
        url = f"https://economia.awesomeapi.com.br/last/{base}-{quote}"
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
        key = f"{base}{quote}"
        item = data.get(key, {})
        return {
            "pair": f"{base}/{quote}",
            "bid": float(item.get("bid", 0)),
            "ask": float(item.get("ask", 0)),
            "high": float(item.get("high", 0)),
            "low": float(item.get("low", 0)),
            "variation_pct": float(item.get("pctChange", 0)),
            "timestamp": item.get("create_date", ""),
        }
    except Exception as e:
        return {"error": str(e)}


def multi_forex() -> List[Dict[str, Any]]:
    pairs = [("USD", "BRL"), ("EUR", "BRL"), ("GBP", "BRL"), ("BTC", "BRL"), ("ETH", "BRL")]
    return [forex(b, q) for b, q in pairs]


def crypto(coin_id: str = "bitcoin", vs: str = "brl") -> Dict[str, Any]:
    """CoinGecko (sem key)."""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={vs}&include_24hr_change=true"
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
        info = data.get(coin_id, {})
        return {
            "coin": coin_id,
            "price": info.get(vs),
            "change_24h_pct": info.get(f"{vs}_24h_change"),
            "vs": vs.upper(),
        }
    except Exception as e:
        return {"error": str(e)}


def loan_payment(principal: float, annual_rate_pct: float, months: int) -> Dict[str, Any]:
    """Calcula parcela mensal (sistema Price/PMT)."""
    if months <= 0:
        return {"error": "meses > 0"}
    r = annual_rate_pct / 100.0 / 12.0
    if r == 0:
        pmt = principal / months
    else:
        pmt = principal * (r * (1 + r) ** months) / ((1 + r) ** months - 1)
    total = pmt * months
    return {
        "monthly_payment": round(pmt, 2),
        "total_paid": round(total, 2),
        "total_interest": round(total - principal, 2),
        "months": months,
        "annual_rate_pct": annual_rate_pct,
    }


def compound_interest(principal: float, annual_rate_pct: float, years: float,
                      monthly_contribution: float = 0) -> Dict[str, Any]:
    """Juros compostos com aporte mensal."""
    months = int(years * 12)
    r = annual_rate_pct / 100.0 / 12.0
    balance = principal
    serie = []
    for m in range(months):
        balance = balance * (1 + r) + monthly_contribution
        if m % 12 == 11:
            serie.append({"year": (m + 1) // 12, "balance": round(balance, 2)})
    total_aportado = principal + monthly_contribution * months
    return {
        "final_balance": round(balance, 2),
        "total_aportado": round(total_aportado, 2),
        "lucro": round(balance - total_aportado, 2),
        "anos": years,
        "serie_anual": serie,
    }


def convert_currency(amount: float, base: str = "USD", quote: str = "BRL") -> Dict[str, Any]:
    fx = forex(base, quote)
    if "error" in fx:
        return fx
    return {
        "from": f"{amount} {base}",
        "to": f"{round(amount * fx['bid'], 2)} {quote}",
        "rate": fx["bid"],
    }
