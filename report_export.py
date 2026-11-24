"""
Génération des rapports de campagne SmilePhish dans 4 formats :
Excel (.xlsx), Word (.docx), PDF, HTML autonome.

Chaque rapport contient : les statistiques globales (nombre + pourcentage) et le détail
nominatif par destinataire avec la date/heure exacte de chaque action et un statut
synthétique de l'action.
"""

import io
from datetime import datetime

# Couleurs de marque SmilePhish (bleu / rouge)
NAVY = "0B2A6B"     # bleu profond (anciennement "navy", conservé comme couleur de texte/titre)
VIOLET = "2563EB"   # bleu principal (anciennement "violet", conservé pour les séries/accents)
GOLD = "DC2626"      # rouge principal (anciennement "gold", conservé pour les alertes/accents 2)
ROSE = "EF4444"      # rouge clair (anciennement "rose", conservé pour l'accent critique)
TEAL = "1D4ED8"      # bleu secondaire (anciennement "teal", conservé pour l'accent "envoyé")
LIGHT_BG = "F3F6FD"


def _now_fmt():
    return datetime.now().strftime("%d/%m/%Y à %H:%M")


def _chart_labels_values(stats):
    labels = ["Envoyés", "Rejetés", "Ouverts", "Cliqués", "Soumis"]
    values = [stats["sent"], stats["rejected"], stats["opened"], stats["clicked"], stats["submitted"]]
    pcts = [stats["pct_sent"], stats["pct_rejected"], stats["pct_opened"], stats["pct_clicked"], stats["pct_submitted"]]
    # Bleu (envoyé) -> rouge (soumis) : plus l'action est risquée, plus elle tire vers le rouge.
    colors_hex = ["#1D4ED8", "#EF4444", "#2563EB", "#F97316", "#DC2626"]
    return labels, values, pcts, colors_hex


def _build_chart_png(stats, title="Répartition des actions de la campagne"):
    """Génère le graphique en barres des statistiques en PNG (matplotlib),
    utilisé pour l'intégrer dans les rapports Word et PDF."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels, values, pcts, colors_hex = _chart_labels_values(stats)

    fig, ax = plt.subplots(figsize=(7, 3.6), dpi=160)
    bars = ax.bar(labels, values, color=colors_hex, width=0.55, zorder=3)

    for bar, v, p in zip(bars, values, pcts):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height(),
            f"{v}\n({p}%)",
            ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#1B1548",
        )

    ax.set_title(title, fontsize=12.5, fontweight="bold", color="#1B1548", pad=14)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#E7E4F4")
    ax.spines["bottom"].set_color("#E7E4F4")
    ax.tick_params(colors="#716E91", labelsize=10)
    ax.set_ylim(0, max(values + [1]) * 1.28)
    ax.grid(axis="y", color="#E7E4F4", linewidth=0.8, zorder=0)
    ax.set_facecolor("#FFFFFF")
    fig.patch.set_facecolor("#FFFFFF")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _build_chart_svg(stats, width=640, height=320):
    """Génère un graphique en barres en SVG pur (sans dépendance JS/CDN) pour le
    rapport HTML autonome, dans les couleurs de marque SmilePhish."""
    labels, values, pcts, colors_hex = _chart_labels_values(stats)
    max_val = max(values + [1])

    pad_left, pad_bottom, pad_top = 46, 50, 30
    chart_w = width - pad_left - 20
    chart_h = height - pad_bottom - pad_top
    n = len(values)
    gap = 26
    bar_w = (chart_w - gap * (n - 1)) / n

    bars_svg = []
    labels_svg = []
    grid_svg = []

    # Lignes de grille horizontales (0%, 25%, 50%, 75%, 100% de l'échelle)
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        y = pad_top + chart_h * (1 - frac)
        grid_svg.append(
            f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - 20}" y2="{y:.1f}" '
            f'stroke="#E7E4F4" stroke-width="1" />'
        )

    for i, (label, v, p, color) in enumerate(zip(labels, values, pcts, colors_hex)):
        bar_h = (v / max_val) * chart_h if max_val else 0
        x = pad_left + i * (bar_w + gap)
        y = pad_top + chart_h - bar_h
        bars_svg.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" '
            f'rx="6" fill="{color}" />'
        )
        bars_svg.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{y - 10:.1f}" text-anchor="middle" '
            f'font-size="13" font-weight="700" fill="#1B1548">{v}</text>'
        )
        bars_svg.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{y + 6:.1f}" text-anchor="middle" '
            f'font-size="10.5" font-weight="700" fill="#FFFFFF">{p}%</text>'
            if bar_h > 20 else ""
        )
        labels_svg.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - pad_bottom + 22:.1f}" text-anchor="middle" '
            f'font-size="12" font-weight="600" fill="#716E91">{label}</text>'
        )

    svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;">
      <rect x="0" y="0" width="{width}" height="{height}" fill="#FFFFFF" rx="14" />
      {''.join(grid_svg)}
      {''.join(bars_svg)}
      {''.join(labels_svg)}
    </svg>"""
    return svg


# ---------------------------------------------------------------------------
# EXCEL (.xlsx) — openpyxl
# ---------------------------------------------------------------------------
def build_xlsx(campaign, stats, rows):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()

    # ---- Feuille 1 : Résumé ----
    ws = wb.active
    ws.title = "Résumé"
    ws.sheet_view.showGridLines = False

    title_font = Font(name="Calibri", size=18, bold=True, color=NAVY)
    sub_font = Font(name="Calibri", size=11, color="716E91")
    header_fill = PatternFill("solid", fgColor=NAVY)
    header_font = Font(color="FFFFFF", bold=True)
    gold_fill = PatternFill("solid", fgColor=GOLD)

    ws.merge_cells("A1:D1")
    ws["A1"] = "SmilePhish — Rapport de simulation de phishing"
    ws["A1"].font = title_font

    ws.merge_cells("A2:D2")
    ws["A2"] = f"{campaign['name']} — généré le {_now_fmt()}"
    ws["A2"].font = sub_font

    ws["A4"] = "Entreprise cliente"
    ws["B4"] = campaign.get("organisation_name", "") if hasattr(campaign, "get") else ""
    ws["A5"] = "Objet de l'email"
    ws["B5"] = campaign["subject"]
    ws["A6"] = "Expéditeur"
    ws["B6"] = f"{campaign['sender_name']} <{campaign['sender_email']}>"
    ws["A7"] = "Date de création"
    ws["B7"] = campaign["created_at"][:16].replace("T", " ")
    for r in (4, 5, 6, 7):
        ws[f"A{r}"].font = Font(bold=True, color=NAVY)

    headers = ["Indicateur", "Nombre", "Pourcentage"]
    start_row = 9
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=start_row, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    metrics = [
        ("Cibles totales", stats["total"], ""),
        ("Emails envoyés", stats["sent"], f"{stats['pct_sent']}%"),
        ("Emails rejetés", stats["rejected"], f"{stats['pct_rejected']}%"),
        ("Emails ouverts", stats["opened"], f"{stats['pct_opened']}%"),
        ("Liens cliqués", stats["clicked"], f"{stats['pct_clicked']}%"),
        ("Ont répondu / soumis", stats["submitted"], f"{stats['pct_submitted']}%"),
    ]
    row_colors = [None, TEAL, ROSE, GOLD, ROSE, ROSE]
    for i, (label, n, pct) in enumerate(metrics, start=1):
        r = start_row + i
        ws.cell(row=r, column=1, value=label).font = Font(bold=True)
        ws.cell(row=r, column=2, value=n).alignment = Alignment(horizontal="center")
        ws.cell(row=r, column=3, value=pct).alignment = Alignment(horizontal="center")

    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 16

    # ---- Graphique natif Excel (modifiable, basé sur les cellules du tableau) ----
    from openpyxl.chart import BarChart, Reference
    from openpyxl.chart.label import DataLabelList

    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Répartition des actions de la campagne"
    chart.y_axis.title = "Nombre de destinataires"
    chart.x_axis.title = None
    chart.height = 9
    chart.width = 17
    chart.gapWidth = 60

    data_first_row = start_row + 2   # "Emails envoyés" (on exclut "Cibles totales")
    data_last_row = start_row + 6    # "Ont répondu / soumis"
    data_ref = Reference(ws, min_col=2, min_row=data_first_row, max_row=data_last_row)
    cats_ref = Reference(ws, min_col=1, min_row=data_first_row, max_row=data_last_row)
    chart.add_data(data_ref, titles_from_data=False)
    chart.set_categories(cats_ref)
    chart.dataLabels = DataLabelList()
    chart.dataLabels.showVal = True
    chart.legend = None

    series = chart.series[0]
    series.graphicalProperties.solidFill = VIOLET

    ws.add_chart(chart, "E8")

    # ---- Feuille 2 : Détail par destinataire ----
    ws2 = wb.create_sheet("Détail par destinataire")
    ws2.sheet_view.showGridLines = False

    cols = [
        "Email", "Prénom", "Nom", "Service", "Statut envoi",
        "Email ouvert", "Date/heure ouverture",
        "Lien cliqué", "Date/heure clic",
        "Formulaire soumis", "Date/heure soumission",
        "Dernière action",
    ]
    for col, h in enumerate(cols, start=1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)

    yes_fill = PatternFill("solid", fgColor="FFE3E9")
    no_fill = PatternFill("solid", fgColor="E3FBF6")

    for i, r in enumerate(rows, start=2):
        values = [
            r["email"], r["first_name"], r["last_name"], r["department"], r["status"],
            "Oui" if r["opened"] else "Non", r["opened_at_fmt"] or "-",
            "Oui" if r["clicked"] else "Non", r["clicked_at_fmt"] or "-",
            "Oui" if r["submitted"] else "Non", r["submitted_at_fmt"] or "-",
            r["last_action"],
        ]
        for col, v in enumerate(values, start=1):
            cell = ws2.cell(row=i, column=col, value=v)
            if col in (6, 8, 10):
                cell.fill = yes_fill if v == "Oui" else no_fill
                cell.alignment = Alignment(horizontal="center")

    widths = [26, 12, 12, 14, 11, 11, 18, 11, 18, 14, 18, 30]
    for col, w in enumerate(widths, start=1):
        ws2.column_dimensions[get_column_letter(col)].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# WORD (.docx) — python-docx
# ---------------------------------------------------------------------------
def build_docx(campaign, stats, rows):
    from docx import Document
    from docx.shared import Pt, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    def set_cell_bg(cell, hex_color):
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), hex_color)
        tc_pr.append(shd)

    doc = Document()

    # Titre
    title = doc.add_heading(level=0)
    run = title.add_run("SmilePhish")
    run.font.color.rgb = RGBColor.from_string(NAVY)
    sub = doc.add_paragraph()
    sub_run = sub.add_run("Rapport de simulation de phishing — sensibilisation à la sécurité")
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = RGBColor.from_string("716E91")

    doc.add_paragraph(f"Entreprise cliente : {campaign.get('organisation_name', '')}")
    doc.add_paragraph(f"Campagne : {campaign['name']}")
    doc.add_paragraph(f"Objet de l'email testé : {campaign['subject']}")
    doc.add_paragraph(f"Expéditeur : {campaign['sender_name']} <{campaign['sender_email']}>")
    doc.add_paragraph(f"Date de création : {campaign['created_at'][:16].replace('T', ' ')}")
    doc.add_paragraph(f"Rapport généré le {_now_fmt()}")

    doc.add_heading("Résumé statistique", level=1)
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text, hdr[2].text = "Indicateur", "Nombre", "Pourcentage"
    for c in hdr:
        set_cell_bg(c, NAVY)
        for p in c.paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor.from_string("FFFFFF")
                r.font.bold = True

    metrics = [
        ("Cibles totales", stats["total"], "-"),
        ("Emails envoyés", stats["sent"], f"{stats['pct_sent']}%"),
        ("Emails rejetés", stats["rejected"], f"{stats['pct_rejected']}%"),
        ("Emails ouverts", stats["opened"], f"{stats['pct_opened']}%"),
        ("Liens cliqués", stats["clicked"], f"{stats['pct_clicked']}%"),
        ("Ont répondu / soumis", stats["submitted"], f"{stats['pct_submitted']}%"),
    ]
    for label, n, pct in metrics:
        row = table.add_row().cells
        row[0].text, row[1].text, row[2].text = label, str(n), str(pct)

    doc.add_heading("Graphique de répartition", level=1)
    chart_buf = _build_chart_png(stats)
    doc.add_picture(chart_buf, width=Cm(15.5))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_heading("Détail nominatif par destinataire", level=1)
    doc.add_paragraph(
        "Chaque ligne indique la date et l'heure exactes de la dernière action réalisée "
        "par le destinataire, utile pour la sensibilisation individuelle."
    )

    cols = ["Email", "Nom", "Service", "Email ouvert", "Lien cliqué", "Soumis", "Dernière action (date/heure)"]
    dtable = doc.add_table(rows=1, cols=len(cols))
    dtable.style = "Light Grid Accent 1"
    for i, h in enumerate(cols):
        cell = dtable.rows[0].cells[i]
        cell.text = h
        set_cell_bg(cell, NAVY)
        for p in cell.paragraphs:
            for r in p.runs:
                r.font.color.rgb = RGBColor.from_string("FFFFFF")
                r.font.bold = True
                r.font.size = Pt(9)

    for r in rows:
        row = dtable.add_row().cells
        row[0].text = r["email"]
        row[1].text = f"{r['first_name']} {r['last_name']}".strip()
        row[2].text = r["department"] or ""
        row[3].text = f"Oui ({r['opened_at_fmt']})" if r["opened"] else "Non"
        row[4].text = f"Oui ({r['clicked_at_fmt']})" if r["clicked"] else "Non"
        row[5].text = f"Oui ({r['submitted_at_fmt']})" if r["submitted"] else "Non"
        row[6].text = f"{r['last_action']} — {r['last_action_at_fmt'] or '-'}"
        for cell in row:
            for p in cell.paragraphs:
                for run_ in p.runs:
                    run_.font.size = Pt(9)

    doc.add_heading("Recommandations", level=1)
    doc.add_paragraph(
        "Il est recommandé d'organiser une session de sensibilisation ciblée pour les "
        "collaborateurs ayant cliqué sur le lien et/ou soumis le formulaire de test, "
        "en s'appuyant sur les éléments factuels ci-dessus (date et heure de l'action)."
    )

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# PDF — reportlab
# ---------------------------------------------------------------------------
def build_pdf(campaign, stats, rows):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT

    navy = colors.HexColor("#1B1548")
    violet = colors.HexColor("#7C5CFF")
    gold = colors.HexColor("#F5A623")
    rose = colors.HexColor("#FF5F7E")
    teal = colors.HexColor("#1FC8B0")
    muted = colors.HexColor("#716E91")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title2", parent=styles["Title"], textColor=navy, fontSize=22, spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"], textColor=muted, fontSize=10, spaceAfter=14,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"], textColor=navy, spaceBefore=16, spaceAfter=8,
    )
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, alignment=TA_LEFT)
    small_style = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8)

    elements = []
    elements.append(Paragraph("SmilePhish", title_style))
    elements.append(Paragraph(
        "Rapport de simulation de phishing — sensibilisation à la sécurité", sub_style
    ))

    meta = [
        f"<b>Entreprise cliente :</b> {campaign.get('organisation_name', '')}",
        f"<b>Campagne :</b> {campaign['name']}",
        f"<b>Objet testé :</b> {campaign['subject']}",
        f"<b>Expéditeur :</b> {campaign['sender_name']} &lt;{campaign['sender_email']}&gt;",
        f"<b>Créée le :</b> {campaign['created_at'][:16].replace('T', ' ')}",
        f"<b>Rapport généré le :</b> {_now_fmt()}",
    ]
    for m in meta:
        elements.append(Paragraph(m, body_style))

    elements.append(Paragraph("Résumé statistique", h2_style))
    metric_rows = [
        ["Indicateur", "Nombre", "%"],
        ["Cibles totales", str(stats["total"]), "-"],
        ["Emails envoyés", str(stats["sent"]), f"{stats['pct_sent']}%"],
        ["Emails rejetés", str(stats["rejected"]), f"{stats['pct_rejected']}%"],
        ["Emails ouverts", str(stats["opened"]), f"{stats['pct_opened']}%"],
        ["Liens cliqués", str(stats["clicked"]), f"{stats['pct_clicked']}%"],
        ["Ont répondu / soumis", str(stats["submitted"]), f"{stats['pct_submitted']}%"],
    ]
    t = Table(metric_rows, colWidths=[8 * cm, 4 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E7E4F4")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF9FF")]),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)

    elements.append(Paragraph("Graphique de répartition", h2_style))
    chart_buf = _build_chart_png(stats)
    from reportlab.platypus import Image as RLImage
    img = RLImage(chart_buf, width=16 * cm, height=16 * cm * 3.6 / 7)
    elements.append(img)

    elements.append(Paragraph("Détail nominatif par destinataire", h2_style))
    elements.append(Paragraph(
        "Date et heure exactes de chaque action — base factuelle pour la sensibilisation "
        "individuelle des collaborateurs concernés.", body_style
    ))
    elements.append(Spacer(1, 8))

    detail_header = ["Email", "Nom", "Service", "Ouvert", "Cliqué", "Soumis", "Dernière action"]
    detail_rows = [detail_header]
    for r in rows:
        detail_rows.append([
            Paragraph(r["email"], small_style),
            Paragraph(f"{r['first_name']} {r['last_name']}".strip(), small_style),
            Paragraph(r["department"] or "-", small_style),
            Paragraph(r["opened_at_fmt"] or "Non", small_style),
            Paragraph(r["clicked_at_fmt"] or "Non", small_style),
            Paragraph(r["submitted_at_fmt"] or "Non", small_style),
            Paragraph(f"{r['last_action']}" + (f"<br/>{r['last_action_at_fmt']}" if r['last_action_at_fmt'] else ""), small_style),
        ])

    dt = Table(
        detail_rows,
        colWidths=[4.2 * cm, 2.6 * cm, 2.2 * cm, 2.3 * cm, 2.3 * cm, 2.3 * cm, 3.3 * cm],
        repeatRows=1,
    )
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E7E4F4")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF9FF")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(dt)

    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Recommandations", h2_style))
    elements.append(Paragraph(
        "Organiser une session de sensibilisation ciblée pour les collaborateurs ayant "
        "cliqué et/ou soumis le formulaire, en s'appuyant sur les horodatages ci-dessus.",
        body_style,
    ))

    doc.build(elements)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# HTML autonome (CSS inline, imprimable en PDF depuis le navigateur)
# ---------------------------------------------------------------------------
def build_html(campaign, stats, rows):
    def row_html(r):
        def badge(ok, dt):
            if ok:
                return f'<span style="background:#ffe3e9;color:#d6315a;padding:3px 10px;border-radius:999px;font-weight:700;font-size:11px;">Oui — {dt}</span>'
            return '<span style="background:#e3fbf6;color:#148f7d;padding:3px 10px;border-radius:999px;font-weight:700;font-size:11px;">Non</span>'

        return f"""
        <tr>
          <td>{r['email']}</td>
          <td>{r['first_name']} {r['last_name']}</td>
          <td>{r['department'] or '-'}</td>
          <td>{badge(r['opened'], r['opened_at_fmt'] or '')}</td>
          <td>{badge(r['clicked'], r['clicked_at_fmt'] or '')}</td>
          <td>{badge(r['submitted'], r['submitted_at_fmt'] or '')}</td>
          <td>{r['last_action']}<br><small style="color:#716e91">{r['last_action_at_fmt'] or ''}</small></td>
        </tr>"""

    rows_html = "\n".join(row_html(r) for r in rows)

    metrics = [
        ("Cibles totales", stats["total"], None),
        ("Envoyés", stats["sent"], stats["pct_sent"]),
        ("Rejetés", stats["rejected"], stats["pct_rejected"]),
        ("Ouverts", stats["opened"], stats["pct_opened"]),
        ("Cliqués", stats["clicked"], stats["pct_clicked"]),
        ("Soumis", stats["submitted"], stats["pct_submitted"]),
    ]
    tiles_html = "\n".join(
        f"""<div style="background:white;border:1px solid #e7e4f4;border-radius:14px;padding:18px;box-shadow:0 8px 20px rgba(39,32,102,0.08);">
              <div style="font-size:28px;font-weight:800;color:#1b1548;">{n}</div>
              {f'<div style="font-size:13px;font-weight:800;color:#6440e8;">{pct}%</div>' if pct is not None else ''}
              <div style="font-size:11px;color:#716e91;text-transform:uppercase;letter-spacing:0.5px;margin-top:4px;">{label}</div>
            </div>"""
        for label, n, pct in metrics
    )

    chart_svg = _build_chart_svg(stats)

    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>SmilePhish — Rapport {campaign['name']}</title>
<style>
  body {{ font-family: "Segoe UI", Arial, sans-serif; background:#f6f5fb; color:#1c1b33; margin:0; padding:40px; }}
  .header {{ background: linear-gradient(120deg,#110c2e,#1b1548 55%,#272066); color:white; padding:28px 32px; border-radius:16px; margin-bottom:28px; }}
  .header h1 {{ margin:0 0 4px; font-size:24px; }}
  .header p {{ margin:0; color:rgba(255,255,255,0.7); font-size:13px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:14px; margin-bottom:28px; }}
  table {{ width:100%; border-collapse:collapse; background:white; border-radius:12px; overflow:hidden; box-shadow:0 8px 20px rgba(39,32,102,0.08); }}
  th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid #e7e4f4; font-size:13px; }}
  th {{ background:#1b1548; color:white; text-transform:uppercase; font-size:11px; letter-spacing:0.5px; }}
  .meta {{ margin-bottom:20px; font-size:14px; }}
  .meta b {{ color:#1b1548; }}
  @media print {{ body {{ background:white; padding:10px; }} }}
</style>
</head>
<body>
  <div class="header">
    <h1>SmilePhish</h1>
    <p>Rapport de simulation de phishing — sensibilisation à la sécurité</p>
  </div>

  <div class="meta">
    <div><b>Entreprise cliente :</b> {campaign.get('organisation_name', '')}</div>
    <div><b>Campagne :</b> {campaign['name']}</div>
    <div><b>Objet testé :</b> {campaign['subject']}</div>
    <div><b>Expéditeur :</b> {campaign['sender_name']} &lt;{campaign['sender_email']}&gt;</div>
    <div><b>Rapport généré le :</b> {_now_fmt()}</div>
  </div>

  <div class="grid">
    {tiles_html}
  </div>

  <h3 style="color:#1b1548;">Graphique de répartition</h3>
  <div style="background:white;border-radius:14px;padding:16px;box-shadow:0 8px 20px rgba(39,32,102,0.08);margin-bottom:28px;">
    {chart_svg}
  </div>

  <h3 style="color:#1b1548;">Détail nominatif par destinataire</h3>
  <table>
    <thead>
      <tr><th>Email</th><th>Nom</th><th>Service</th><th>Ouvert</th><th>Cliqué</th><th>Soumis</th><th>Dernière action</th></tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <p style="margin-top:24px;color:#716e91;font-size:12px;">
    Document généré par SmilePhish — usage interne de sensibilisation à la sécurité.
  </p>
</body>
</html>"""
