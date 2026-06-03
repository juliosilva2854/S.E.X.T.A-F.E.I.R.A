"""
mavis.skills.geocoding — geocoding leve com cache JSON + seed manual.

Objetivo:
- Resolver nomes de unidades (UPA, AMA, hospitais, etc.) para coordenadas (lat, lng)
- Usar cache local em /app/data/geocode_cache.json para não estourar rate-limit do Nominatim
- Seed com coordenadas conhecidas das principais unidades da Grande SP
- Fallback inteligente: tenta Nominatim só se não estiver no cache E se internet estiver disponível
"""
from __future__ import annotations

import json
import os
import time
import unicodedata
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import requests

from mavis.core.paths import APP_ROOT

CACHE_FILE = Path(APP_ROOT) / "geocode_cache.json"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "MavisSextaFeira/3.0 (analytics dashboard)"
RATE_LIMIT_SECONDS = 1.1  # Nominatim pede 1 req/s


# Coordenadas aproximadas — São Paulo centro como fallback geral
SP_CENTER = (-23.5505, -46.6333)

# Seed manual com unidades comuns observadas no banco
# (lat, lng) — aproximações de centróide de bairro/região (fonte: OSM)
SEED_COORDS: Dict[str, Tuple[float, float]] = {
    "CASA": (-23.5505, -46.6333),
    "BOX": (-23.5489, -46.6388),
    "UPA VERA CRUZ": (-23.5870, -46.5710),
    "UPA SANTO AMARO": (-23.6562, -46.7100),
    "UPA VILA MARIANA": (-23.5878, -46.6346),
    "UPA VILA MORAES": (-23.6230, -46.5520),
    "UPA VILA NOVA SABARA": (-23.6442, -46.5234),
    "UPA SAPOPEMBA": (-23.6202, -46.5077),
    "UPA SACOMA": (-23.6125, -46.6010),
    "UPA JABAQUARA": (-23.6500, -46.6450),
    "UPA HELIOPOLIS": (-23.6235, -46.6072),
    "UPA IPIRANGA": (-23.5860, -46.6010),
    "UPA CAMPO LIMPO": (-23.6580, -46.7530),
    "UPA CAMPO BELO": (-23.6260, -46.6720),
    "UPA SAUDE": (-23.6190, -46.6390),
    "UPA AGUA RASA": (-23.5648, -46.5790),
    "UPA TATUAPE": (-23.5394, -46.5733),
    "UPA TIRADENTES": (-23.5505, -46.6333),
    "UPA PARI": (-23.5310, -46.6155),
    "UPA PIRITUBA": (-23.4825, -46.7370),
    "UPA PERUS": (-23.4007, -46.7530),
    "UPA TREMEMBE": (-23.4640, -46.5970),
    "UPA JACANA": (-23.4810, -46.5800),
    "UPA VILA NOVA CACHOEIRINHA": (-23.4775, -46.6620),
    "UPA BRASILANDIA": (-23.4570, -46.6660),
    "UPA FREGUESIA": (-23.4970, -46.6920),
    "UPA SAO MIGUEL": (-23.4980, -46.4440),
    "UPA ITAIM PAULISTA": (-23.5040, -46.4040),
    "UPA ERMELINO MATARAZZO": (-23.5005, -46.4830),
    "UPA PENHA": (-23.5310, -46.5400),
    "UPA ARICANDUVA": (-23.5670, -46.5310),
    "UPA VILA FORMOSA": (-23.5660, -46.5510),
    "UPA SAO MATEUS": (-23.6010, -46.4760),
    "UPA CIDADE TIRADENTES": (-23.5870, -46.4040),
    "UPA GUAIANASES": (-23.5390, -46.4150),
    "UPA LAJEADO": (-23.5470, -46.4220),
    "UPA CIDADE LIDER": (-23.5740, -46.4690),
    "UPA ITAQUERA": (-23.5360, -46.4570),
    "UPA JOSE BONIFACIO": (-23.5575, -46.4470),
    "UPA PARELHEIROS": (-23.8270, -46.7270),
    "UPA GRAJAU": (-23.7600, -46.6940),
    "UPA M'BOI MIRIM": (-23.7220, -46.7430),
    "UPA CAPAO REDONDO": (-23.6770, -46.7770),
    "UPA JARDIM ANGELA": (-23.7080, -46.7790),
    "UPA JARDIM SAO LUIS": (-23.6800, -46.7320),
    "UPA SOCORRO": (-23.6580, -46.7050),
    "UPA INTERLAGOS": (-23.6970, -46.6770),
    "UPA CIDADE ADEMAR": (-23.6770, -46.6470),
    "UPA PEDREIRA": (-23.6970, -46.6470),
    "UPA AMERICANOPOLIS": (-23.6620, -46.6390),
    "UPA CURSINO": (-23.6190, -46.6172),
    "UPA SAO LUCAS": (-23.6080, -46.5650),
    "UPA CARRAO": (-23.5450, -46.5460),
    "UPA CANGAIBA": (-23.5060, -46.5210),
    "UPA VILA MATILDE": (-23.5430, -46.5310),
    "UPA VILA MARIA": (-23.5060, -46.5910),
    "UPA VILA GUILHERME": (-23.5170, -46.6080),
    "UPA SANTANA": (-23.5060, -46.6260),
    "UPA CASA VERDE": (-23.5070, -46.6620),
    "UPA LIMAO": (-23.4990, -46.6695),
    "UPA BUTANTA": (-23.5715, -46.7180),
    "UPA RIO PEQUENO": (-23.5660, -46.7510),
    "UPA RAPOSO TAVARES": (-23.5870, -46.7800),
    "UPA VILA SONIA": (-23.5970, -46.7400),
    "UPA MORUMBI": (-23.6080, -46.7110),
    "UPA JAGUARE": (-23.5470, -46.7530),
    "UPA LAPA": (-23.5260, -46.7065),
    "UPA BARRA FUNDA": (-23.5260, -46.6650),
    "UPA PERDIZES": (-23.5440, -46.6740),
    "UPA POMPEIA": (-23.5285, -46.6850),
    "UPA VILA LEOPOLDINA": (-23.5380, -46.7400),
    "UPA PINHEIROS": (-23.5640, -46.6900),
    "UPA ITAIM BIBI": (-23.5860, -46.6770),
    "UPA MOEMA": (-23.5990, -46.6610),
    "UPA INDIANOPOLIS": (-23.6010, -46.6520),
    "UPA JARDINS": (-23.5760, -46.6610),
    "UPA CONSOLACAO": (-23.5530, -46.6580),
    "UPA SE": (-23.5505, -46.6333),
    "UPA REPUBLICA": (-23.5447, -46.6420),
    "UPA BELA VISTA": (-23.5610, -46.6470),
    "UPA LIBERDADE": (-23.5580, -46.6360),
    "UPA CAMBUCI": (-23.5650, -46.6240),
    "UPA MOOCA": (-23.5530, -46.6010),
    "UPA BELEM": (-23.5410, -46.6010),
    "UPA BRAS": (-23.5430, -46.6190),
    # Unidades específicas que o Nominatim não resolve (coords manuais aproximadas)
    "HM DR. FERNANDO MAURO PIRES DA ROCHA": (-23.8281, -46.7274),  # Parelheiros
    "UPA PARQUE DOROTEIA": (-23.6889, -46.6585),                   # Pedreira/Cidade Ademar
    "UPA DONA MARIA ANTONIETA FERREIRA BARROS": (-23.7062, -46.7760),  # Jardim Ângela
}


# ---------- Cache I/O ----------
def _load_cache() -> Dict[str, Any]:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(CACHE_FILE) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CACHE_FILE)
    except Exception:
        pass


# ---------- Normalização ----------
def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm_key(name: str) -> str:
    return _strip_accents((name or "").strip().upper())


# ---------- Estado em memória ----------
_LAST_REMOTE_CALL = 0.0
_MEM_CACHE: Optional[Dict[str, Any]] = None


def _ensure_cache() -> Dict[str, Any]:
    """Carrega cache do disco e mescla seed (uma vez)."""
    global _MEM_CACHE
    if _MEM_CACHE is None:
        cache = _load_cache()
        changed = False
        for name, (lat, lng) in SEED_COORDS.items():
            k = _norm_key(name)
            if k not in cache:
                cache[k] = {"lat": lat, "lng": lng, "source": "seed", "name": name}
                changed = True
        if changed:
            _save_cache(cache)
        _MEM_CACHE = cache
    return _MEM_CACHE


# Prefixos de tipo de unidade — removidos para tentar geocodificar o bairro/logradouro
_FACILITY_PREFIXES = [
    "UPA", "AMA", "AMA/UBS", "UBS", "HM", "HMI", "HOSPITAL MUNICIPAL", "HOSPITAL",
    "PA", "PS", "PSM", "PRONTO SOCORRO", "PRONTO-SOCORRO", "CAPS", "CER", "CEO",
    "AME", "DR.", "DR", "DRA.", "DRA", "PROF.", "PROF",
]


def _bbox_sp() -> str:
    # viewbox da Grande São Paulo (lon_esq, lat_topo, lon_dir, lat_baixo)
    return "-46.95,-23.30,-46.30,-23.90"


def _strip_facility(name: str) -> str:
    """Remove prefixos de tipo de unidade para sobrar o bairro/identificador."""
    s = _norm_key(name)
    changed = True
    while changed:
        changed = False
        for p in _FACILITY_PREFIXES:
            if s.startswith(p + " "):
                s = s[len(p):].strip()
                changed = True
    return s.strip()


def _query_nominatim(query: str) -> Optional[Tuple[float, float]]:
    global _LAST_REMOTE_CALL
    elapsed = time.time() - _LAST_REMOTE_CALL
    if elapsed < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - elapsed)
    _LAST_REMOTE_CALL = time.time()
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "q": query, "format": "json", "limit": 1, "countrycodes": "br",
                "viewbox": _bbox_sp(), "bounded": 1,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=5.0,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None


def _remote_lookup(name: str) -> Optional[Tuple[float, float]]:
    """Consulta Nominatim com múltiplas variações para maximizar acerto.
    1) nome completo  2) sem prefixo de unidade (bairro)  3) bairro como 'suburb'."""
    queries = [f"{name}, São Paulo, SP, Brasil"]
    bairro = _strip_facility(name)
    if bairro and bairro != _norm_key(name) and len(bairro) >= 3:
        queries.append(f"{bairro}, São Paulo, SP, Brasil")
        queries.append(f"bairro {bairro}, São Paulo, Brasil")
    for q in queries:
        coords = _query_nominatim(q)
        if coords:
            return coords
    return None


# ---------- API pública ----------
def geocode(name: str, allow_remote: bool = True) -> Optional[Tuple[float, float]]:
    """Retorna (lat, lng) para o nome dado, ou None se não conseguir resolver.
    Primeiro tenta cache (incluindo seed). Se allow_remote=True, consulta Nominatim
    e salva no cache. Em caso de fail, retorna None (não inventa)."""
    if not name or not name.strip():
        return None
    cache = _ensure_cache()
    k = _norm_key(name)
    if k in cache and isinstance(cache[k], dict) and cache[k].get("lat") is not None:
        e = cache[k]
        return float(e["lat"]), float(e["lng"])

    # Tenta match parcial: se nome contém uma chave conhecida, usa
    for known_key, entry in cache.items():
        if known_key and known_key in k and len(known_key) >= 8:
            if isinstance(entry, dict) and entry.get("lat") is not None:
                return float(entry["lat"]), float(entry["lng"])

    if not allow_remote:
        return None

    coords = _remote_lookup(name)
    if coords:
        cache[k] = {"lat": coords[0], "lng": coords[1], "source": "nominatim", "name": name}
        _save_cache(cache)
        return coords

    # Marca como tentado para não bater de novo
    cache[k] = {"lat": None, "lng": None, "source": "failed", "name": name}
    _save_cache(cache)
    return None


def geocode_many(names, allow_remote: bool = True) -> Dict[str, Tuple[float, float]]:
    """Retorna dict {name_original: (lat, lng)} apenas para nomes resolvidos."""
    out: Dict[str, Tuple[float, float]] = {}
    for n in names:
        c = geocode(n, allow_remote=allow_remote)
        if c:
            out[n] = c
    return out


def get_center() -> Tuple[float, float]:
    """Centro padrão para o mapa (São Paulo)."""
    return SP_CENTER
