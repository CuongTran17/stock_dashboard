from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Literal

from openpyxl import Workbook
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.models import User, UserSubscription

ReportType = Literal["summary", "revenue", "users", "orders"]
ReportPeriod = Literal["day", "month", "quarter", "year", "all", "custom"]
ReportSort = Literal["asc", "desc"]


@dataclass(frozen=True)
class ReportFilters:
    report_type: ReportType = "summary"
    period: ReportPeriod = "month"
    anchor_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    sort: ReportSort = "asc"


@dataclass(frozen=True)
class ResolvedReportRange:
    start_date: date | None
    end_date: date | None
    bucket: Literal["day", "month", "quarter", "year", "all"]
    label: str


def _today() -> date:
    return datetime.now().date()


def _month_end(value: date) -> date:
    if value.month == 12:
        return date(value.year, 12, 31)
    return date(value.year, value.month + 1, 1) - timedelta(days=1)


def resolve_report_range(filters: ReportFilters) -> ResolvedReportRange:
    anchor = filters.anchor_date or _today()
    if filters.period == "all":
        return ResolvedReportRange(None, None, "year", "Tất cả")
    if filters.period == "custom":
        if filters.start_date is None or filters.end_date is None:
            raise ValueError("start_date and end_date are required for custom period")
        if filters.end_date < filters.start_date:
            raise ValueError("end_date must be after or equal to start_date")
        return ResolvedReportRange(filters.start_date, filters.end_date, "day", "Tùy chọn")
    if filters.period == "day":
        return ResolvedReportRange(anchor, anchor, "day", anchor.isoformat())
    if filters.period == "month":
        start = date(anchor.year, anchor.month, 1)
        return ResolvedReportRange(start, _month_end(start), "day", anchor.strftime("%Y-%m"))
    if filters.period == "quarter":
        quarter_start_month = ((anchor.month - 1) // 3) * 3 + 1
        start = date(anchor.year, quarter_start_month, 1)
        end = _month_end(date(anchor.year, quarter_start_month + 2, 1))
        return ResolvedReportRange(start, end, "month", f"Q{((anchor.month - 1) // 3) + 1}/{anchor.year}")
    if filters.period == "year":
        return ResolvedReportRange(date(anchor.year, 1, 1), date(anchor.year, 12, 31), "month", str(anchor.year))
    raise ValueError(f"Unsupported report period: {filters.period}")


def sort_detail_rows(rows: Iterable[dict[str, Any]], sort: ReportSort = "asc") -> list[dict[str, Any]]:
    reverse = sort == "desc"
    return sorted(rows, key=lambda row: str(row.get("date") or row.get("period") or ""), reverse=reverse)


def _date_expr(column: Any, bucket: str) -> Any:
    if bucket == "year":
        return func.date_format(column, "%Y")
    if bucket == "quarter":
        return func.concat(func.year(column), "-Q", func.quarter(column))
    if bucket == "month":
        return func.date_format(column, "%Y-%m")
    return func.date_format(column, "%Y-%m-%d")


def _apply_date_range(query: Any, column: Any, resolved: ResolvedReportRange) -> Any:
    if resolved.start_date is not None:
        query = query.filter(column >= datetime.combine(resolved.start_date, datetime.min.time()))
    if resolved.end_date is not None:
        query = query.filter(column <= datetime.combine(resolved.end_date, datetime.max.time()))
    return query


def build_admin_report(db: Session, filters: ReportFilters) -> dict[str, Any]:
    resolved = resolve_report_range(filters)
    sort = filters.sort if filters.sort in {"asc", "desc"} else "asc"

    revenue = _build_revenue_section(db, resolved, sort)
    users = _build_users_section(db, resolved, sort)
    orders = _build_orders_section(db, resolved, sort)

    sections = {
        "revenue": revenue,
        "users": users,
        "orders": orders,
    }
    selected = sections if filters.report_type == "summary" else {filters.report_type: sections[filters.report_type]}
    return {
        "report_type": filters.report_type,
        "period": filters.period,
        "sort": sort,
        "range": {
            "start_date": resolved.start_date.isoformat() if resolved.start_date else None,
            "end_date": resolved.end_date.isoformat() if resolved.end_date else None,
            "bucket": resolved.bucket,
            "label": resolved.label,
        },
        "sections": selected,
    }


def _build_revenue_section(db: Session, resolved: ResolvedReportRange, sort: ReportSort) -> dict[str, Any]:
    base = db.query(UserSubscription).filter(UserSubscription.status == "completed")
    base = _apply_date_range(base, UserSubscription.created_at, resolved)
    total_revenue = float(base.with_entities(func.coalesce(func.sum(UserSubscription.amount), 0)).scalar() or 0)
    order_count = int(base.with_entities(func.count(UserSubscription.id)).scalar() or 0)

    period_expr = _date_expr(UserSubscription.created_at, resolved.bucket).label("period")
    rows = (
        base.with_entities(
            period_expr,
            func.coalesce(func.sum(UserSubscription.amount), 0).label("revenue"),
            func.count(UserSubscription.id).label("orders"),
        )
        .group_by(period_expr)
        .all()
    )
    details = sort_detail_rows(
        [
            {
                "date": str(row.period),
                "revenue": float(row.revenue or 0),
                "orders": int(row.orders or 0),
            }
            for row in rows
        ],
        sort,
    )
    return {
        "title": "Doanh thu",
        "summary": {
            "total_revenue": total_revenue,
            "completed_orders": order_count,
            "average_order_value": round(total_revenue / order_count, 2) if order_count else 0,
        },
        "details": details,
    }


def _build_users_section(db: Session, resolved: ResolvedReportRange, sort: ReportSort) -> dict[str, Any]:
    base = db.query(User)
    ranged = _apply_date_range(base, User.created_at, resolved)
    total_new = int(ranged.with_entities(func.count(User.id)).scalar() or 0)
    premium_count = int(ranged.with_entities(func.count(User.id)).filter(User.role.in_(["premium", "admin"])).scalar() or 0)
    locked_count = int(ranged.with_entities(func.count(User.id)).filter(User.is_locked.is_(True)).scalar() or 0)

    period_expr = _date_expr(User.created_at, resolved.bucket).label("period")
    rows = (
        ranged.with_entities(
            period_expr,
            func.count(User.id).label("new_users"),
            func.sum(func.if_(User.role.in_(["premium", "admin"]), 1, 0)).label("premium_users"),
            func.sum(func.if_(User.is_locked.is_(True), 1, 0)).label("locked_users"),
        )
        .group_by(period_expr)
        .all()
    )
    details = sort_detail_rows(
        [
            {
                "date": str(row.period),
                "new_users": int(row.new_users or 0),
                "premium_users": int(row.premium_users or 0),
                "locked_users": int(row.locked_users or 0),
            }
            for row in rows
        ],
        sort,
    )
    return {
        "title": "Người dùng",
        "summary": {
            "new_users": total_new,
            "premium_users": premium_count,
            "locked_users": locked_count,
        },
        "details": details,
    }


def _build_orders_section(db: Session, resolved: ResolvedReportRange, sort: ReportSort) -> dict[str, Any]:
    base = db.query(UserSubscription)
    base = _apply_date_range(base, UserSubscription.created_at, resolved)
    total_orders = int(base.with_entities(func.count(UserSubscription.id)).scalar() or 0)
    completed = int(base.with_entities(func.count(UserSubscription.id)).filter(UserSubscription.status == "completed").scalar() or 0)
    pending = int(base.with_entities(func.count(UserSubscription.id)).filter(UserSubscription.status == "pending").scalar() or 0)
    cancelled = int(base.with_entities(func.count(UserSubscription.id)).filter(UserSubscription.status.in_(["cancelled", "expired"])).scalar() or 0)

    period_expr = _date_expr(UserSubscription.created_at, resolved.bucket).label("period")
    rows = (
        base.with_entities(
            period_expr,
            func.count(UserSubscription.id).label("orders"),
            func.sum(func.if_(UserSubscription.status == "completed", 1, 0)).label("completed"),
            func.sum(func.if_(UserSubscription.status == "pending", 1, 0)).label("pending"),
            func.sum(func.if_(UserSubscription.status.in_(["cancelled", "expired"]), 1, 0)).label("cancelled"),
        )
        .group_by(period_expr)
        .all()
    )
    details = sort_detail_rows(
        [
            {
                "date": str(row.period),
                "orders": int(row.orders or 0),
                "completed": int(row.completed or 0),
                "pending": int(row.pending or 0),
                "cancelled": int(row.cancelled or 0),
            }
            for row in rows
        ],
        sort,
    )
    return {
        "title": "Đơn hàng",
        "summary": {
            "orders": total_orders,
            "completed": completed,
            "pending": pending,
            "cancelled": cancelled,
        },
        "details": details,
    }


def report_to_xlsx(report: dict[str, Any]) -> bytes:
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Tong hop"
    summary_sheet.append(["Loại báo cáo", _report_type_label(report["report_type"])])
    summary_sheet.append(["Khoảng thời gian", report["range"]["label"]])
    summary_sheet.append(["Từ ngày", report["range"]["start_date"] or "Tất cả"])
    summary_sheet.append(["Đến ngày", report["range"]["end_date"] or "Tất cả"])
    summary_sheet.append([])

    for section_key, section in report["sections"].items():
        sheet = workbook.create_sheet(title=_excel_sheet_title(section_key))
        sheet.append([section["title"]])
        sheet.append([])
        sheet.append(["Chỉ số", "Giá trị"])
        for key, value in section["summary"].items():
            sheet.append([_field_label(key), value])
        sheet.append([])
        details = section["details"]
        if details:
            headers = list(details[0].keys())
            sheet.append([_field_label(header) for header in headers])
            for row in details:
                sheet.append([row.get(header) for header in headers])
        summary_sheet.append([section["title"]])
        for key, value in section["summary"].items():
            summary_sheet.append([_field_label(key), value])
        summary_sheet.append([])

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def report_to_pdf(report: dict[str, Any]) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (
            BaseDocTemplate,
            Frame,
            PageTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
    except ModuleNotFoundError as exc:
        raise RuntimeError("reportlab is required to export PDF reports") from exc

    font_name = _register_vietnamese_font(pdfmetrics, TTFont)
    buffer = BytesIO()

    def draw_page(canvas: Any, doc: Any) -> None:
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#0f172a"))
        canvas.rect(0, height - 26 * mm, width, 26 * mm, stroke=0, fill=1)
        canvas.setFont(font_name, 9)
        canvas.setFillColor(colors.HexColor("#cbd5e1"))
        canvas.drawString(18 * mm, height - 11 * mm, "Admin Dashboard")
        canvas.setFont(font_name, 16)
        canvas.setFillColor(colors.white)
        canvas.drawString(18 * mm, height - 18 * mm, "Báo cáo quản trị")
        canvas.setFont(font_name, 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawRightString(width - 18 * mm, 10 * mm, f"Trang {doc.page}")
        canvas.restoreState()

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=34 * mm,
        bottomMargin=18 * mm,
        title="Báo cáo quản trị",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=draw_page)])

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=12,
        spaceAfter=8,
    )
    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )
    centered_style = ParagraphStyle("Centered", parent=small_style, alignment=TA_CENTER)
    right_style = ParagraphStyle("Right", parent=small_style, alignment=TA_RIGHT)

    story: list[Any] = [
        Paragraph("Báo cáo quản trị", title_style),
        Paragraph(
            f"Loại báo cáo: <b>{_report_type_label(report['report_type'])}</b> &nbsp;&nbsp; "
            f"Khoảng thời gian: <b>{report['range']['label']}</b> &nbsp;&nbsp; "
            f"Từ {report['range']['start_date'] or 'Tất cả'} đến {report['range']['end_date'] or 'Tất cả'}",
            subtitle_style,
        ),
    ]

    for section in report["sections"].values():
        story.append(Paragraph(str(section["title"]), section_style))
        summary_rows = _summary_table_rows(section["summary"])
        if summary_rows:
            story.append(_summary_cards(summary_rows, font_name, small_style, right_style))
            story.append(Spacer(1, 8))

        details = section["details"]
        if details:
            headers = list(details[0].keys())
            table_rows: list[list[Any]] = [[Paragraph(_field_label(header), centered_style) for header in headers]]
            for row in details[:80]:
                cells: list[Any] = []
                for header in headers:
                    value = _format_report_value(header, row.get(header))
                    style = right_style if _is_numeric_value(row.get(header)) else small_style
                    cells.append(Paragraph(value, style))
                table_rows.append(cells)
            story.append(_detail_table(table_rows, font_name))
            if len(details) > 80:
                story.append(Paragraph(f"Đã hiển thị 80/{len(details)} dòng chi tiết trong bản PDF.", small_style))
        else:
            story.append(Paragraph("Không có dữ liệu trong khoảng thời gian này.", small_style))

    doc.build(story)
    return buffer.getvalue()


def _register_vietnamese_font(pdfmetrics: Any, TTFont: Any) -> str:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            font_name = f"AdminReport-{path.stem}"
            if font_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(font_name, str(path)))
            return font_name
    return "Helvetica"


def _field_label(key: str) -> str:
    labels = {
        "date": "Thời gian",
        "revenue": "Doanh thu",
        "orders": "Đơn hàng",
        "completed_orders": "GD hoàn tất",
        "average_order_value": "TB/GD",
        "total_revenue": "Tổng doanh thu",
        "new_users": "Người dùng mới",
        "premium_users": "Premium",
        "locked_users": "Bị khóa",
        "completed": "Hoàn tất",
        "pending": "Đang chờ",
        "cancelled": "Đã hủy",
    }
    return labels.get(key, key.replace("_", " ").title())


def _report_type_label(report_type: str) -> str:
    return {
        "summary": "Tổng hợp",
        "revenue": "Doanh thu",
        "users": "Người dùng",
        "orders": "Đơn hàng",
    }.get(report_type, report_type)


def _excel_sheet_title(section_key: str) -> str:
    return {
        "revenue": "Doanh thu",
        "users": "Nguoi dung",
        "orders": "Don hang",
    }.get(section_key, section_key[:31])


def _is_numeric_value(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _format_report_value(key: str, value: Any) -> str:
    if value is None:
        return "-"
    if _is_numeric_value(value):
        if any(token in key for token in ("revenue", "amount", "value")):
            return f"{float(value):,.0f} VND".replace(",", ".")
        return f"{float(value):,.0f}".replace(",", ".")
    return str(value)


def _summary_table_rows(summary: dict[str, Any]) -> list[list[str]]:
    return [[_field_label(key), _format_report_value(key, value)] for key, value in summary.items()]


def _summary_cards(rows: list[list[str]], font_name: str, label_style: Any, value_style: Any) -> Any:
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Table, TableStyle

    cells = [[Paragraph(label, label_style), Paragraph(f"<b>{value}</b>", value_style)] for label, value in rows]
    table = Table(cells, colWidths=[58 * mm, 32 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _detail_table(rows: list[list[Any]], font_name: str) -> Any:
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    column_count = len(rows[0])
    table = Table(rows, repeatRows=1, hAlign="LEFT")
    style_commands: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2fe")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#075985")),
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for row_index in range(1, len(rows)):
        if row_index % 2 == 0:
            style_commands.append(("BACKGROUND", (0, row_index), (column_count - 1, row_index), colors.HexColor("#f8fafc")))
    table.setStyle(TableStyle(style_commands))
    return table
