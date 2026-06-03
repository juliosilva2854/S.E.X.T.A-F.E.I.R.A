"""
mavis.skills.news_weather — Notícias e clima sem API key (RSS + open-meteo).
"""
import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any


def headlines(source: str = "g1", limit: int = 5) -> List[Dict[str, Any]]:
    """Manchetes via RSS público (G1 / UOL / etc)."""
    feeds = {
        "g1": "https://g1.globo.com/rss/g1/",
        "uol": "https://rss.uol.com.br/feed/noticias.xml",
        "tecmundo": "https://www.tecmundo.com.br/rss",
    }
    url = feeds.get(source, feeds["g1"])
    try:
        import feedparser
        f = feedparser.parse(url)
        out = []
        for e in f.entries[:limit]:
            out.append({
                "title": e.get("title", ""),
                "link": e.get("link", ""),
                "published": e.get("published", ""),
                "summary": (e.get("summary", "") or "")[:240],
            })
        return out
    except Exception as e:
        return [{"error": str(e)}]


def speakable_headlines(source: str = "g1") -> str:
    items = headlines(source, 3)
    if not items or "error" in items[0]:
        return "Não consegui acessar as notícias agora, senhor."
    out = "Principais manchetes: "
    out += "; ".join(i["title"] for i in items)
    return out + "."


def weather(lat: float = -23.5505, lon: float = -46.6333) -> Dict[str, Any]:
    """Clima atual via Open-Meteo (sem API key). Default = São Paulo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone=America%2FSao_Paulo&forecast_days=1"
    )
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
        cur = data.get("current", {})
        daily = data.get("daily", {})
        return {
            "temp_c": cur.get("temperature_2m"),
            "humidity": cur.get("relative_humidity_2m"),
            "wind_kmh": cur.get("wind_speed_10m"),
            "max_c": (daily.get("temperature_2m_max") or [None])[0],
            "min_c": (daily.get("temperature_2m_min") or [None])[0],
            "rain_prob": (daily.get("precipitation_probability_max") or [None])[0],
        }
    except Exception as e:
        return {"error": str(e)}


def speakable_weather(lat: float = -23.5505, lon: float = -46.6333) -> str:
    w = weather(lat, lon)
    if "error" in w:
        return "Não consegui consultar o clima agora, senhor."
    return (
        f"Clima atual: {w['temp_c']:.0f} graus, umidade {w['humidity']}%. "
        f"Hoje a máxima é {w['max_c']:.0f} e a mínima {w['min_c']:.0f}, "
        f"com {w['rain_prob']}% de chance de chuva."
    )
