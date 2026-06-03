"""
mavis.skills.analytics_export — gera CSV / XLSX / PDF a partir de export_rows().
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Tuple


# ---------- CSV ----------
def to_csv(rows: List[Dict[str, Any]]) -> bytes:
    if not rows:
        return "data,km,visitas,unidades\n".encode("utf-8-sig")
    fieldnames = list(rows[0].keys())
    buf = io.StringIO()
    # BOM p/ Excel reconhecer acentos
    writer = csv.DictWriter(buf, fieldnames=fieldnames, delimiter=";")
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return buf.getvalue().encode("utf-8-sig")


# ---------- XLSX ----------
def to_xlsx(rows: List[Dict[str, Any]], kpis: Dict[str, Any] | None = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Diário"

    header_fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
    header_font = Font(bold=True, color="0A0A0A", name="Calibri", size=11)
    border = Border(*(Side(style="thin", color="DDDDDD"),) * 4)

    if rows:
        headers = list(rows[0].keys())
        ws.append(headers)
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
        for r in rows:
            ws.append([r.get(h, "") for h in headers])

        # Auto-fit aproximado
        for col_idx, h in enumerate(headers, 1):
            max_len = max([len(str(h))] + [len(str(r.get(h, ""))) for r in rows])
            ws.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 60)
    else:
        ws.append(["Sem dados no filtro selecionado."])

    # Aba KPIs
    if kpis:
        ws2 = wb.create_sheet("KPIs")
        ws2.append(["Indicador", "Valor"])
        ws2["A1"].font = header_font
        ws2["A1"].fill = header_fill
        ws2["B1"].font = header_font
        ws2["B1"].fill = header_fill
        skip = {"top_destinos", "top_equipamentos", "filtro"}
        for k, v in kpis.items():
            if k in skip:
                continue
            ws2.append([k, v])
        ws2.column_dimensions["A"].width = 32
        ws2.column_dimensions["B"].width = 24

        if kpis.get("top_destinos"):
            ws3 = wb.create_sheet("Top Destinos")
            ws3.append(["Unidade", "Visitas"])
            ws3["A1"].font = header_font
            ws3["A1"].fill = header_fill
            ws3["B1"].font = header_font
            ws3["B1"].fill = header_fill
            for d in kpis["top_destinos"]:
                ws3.append([d["unidade"], d["visitas"]])
            ws3.column_dimensions["A"].width = 48
            ws3.column_dimensions["B"].width = 12

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------- PDF ----------
def to_pdf(rows: List[Dict[str, Any]], kpis: Dict[str, Any] | None = None,
           filtro: Dict[str, Any] | None = None) -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=12 * mm, rightMargin=12 * mm,
                            topMargin=12 * mm, bottomMargin=12 * mm,
                            title="Mavis · Relatório Analytics")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], textColor=colors.HexColor("#F59E0B"),
                                  alignment=0, fontSize=18, spaceAfter=6)
    subtitle = ParagraphStyle("sub", parent=styles["Normal"], textColor=colors.HexColor("#71717a"),
                              fontSize=9, spaceAfter=10)
    section = ParagraphStyle("sec", parent=styles["Heading2"], textColor=colors.HexColor("#F59E0B"),
                             fontSize=11, spaceAfter=6, spaceBefore=10)

    story = []
    story.append(Paragraph("Mavis · Relatório Analytics", title_style))
    fstr_parts = []
    if filtro:
        if filtro.get("start"):
            fstr_parts.append(f"De {filtro['start']}")
        if filtro.get("end"):
            fstr_parts.append(f"até {filtro['end']}")
        if filtro.get("unidade"):
            fstr_parts.append(f"unidade: {filtro['unidade']}")
    fstr_parts.append(f"gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    story.append(Paragraph(" · ".join(fstr_parts), subtitle))

    if kpis:
        story.append(Paragraph("Indicadores", section))
        kpi_pairs: List[Tuple[str, Any]] = [
            ("Total KM", kpis.get("total_km", 0)),
            ("Dias úteis", kpis.get("total_dias", 0)),
            ("Média KM/dia", kpis.get("media_km_dia", 0)),
            ("Média KM/semana", kpis.get("media_km_semana", 0)),
            ("Litros estimados", kpis.get("litros_estimados", 0)),
            ("Custo combustível (R$)", kpis.get("custo_combustivel", 0)),
            ("Preventivas", kpis.get("total_preventivas", 0)),
            ("Atendimentos", kpis.get("total_atendimentos", 0)),
            ("Entregas de insumos", kpis.get("total_entregas_insumos", 0)),
            ("Trocas / substituições", kpis.get("total_trocas_equipamentos", 0)),
        ]
        # Em grid 5 colunas (label/valor pairs em colunas)
        cols = 5
        rows_kpi = []
        for i in range(0, len(kpi_pairs), cols):
            chunk = kpi_pairs[i:i + cols]
            labels = [c[0] for c in chunk]
            vals = [str(c[1]) for c in chunk]
            rows_kpi.append(labels)
            rows_kpi.append(vals)
        t = Table(rows_kpi, colWidths=[52 * mm] * cols)
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#27272a")),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#EEEEEE")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FEF3C7")),
            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#FEF3C7")),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#F59E0B")),
            ("TEXTCOLOR", (0, 3), (-1, 3), colors.HexColor("#F59E0B")),
        ]))
        story.append(t)
        story.append(Spacer(1, 4 * mm))

        # Top destinos
        td = kpis.get("top_destinos") or []
        if td:
            story.append(Paragraph("Top destinos", section))
            data = [["#", "Unidade", "Visitas"]]
            for i, d in enumerate(td, 1):
                data.append([str(i), d["unidade"], str(d["visitas"])])
            tbl = Table(data, colWidths=[10 * mm, 160 * mm, 25 * mm])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F59E0B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0A0A0A")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
                ("LINEBELOW", (0, 0), (-1, -1), 0.2, colors.HexColor("#EEEEEE")),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 4 * mm))

    if rows:
        story.append(Paragraph("Diário", section))
        headers = ["Data", "KM", "Visitas", "Unidades", "Prev.", "Atend.", "Insumos", "Trocas"]
        data = [headers]
        for r in rows:
            data.append([
                r.get("data", ""),
                str(r.get("km", "")),
                str(r.get("visitas", "")),
                (r.get("unidades", "") or "")[:80],
                str(r.get("preventivas", "")),
                str(r.get("atendimentos", "")),
                str(r.get("entregas_insumos", "")),
                str(r.get("trocas", "")),
            ])
        tbl = Table(data, colWidths=[22 * mm, 14 * mm, 16 * mm, 110 * mm, 14 * mm, 16 * mm, 18 * mm, 16 * mm],
                    repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F59E0B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0A0A0A")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.2, colors.HexColor("#EEEEEE")),
            ("ALIGN", (1, 0), (2, -1), "RIGHT"),
            ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(tbl)
    else:
        story.append(Paragraph("Sem registros para o filtro selecionado.", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()
