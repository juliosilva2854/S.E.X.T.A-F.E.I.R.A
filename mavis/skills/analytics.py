"""
mavis.skills.analytics — Extrai estatísticas dos relatórios + cruza com banco de rotas.

Parser inteligente sem gastar quota Gemini:
- Identifica datas pelas marcações 📅 DD/MM/YYYY
- Detecta unidades visitadas confrontando o texto com nomes presentes em banco_de_dados.json
- Calcula KM diário encadeando CASA → loc1 → loc2 → ... → CASA com routes_km
- Conta atividades (manutenções, atendimentos, entregas, trocas)
- Conta equipamentos trocados (manguito, Trius, P.A, glicosímetro, totem, teclado, mouse, fonte)
"""
import os
import re
import unicodedata
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple

from mavis.core.storage import read_json
from mavis.core.paths import ARQUIVO_DB_ROTAS, ARQUIVO_RELATORIOS

# Padrões
RE_DAY = re.compile(r"📅\s*(\d{2}/\d{2}/\d{4})")
RE_PERIOD = re.compile(r"(\d{2}/\d{2}/\d{4})\s*(?:a|-|até)\s*(\d{2}/\d{2}/\d{4})", re.I)

ATIVIDADES = {
    "manutencao_preventiva": ["manutenção preventiva", "manutencao preventiva", "preventiva", "atendimento preventivo"],
    "atendimento_tecnico":   ["atendimento técnico", "atendimento tecnico"],
    "entrega_insumos":       ["entrega de insumos", "entrega dos insumos", "entreguei insumos", "deixei insumos"],
    "troca_equipamento":     ["troca de", "substituí", "substituo", "substitui", "reposição", "reposicao"],
    "configuracao":          ["configurei", "configuração", "configuracao", "configurando", "zabbix"],
}

EQUIPAMENTOS = [
    "manguito", "manguto", "trius", "totem", "glicosímetro", "glicosimetro",
    "teclado", "mouse", "fonte", "oxímetro", "oximetro", "termômetro", "termometro",
    "impressora", "computador", "monitor", "aparelho de p.a", "aparelho de pa",
    "bomba", "pino", "fechadura", "cabo",
]


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _normalize(s: str) -> str:
    return _strip_accents(s.lower()).strip()


def _unidades_known() -> List[str]:
    """Extrai lista de unidades únicas presentes nas chaves do banco de rotas."""
    db = read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
    rotas = db.get("rotas_km", {})
    nomes = set()
    for chave in rotas.keys():
        if "_" in chave:
            o, d = chave.split("_", 1)
            nomes.add(o.strip().upper())
            nomes.add(d.strip().upper())
        else:
            nomes.add(chave.strip().upper())
    # Filtra "CASA" e similares (são origem padrão)
    nomes.discard("CASA")
    nomes.discard("")
    # Ordena por tamanho desc para casar "UPA DR. AUGUSTO GOMES DE MATTOS" antes de "UPA"
    return sorted(nomes, key=len, reverse=True)


def _km_between(origem: str, destino: str) -> float:
    """Procura origem→destino, ou destino→origem (assume simétrico), ou 25km fallback."""
    db = read_json(ARQUIVO_DB_ROTAS, {"rotas_km": {}})
    rotas = db.get("rotas_km", {})
    o = origem.upper().strip()
    d = destino.upper().strip()
    if o == d:
        return 0.0
    for key in [f"{o}_{d}", f"{d}_{o}"]:
        if key in rotas:
            return float(rotas[key])
    return 0.0  # 0 quando desconhecido (não chuta)


def _detect_locations(text: str, unidades: List[str]) -> List[str]:
    """Detecta quais unidades aparecem no texto, na ordem de aparição.
    Evita substrings: se 'UPA VILA MARIANA' bateu, não conta 'VILA MARIANA' separadamente.
    Normaliza versões com/sem acento (deduplica pela forma sem acento)."""
    tnorm = _normalize(text)
    achados: List[Tuple[int, str, str]] = []  # (idx, original, normalizado)
    intervalos_ocupados: List[Tuple[int, int]] = []
    seen_norm = set()
    # Ordenado por tamanho desc (já vem assim)
    for u in unidades:
        unorm = _normalize(u)
        if not unorm or len(unorm) < 5:
            continue
        if unorm in seen_norm:
            continue
        idx = tnorm.find(unorm)
        if idx < 0:
            continue
        end = idx + len(unorm)
        # Verifica se sobrepõe alguém já achado (maior)
        sobrepoe = any(not (end <= a or idx >= b) for a, b in intervalos_ocupados)
        if sobrepoe:
            continue
        intervalos_ocupados.append((idx, end))
        achados.append((idx, u, unorm))
        seen_norm.add(unorm)
    achados.sort(key=lambda x: x[0])
    return [u for _, u, _ in achados]


def _activities(text: str) -> Dict[str, int]:
    t = _normalize(text)
    out = {}
    for cat, palavras in ATIVIDADES.items():
        c = 0
        for p in palavras:
            c += t.count(_normalize(p))
        if c:
            out[cat] = c
    return out


def _equipments(text: str) -> Dict[str, int]:
    t = _normalize(text)
    out = Counter()
    for eq in EQUIPAMENTOS:
        c = t.count(_normalize(eq))
        if c:
            # Normaliza "manguto"->"manguito"
            key = "manguito" if eq in ("manguito", "manguto") else eq
            key = "glicosimetro" if "glico" in key else key
            key = "termometro" if "termom" in key else key
            key = "aparelho_pa" if "aparelho" in key else key
            out[key] += c
    return dict(out)


def parse_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """Parseia um relatório em estrutura por dia."""
    unidades = _unidades_known()
    conteudo = report.get("conteudo_relatorio", "")
    if "503 UNAVAILABLE" in conteudo or "houve falha" in conteudo.lower():
        return {"id": report.get("id"), "periodo": report.get("periodo"), "days": [], "skipped": True}

    # Divide por marcador de dia
    matches = list(RE_DAY.finditer(conteudo))
    days = []
    for i, m in enumerate(matches):
        date_str = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(conteudo)
        block = conteudo[start:end]

        locs = _detect_locations(block, unidades)
        # KM diário: CASA → loc1 → ... → CASA
        km = 0.0
        if locs:
            km += _km_between("CASA", locs[0])
            for j in range(len(locs) - 1):
                km += _km_between(locs[j], locs[j + 1])
            km += _km_between(locs[-1], "CASA")

        days.append({
            "date": date_str,
            "locations": locs,
            "km": round(km, 1),
            "activities": _activities(block),
            "equipments": _equipments(block),
        })

    return {
        "id": report.get("id"),
        "periodo": report.get("periodo"),
        "gerado_em": report.get("gerado_em", ""),
        "days": days,
    }


def parse_all() -> List[Dict[str, Any]]:
    reports = read_json(ARQUIVO_RELATORIOS, [])
    return [parse_report(r) for r in reports]


# ==============================================================
# Agregações
# ==============================================================
def _to_date(s: str) -> datetime:
    return datetime.strptime(s, "%d/%m/%Y")


def _week_key(d: datetime) -> str:
    iso = d.isocalendar()
    return f"{iso.year}-S{iso.week:02d}"


def _month_key(d: datetime) -> str:
    return d.strftime("%Y-%m")


def _flat_days(parsed: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Achata em lista de dias únicos (último parse ganha em caso de dup)."""
    by_date: Dict[str, Dict[str, Any]] = {}
    for r in parsed:
        for d in r.get("days", []):
            by_date[d["date"]] = d
    out = list(by_date.values())
    out.sort(key=lambda x: _to_date(x["date"]))
    return out


def kpis(fuel_cost_per_liter: float = 5.89, km_per_liter: float = 10.0) -> Dict[str, Any]:
    parsed = parse_all()
    days = _flat_days(parsed)
    total_km = sum(d["km"] for d in days)
    total_atendimentos = 0
    total_preventivas = 0
    total_entregas = 0
    total_trocas = 0
    eq_counter = Counter()
    loc_counter = Counter()
    for d in days:
        a = d.get("activities", {})
        total_atendimentos += a.get("atendimento_tecnico", 0)
        total_preventivas += a.get("manutencao_preventiva", 0)
        total_entregas += a.get("entrega_insumos", 0)
        total_trocas += a.get("troca_equipamento", 0)
        for k, v in (d.get("equipments") or {}).items():
            eq_counter[k] += v
        for loc in d.get("locations", []):
            loc_counter[loc] += 1

    dias_trabalhados = len(days)
    semanas = len({_week_key(_to_date(d["date"])) for d in days})
    meses = len({_month_key(_to_date(d["date"])) for d in days})
    media_km_dia = round(total_km / dias_trabalhados, 1) if dias_trabalhados else 0
    media_km_semana = round(total_km / semanas, 1) if semanas else 0
    litros = total_km / km_per_liter if km_per_liter > 0 else 0
    custo_combustivel = litros * fuel_cost_per_liter

    return {
        "total_km": round(total_km, 1),
        "total_dias": dias_trabalhados,
        "total_semanas": semanas,
        "total_meses": meses,
        "media_km_dia": media_km_dia,
        "media_km_semana": media_km_semana,
        "total_atendimentos": total_atendimentos,
        "total_preventivas": total_preventivas,
        "total_entregas_insumos": total_entregas,
        "total_trocas_equipamentos": total_trocas,
        "litros_estimados": round(litros, 1),
        "custo_combustivel": round(custo_combustivel, 2),
        "fuel_cost_per_liter": fuel_cost_per_liter,
        "km_per_liter": km_per_liter,
        "top_destinos": [{"unidade": u, "visitas": c} for u, c in loc_counter.most_common(10)],
        "top_equipamentos": [{"item": e, "qtd": c} for e, c in eq_counter.most_common(8)],
        "ultimo_dia": days[-1]["date"] if days else None,
        "primeiro_dia": days[0]["date"] if days else None,
    }


def weekly_series(weeks: int = 12) -> List[Dict[str, Any]]:
    parsed = parse_all()
    days = _flat_days(parsed)
    by_week: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"km": 0.0, "visitas": 0, "dias_uteis": 0, "preventivas": 0, "atendimentos": 0})
    for d in days:
        wk = _week_key(_to_date(d["date"]))
        by_week[wk]["km"] += d["km"]
        by_week[wk]["visitas"] += len(d.get("locations", []))
        by_week[wk]["dias_uteis"] += 1
        a = d.get("activities", {})
        by_week[wk]["preventivas"] += a.get("manutencao_preventiva", 0)
        by_week[wk]["atendimentos"] += a.get("atendimento_tecnico", 0)
    out = sorted(by_week.items(), key=lambda x: x[0])[-weeks:]
    return [{"semana": k, **{kk: round(v, 1) if isinstance(v, float) else v for kk, v in val.items()}}
            for k, val in out]


def monthly_series(months: int = 12) -> List[Dict[str, Any]]:
    parsed = parse_all()
    days = _flat_days(parsed)
    by_month: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"km": 0.0, "visitas": 0, "dias_uteis": 0,
                                                                "preventivas": 0, "atendimentos": 0,
                                                                "entregas": 0, "trocas": 0, "locs": Counter()})
    for d in days:
        mk = _month_key(_to_date(d["date"]))
        by_month[mk]["km"] += d["km"]
        by_month[mk]["visitas"] += len(d.get("locations", []))
        by_month[mk]["dias_uteis"] += 1
        a = d.get("activities", {})
        by_month[mk]["preventivas"] += a.get("manutencao_preventiva", 0)
        by_month[mk]["atendimentos"] += a.get("atendimento_tecnico", 0)
        by_month[mk]["entregas"] += a.get("entrega_insumos", 0)
        by_month[mk]["trocas"] += a.get("troca_equipamento", 0)
        for loc in d.get("locations", []):
            by_month[mk]["locs"][loc] += 1
    out = sorted(by_month.items(), key=lambda x: x[0])[-months:]
    final = []
    for k, val in out:
        top_locs = val["locs"].most_common(3)
        final.append({
            "mes": k,
            "km": round(val["km"], 1),
            "visitas": val["visitas"],
            "dias_uteis": val["dias_uteis"],
            "preventivas": val["preventivas"],
            "atendimentos": val["atendimentos"],
            "entregas": val["entregas"],
            "trocas": val["trocas"],
            "top3_destinos": [{"unidade": u, "visitas": c} for u, c in top_locs],
        })
    return final


def daily_series(days_window: int = 60) -> List[Dict[str, Any]]:
    parsed = parse_all()
    days = _flat_days(parsed)[-days_window:]
    return [{
        "date": d["date"],
        "km": d["km"],
        "visitas": len(d.get("locations", [])),
        "locations": d.get("locations", []),
    } for d in days]


def heatmap_weekday() -> Dict[str, Any]:
    """Distribui KM/atividade por dia da semana (mapa de calor: seg-sex)."""
    parsed = parse_all()
    days = _flat_days(parsed)
    weekdays = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]
    by_wd: Dict[int, Dict[str, float]] = {i: {"km": 0.0, "dias": 0, "visitas": 0} for i in range(7)}
    for d in days:
        dt = _to_date(d["date"])
        wd = dt.weekday()
        by_wd[wd]["km"] += d["km"]
        by_wd[wd]["dias"] += 1
        by_wd[wd]["visitas"] += len(d.get("locations", []))
    return [
        {
            "dia": weekdays[i],
            "km": round(by_wd[i]["km"], 1),
            "dias": by_wd[i]["dias"],
            "visitas": by_wd[i]["visitas"],
            "media_km": round(by_wd[i]["km"] / by_wd[i]["dias"], 1) if by_wd[i]["dias"] else 0,
        }
        for i in range(7)
    ]


def activity_distribution() -> List[Dict[str, Any]]:
    parsed = parse_all()
    days = _flat_days(parsed)
    counter = Counter()
    for d in days:
        for k, v in d.get("activities", {}).items():
            counter[k] += v
    labels = {
        "manutencao_preventiva": "Manutenções preventivas",
        "atendimento_tecnico": "Atendimentos técnicos",
        "entrega_insumos": "Entregas de insumos",
        "troca_equipamento": "Trocas / substituições",
        "configuracao": "Configurações / Zabbix",
    }
    return [{"tipo": labels.get(k, k), "qtd": v} for k, v in counter.most_common()]


# ==============================================================
# FILTROS + MAP DATA + EXPORT
# ==============================================================
def _parse_iso_or_br(s: str) -> datetime:
    """Aceita 'YYYY-MM-DD' ou 'DD/MM/YYYY'."""
    if not s:
        return None  # type: ignore
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None  # type: ignore


def filtered_days(start: str = "", end: str = "", unidade: str = "") -> List[Dict[str, Any]]:
    """Retorna a lista de dias (achatada) filtrada por intervalo e unidade.
    - start/end: 'YYYY-MM-DD' ou 'DD/MM/YYYY'
    - unidade: substring (normalizada) que deve aparecer em qualquer location do dia.
    """
    parsed = parse_all()
    days = _flat_days(parsed)
    dt_start = _parse_iso_or_br(start) if start else None
    dt_end = _parse_iso_or_br(end) if end else None
    unorm = _normalize(unidade) if unidade else ""

    out = []
    for d in days:
        dt = _to_date(d["date"])
        if dt_start and dt < dt_start:
            continue
        if dt_end and dt > dt_end:
            continue
        if unorm:
            locs_norm = [_normalize(l) for l in d.get("locations", [])]
            if not any(unorm in ln for ln in locs_norm):
                continue
        out.append(d)
    return out


def unidades_list() -> List[str]:
    """Lista única de unidades que JÁ apareceram nos relatórios (não só no banco)."""
    parsed = parse_all()
    days = _flat_days(parsed)
    seen = Counter()
    for d in days:
        for loc in d.get("locations", []):
            seen[loc] += 1
    return [u for u, _ in seen.most_common()]


def kpis_filtered(
    start: str = "", end: str = "", unidade: str = "",
    fuel_cost_per_liter: float = 5.89, km_per_liter: float = 10.0,
) -> Dict[str, Any]:
    """Mesmo formato de kpis() porém aplicando filtros."""
    days = filtered_days(start, end, unidade)
    total_km = sum(d["km"] for d in days)
    total_atendimentos = 0
    total_preventivas = 0
    total_entregas = 0
    total_trocas = 0
    eq_counter = Counter()
    loc_counter = Counter()
    for d in days:
        a = d.get("activities", {})
        total_atendimentos += a.get("atendimento_tecnico", 0)
        total_preventivas += a.get("manutencao_preventiva", 0)
        total_entregas += a.get("entrega_insumos", 0)
        total_trocas += a.get("troca_equipamento", 0)
        for k, v in (d.get("equipments") or {}).items():
            eq_counter[k] += v
        for loc in d.get("locations", []):
            loc_counter[loc] += 1

    dias_trabalhados = len(days)
    semanas = len({_week_key(_to_date(d["date"])) for d in days})
    meses = len({_month_key(_to_date(d["date"])) for d in days})
    media_km_dia = round(total_km / dias_trabalhados, 1) if dias_trabalhados else 0
    media_km_semana = round(total_km / semanas, 1) if semanas else 0
    litros = total_km / km_per_liter if km_per_liter > 0 else 0
    custo_combustivel = litros * fuel_cost_per_liter

    return {
        "total_km": round(total_km, 1),
        "total_dias": dias_trabalhados,
        "total_semanas": semanas,
        "total_meses": meses,
        "media_km_dia": media_km_dia,
        "media_km_semana": media_km_semana,
        "total_atendimentos": total_atendimentos,
        "total_preventivas": total_preventivas,
        "total_entregas_insumos": total_entregas,
        "total_trocas_equipamentos": total_trocas,
        "litros_estimados": round(litros, 1),
        "custo_combustivel": round(custo_combustivel, 2),
        "fuel_cost_per_liter": fuel_cost_per_liter,
        "km_per_liter": km_per_liter,
        "top_destinos": [{"unidade": u, "visitas": c} for u, c in loc_counter.most_common(10)],
        "top_equipamentos": [{"item": e, "qtd": c} for e, c in eq_counter.most_common(8)],
        "ultimo_dia": days[-1]["date"] if days else None,
        "primeiro_dia": days[0]["date"] if days else None,
        "filtro": {"start": start, "end": end, "unidade": unidade},
    }


def weekly_filtered(start: str = "", end: str = "", unidade: str = "", weeks: int = 12) -> List[Dict[str, Any]]:
    days = filtered_days(start, end, unidade)
    by_week: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"km": 0.0, "visitas": 0, "dias_uteis": 0,
                                                              "preventivas": 0, "atendimentos": 0})
    for d in days:
        wk = _week_key(_to_date(d["date"]))
        by_week[wk]["km"] += d["km"]
        by_week[wk]["visitas"] += len(d.get("locations", []))
        by_week[wk]["dias_uteis"] += 1
        a = d.get("activities", {})
        by_week[wk]["preventivas"] += a.get("manutencao_preventiva", 0)
        by_week[wk]["atendimentos"] += a.get("atendimento_tecnico", 0)
    out = sorted(by_week.items(), key=lambda x: x[0])[-weeks:]
    return [{"semana": k, **{kk: round(v, 1) if isinstance(v, float) else v for kk, v in val.items()}}
            for k, val in out]


def activity_filtered(start: str = "", end: str = "", unidade: str = "") -> List[Dict[str, Any]]:
    days = filtered_days(start, end, unidade)
    counter = Counter()
    for d in days:
        for k, v in d.get("activities", {}).items():
            counter[k] += v
    labels = {
        "manutencao_preventiva": "Manutenções preventivas",
        "atendimento_tecnico": "Atendimentos técnicos",
        "entrega_insumos": "Entregas de insumos",
        "troca_equipamento": "Trocas / substituições",
        "configuracao": "Configurações / Zabbix",
    }
    return [{"tipo": labels.get(k, k), "qtd": v} for k, v in counter.most_common()]


def map_data(start: str = "", end: str = "", unidade: str = "", allow_remote: bool = True) -> Dict[str, Any]:
    """Retorna dados para o mapa de calor geográfico.

    Estrutura:
      {
        "center": [lat, lng],
        "points": [{"lat": .., "lng": .., "weight": .., "unidade": .., "visitas": ..,
                    "km_total": ..}, ...],
        "unresolved": ["UPA X NAO ACHADA", ...],
        "total_visitas": int,
        "total_unidades": int
      }
    """
    from mavis.skills import geocoding as geo
    days = filtered_days(start, end, unidade)

    loc_counter: Counter = Counter()
    loc_km: Dict[str, float] = defaultdict(float)
    for d in days:
        locs = d.get("locations", [])
        if not locs:
            continue
        # Distribui o KM do dia igualmente entre as unidades visitadas no dia
        share = d["km"] / len(locs) if locs else 0.0
        for loc in locs:
            loc_counter[loc] += 1
            loc_km[loc] += share

    points = []
    unresolved = []
    max_visits = max(loc_counter.values()) if loc_counter else 1
    for loc, visitas in loc_counter.most_common():
        coords = geo.geocode(loc, allow_remote=allow_remote)
        if coords is None:
            unresolved.append(loc)
            continue
        lat, lng = coords
        points.append({
            "lat": lat,
            "lng": lng,
            "weight": round(visitas / max_visits, 4),
            "unidade": loc,
            "visitas": visitas,
            "km_total": round(loc_km[loc], 1),
        })

    return {
        "center": list(geo.get_center()),
        "points": points,
        "unresolved": unresolved,
        "total_visitas": sum(loc_counter.values()),
        "total_unidades": len(loc_counter),
        "filtro": {"start": start, "end": end, "unidade": unidade},
    }


def export_rows(start: str = "", end: str = "", unidade: str = "") -> List[Dict[str, Any]]:
    """Linhas tabulares prontas para exportação."""
    days = filtered_days(start, end, unidade)
    rows = []
    for d in days:
        a = d.get("activities", {})
        e = d.get("equipments", {})
        rows.append({
            "data": d["date"],
            "km": d["km"],
            "visitas": len(d.get("locations", [])),
            "unidades": " → ".join(d.get("locations", [])),
            "preventivas": a.get("manutencao_preventiva", 0),
            "atendimentos": a.get("atendimento_tecnico", 0),
            "entregas_insumos": a.get("entrega_insumos", 0),
            "trocas": a.get("troca_equipamento", 0),
            "configuracoes": a.get("configuracao", 0),
            "equipamentos": ", ".join(f"{k}:{v}" for k, v in e.items()) if e else "",
        })
    return rows


def month_detail(month_str: str) -> Dict[str, Any]:
    """Detalhe de um mês específico (YYYY-MM)."""
    parsed = parse_all()
    days = [d for d in _flat_days(parsed) if _month_key(_to_date(d["date"])) == month_str]
    if not days:
        return {"error": "mês sem dados", "month": month_str}
    total_km = sum(d["km"] for d in days)
    loc_counter = Counter()
    eq_counter = Counter()
    act_counter = Counter()
    for d in days:
        for loc in d.get("locations", []):
            loc_counter[loc] += 1
        for e, c in (d.get("equipments") or {}).items():
            eq_counter[e] += c
        for a, c in (d.get("activities") or {}).items():
            act_counter[a] += c
    return {
        "month": month_str,
        "total_km": round(total_km, 1),
        "dias_trabalhados": len(days),
        "media_km_dia": round(total_km / len(days), 1),
        "top_destinos": [{"unidade": u, "visitas": c} for u, c in loc_counter.most_common(10)],
        "top_equipamentos": [{"item": e, "qtd": c} for e, c in eq_counter.most_common(8)],
        "atividades": dict(act_counter),
        "days": days,
    }
