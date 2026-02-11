# views.py
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

from datetime import timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncDay, TruncMonth
from django.shortcuts import render
from django.utils.timezone import now

from appointment.models import Appointment
from patient.models import Patient
from billing.models import BillingRecord
from inventory.models import InventoryItem


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def reports_dashboard(request):
    # -----------------------------
    # Config & Filters
    # -----------------------------
    range_type = request.GET.get("range", "daily")  # daily | monthly
    today = now()
    start_date = today - timedelta(days=30)

    trunc = TruncMonth if range_type == "monthly" else TruncDay
    date_format = "%b %Y" if range_type == "monthly" else "%b %d"

    # -----------------------------
    # Summary Metrics
    # -----------------------------
    completed_appointments = Appointment.objects.filter(
        status="done",
        date__gte=start_date
    ).count()

    total_patients = Patient.objects.count()

    paid_revenue = (
        BillingRecord.objects.filter(
            payment_status="paid",
            date_issued__gte=start_date
        ).aggregate(total=Sum("amount"))["total"] or 0
    )

    low_stock_count = InventoryItem.objects.filter(
        stock__lte=F("low_stock_threshold")
    ).count()

    expired_item_count = InventoryItem.objects.filter(
        status="expired"
    ).count()

    # -----------------------------
    # Appointment Trend
    # -----------------------------
    appointment_trend = (
        Appointment.objects.filter(
            date__gte=start_date,
            status__in=["arrived", "ongoing", "done"]
        )
        .annotate(period=trunc("date"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    appointment_labels = [a["period"].strftime(date_format) for a in appointment_trend]
    appointment_data = [a["count"] for a in appointment_trend]

    # -----------------------------
    # Patient Growth
    # -----------------------------
    patient_growth = (
        Patient.objects.filter(created_at__gte=start_date)
        .annotate(period=trunc("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    patient_labels = [p["period"].strftime(date_format) for p in patient_growth]
    patient_data = [p["count"] for p in patient_growth]

    # -----------------------------
    # Revenue Trend (PAID ONLY)
    # -----------------------------
    revenue_trend = (
        BillingRecord.objects.filter(
            payment_status="paid",
            date_issued__gte=start_date
        )
        .annotate(period=trunc("date_issued"))
        .values("period")
        .annotate(total=Sum("amount"))
        .order_by("period")
    )

    revenue_labels = [r["period"].strftime(date_format) for r in revenue_trend]
    revenue_data = [float(r["total"] or 0) for r in revenue_trend]

    # -----------------------------
    # Inventory by Category
    # -----------------------------
    inventory_by_category = (
        InventoryItem.objects
        .values("category")
        .annotate(count=Count("id"))
        .order_by("category")
    )

    inventory_category_labels = [i["category"] or "Uncategorized" for i in inventory_by_category]
    inventory_category_data = [i["count"] for i in inventory_by_category]

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        "range_type": range_type,

        # Summary cards
        "completed_appointments": completed_appointments,
        "total_patients": total_patients,
        "paid_revenue": paid_revenue,
        "low_stock_count": low_stock_count,
        "expired_item_count": expired_item_count,

        # Charts
        "appointment_labels": appointment_labels,
        "appointment_data": appointment_data,

        "patient_labels": patient_labels,
        "patient_data": patient_data,

        "revenue_labels": revenue_labels,
        "revenue_data": revenue_data,

        "inventory_category_labels": inventory_category_labels,
        "inventory_category_data": inventory_category_data,
    }

    return render(request, "reports/index.html", context)

# -----------------------------
# Shared Data Builder
# -----------------------------
def build_report_data(range_type):
    today = now()
    start_date = today - timedelta(days=30)

    trunc = TruncMonth if range_type == "monthly" else TruncDay
    date_format = "%b %Y" if range_type == "monthly" else "%b %d"

    appointment_trend = (
        Appointment.objects
        .filter(date__gte=start_date, status__in=["arrived", "ongoing", "done"])
        .annotate(period=trunc("date"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    patient_growth = (
        Patient.objects
        .filter(created_at__gte=start_date)
        .annotate(period=trunc("created_at"))
        .values("period")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    revenue_trend = (
        BillingRecord.objects
        .filter(payment_status="paid", date_issued__gte=start_date)
        .annotate(period=trunc("date_issued"))
        .values("period")
        .annotate(total=Sum("amount"))
        .order_by("period")
    )

    inventory_summary = (
        InventoryItem.objects
        .values("category")
        .annotate(
            total=Count("id"),
            low_stock=Count("id", filter=F("status") == "low_stock"),
            expired=Count("id", filter=F("status") == "expired"),
        )
    )

    return {
        "date": today.date(),
        "range": range_type,
        "appointment_chart": [(a["period"].strftime(date_format), a["count"]) for a in appointment_trend],
        "patient_chart": [(p["period"].strftime(date_format), p["count"]) for p in patient_growth],
        "revenue_chart": [(r["period"].strftime(date_format), float(r["total"] or 0)) for r in revenue_trend],
        "inventory_chart": list(inventory_summary),
        "raw": {
            "appointments": Appointment.objects.filter(date__gte=start_date),
            "patients": Patient.objects.filter(created_at__gte=start_date),
            "billing": BillingRecord.objects.filter(payment_status="paid", date_issued__gte=start_date),
            "inventory": InventoryItem.objects.all(),
        }
    }

# -----------------------------
# Export View (Excel / PDF)
# -----------------------------
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def export_reports_dashboard(request):
    range_type = request.GET.get("range", "daily")
    export_format = request.GET.get("format", "excel")

    if export_format not in ["excel", "pdf"]:
        export_format = "excel"

    data = build_report_data(range_type)

    if export_format == "pdf":
        return export_pdf_report(data)

    return export_excel_report(data)

# -----------------------------
# PDF Renderer
# -----------------------------
def export_pdf_report(data):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Clinic_Report_{data["range"]}_{data["date"]}.pdf"'
    )

    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Clinic Reports Summary", styles["Title"]))
    elements.append(Spacer(1, 16))

    def table(title, rows, headers):
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 8))
        elements.append(Table([headers] + rows))
        elements.append(Spacer(1, 16))

    table(
        "Appointments Trend",
        data["appointment_chart"],
        ["Period", "Appointments"]
    )

    table(
        "Patient Growth",
        data["patient_chart"],
        ["Period", "New Patients"]
    )

    table(
        "Paid Revenue",
        data["revenue_chart"],
        ["Period", "Amount (₱)"]
    )

    table(
        "Inventory Status",
        [(i["category"], i["total"], i["low_stock"], i["expired"]) for i in data["inventory_chart"]],
        ["Category", "Total", "Low Stock", "Expired"]
    )

    doc.build(elements)
    return response

# -----------------------------
# Excel Renderer
# -----------------------------
def export_excel_report(data):
    wb = Workbook()

    # Appointments
    ws = wb.active
    ws.title = "Appointments"
    ws.append(["ID", "Date", "Status", "Dentist", "Branch"])
    for a in data["raw"]["appointments"]:
        ws.append([
            a.display_id,
            a.date,
            a.status,
            a.dentist.name if a.dentist else "",
            a.branch.name if a.branch else ""
        ])

    # Patients
    ws = wb.create_sheet("Patients")
    ws.append(["Name", "Email", "Created At"])
    for p in data["raw"]["patients"]:
        ws.append([p.name, p.email, p.created_at.date()])

    # Billing
    ws = wb.create_sheet("Billing")
    ws.append(["Patient", "Amount", "Issued Date"])
    for b in data["raw"]["billing"]:
        ws.append([b.patient.name, float(b.amount), b.date_issued.date()])

    # Inventory
    ws = wb.create_sheet("Inventory")
    ws.append(["Item", "Category", "Stock", "Status"])
    for i in data["raw"]["inventory"]:
        ws.append([i.item_name, i.category, i.stock, i.status])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="Clinic_Data_{data["range"]}_{data["date"]}.xlsx"'
    )

    wb.save(response)
    return response