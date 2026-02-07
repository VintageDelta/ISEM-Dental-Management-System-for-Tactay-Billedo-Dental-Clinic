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

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def export_reports_dashboard(request):
    range_type = request.GET.get("range", "daily")
    today = now()
    start_date = today - timedelta(days=30)

    trunc = TruncMonth if range_type == "monthly" else TruncDay
    date_format = "%b %Y" if range_type == "monthly" else "%b %d"

    wb = Workbook()
    ws = wb.active
    ws.title = "Dashboard Report"

    header_font = Font(bold=True)
    row = 1

    def write_header(title):
        nonlocal row
        ws.cell(row=row, column=1, value=title).font = Font(bold=True, size=14)
        row += 2

    def write_table(headers, data_rows):
        nonlocal row
        for col, h in enumerate(headers, start=1):
            ws.cell(row=row, column=col, value=h).font = header_font
        row += 1
        for data in data_rows:
            for col, value in enumerate(data, start=1):
                ws.cell(row=row, column=col, value=value)
            row += 1
        row += 2

    # -------------------------
    # Appointments Summary
    # -------------------------
    write_header("Appointments Summary")

    appointment_trend = (
        Appointment.objects.filter(
            date__gte=start_date,
            status__in=["arrived", "ongoing", "done"]
        )
        .annotate(period=trunc("date"))
        .values("period")
        .annotate(total=Count("id"))
        .order_by("period")
    )

    appointment_data = [
        (a["period"].strftime(date_format), a["total"])
        for a in appointment_trend
    ]

    write_table(
        ["Period", "Total Appointments"],
        appointment_data
    )

    # -------------------------
    # Patient Growth
    # -------------------------
    write_header("Patient Growth")

    patient_growth = (
        Patient.objects.filter(created_at__gte=start_date)
        .annotate(period=trunc("created_at"))
        .values("period")
        .annotate(total=Count("id"))
        .order_by("period")
    )

    patient_data = [
        (p["period"].strftime(date_format), p["total"])
        for p in patient_growth
    ]

    write_table(
        ["Period", "New Patients"],
        patient_data
    )

    # -------------------------
    # Billing / Revenue (PAID)
    # -------------------------
    write_header("Paid Revenue Summary")

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

    revenue_data = [
        (r["period"].strftime(date_format), float(r["total"] or 0))
        for r in revenue_trend
    ]

    write_table(
        ["Period", "Total Revenue (₱)"],
        revenue_data
    )

    # -------------------------
    # Inventory Status Summary
    # -------------------------
    write_header("Inventory Status")

    inventory_summary = (
        InventoryItem.objects
        .values("category")
        .annotate(
            total=Count("id"),
            low_stock=Count("id", filter=F("status") == "low_stock"),
            expired=Count("id", filter=F("status") == "expired"),
        )
        .order_by("category")
    )

    inventory_data = [
        (
            i["category"],
            i["total"],
            i["low_stock"],
            i["expired"],
        )
        for i in inventory_summary
    ]

    write_table(
        ["Category", "Total Items", "Low Stock", "Expired"],
        inventory_data
    )

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="Clinic_Reports_{today.date()}.xlsx"'
    )

    wb.save(response)
    return response