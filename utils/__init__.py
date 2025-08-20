# File: utils/__init__.py
# Descrizione: Contiene funzioni di utilità generiche riutilizzate in diverse parti dell'applicazione.

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional, Tuple, List
import csv
import tempfile
from fastapi.responses import FileResponse

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - openpyxl is an optional dep at runtime
    Workbook = None
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU


MONTH_NAMES = {
    1: "Gennaio",
    2: "Febbraio",
    3: "Marzo",
    4: "Aprile",
    5: "Maggio",
    6: "Giugno",
    7: "Luglio",
    8: "Agosto",
    9: "Settembre",
    10: "Ottobre",
    11: "Novembre",
    12: "Dicembre",
}

def get_color_for_type(training_type: Optional[str]) -> str:
    """
    Restituisce un codice colore esadecimale basato sul tipo di allenamento.
    """
    colors = {
        "Barca": "#0d6efd",
        "Remoergometro": "#198754",
        "Corsa": "#6f42c1",
        "Pesi": "#dc3545",
        "Circuito": "#fd7e14",
        "Altro": "#212529"
    }
    return colors.get(training_type, "#6c757d")


DAY_MAP_DATETIL = {
    "Lunedì": MO, "Martedì": TU, "Mercoledì": WE, "Giovedì": TH,
    "Venerdì": FR, "Sabato": SA, "Domenica": SU
}


def parse_time_string(time_str: str) -> time:
    """
    Converte una stringa 'HH:MM' in un oggetto time.
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)
    except (ValueError, TypeError):
        return time(0, 0)


def parse_orario(base_date: date, orario_str: str) -> Tuple[datetime, datetime]:
    """
    Converte una stringa di orario (es. "8:00-10:00") in un tuple
    di oggetti datetime di inizio e fine con timezone UTC.
    """
    if not orario_str or orario_str.lower() == "personalizzato":
        return (datetime.combine(base_date, time.min, timezone.utc), 
                datetime.combine(base_date, time.max, timezone.utc))
    try:
        if '-' in orario_str:
            parts = orario_str.split('-', 1)
            start_part = parts[0].strip()
            end_part = parts[1].strip() if len(parts) > 1 else ""
            start_time_obj = parse_time_string(start_part)
            if end_part:
                end_time_obj = parse_time_string(end_part)
            else:
                # default duration 60 minutes when end is missing
                start_dt = datetime.combine(base_date, start_time_obj, timezone.utc)
                end_dt = start_dt + timedelta(hours=1)
                return start_dt, end_dt
        else:
            start_time_obj = parse_time_string(orario_str.strip())
            start_dt = datetime.combine(base_date, start_time_obj, timezone.utc)
            end_dt = start_dt + timedelta(hours=1)
            return start_dt, end_dt

        start_dt = datetime.combine(base_date, start_time_obj, timezone.utc)
        end_dt = datetime.combine(base_date, end_time_obj, timezone.utc)
        if end_dt < start_dt:
            # guard against invalid ranges
            end_dt = start_dt
        return start_dt, end_dt
    except Exception:
        return (datetime.combine(base_date, time.min, timezone.utc), 
                datetime.combine(base_date, time.max, timezone.utc))


def _build_title(month_start: date) -> str:
    month_name = MONTH_NAMES.get(month_start.month, str(month_start.month))
    return f"Turni aperture Canottieri {month_name} {month_start.year}"


def export_turni_csv(turni: List["models.Turno"], month_start: date) -> FileResponse:
    """Generate a CSV report for ``turni`` of ``month_start`` and return it."""
    title = _build_title(month_start)
    filename = f"{title}.csv"
    with tempfile.NamedTemporaryFile("w", delete=False, newline="", suffix=".csv") as tmp:
        writer = csv.writer(tmp)
        writer.writerow([title])
        writer.writerow(["ID", "Data", "Fascia Oraria", "Allenatore"])
        for t in turni:
            coach = f"{t.user.first_name} {t.user.last_name}" if t.user else ""
            writer.writerow([t.id, t.data.isoformat(), t.fascia_oraria, coach])
        tmp_path = tmp.name
    return FileResponse(tmp_path, media_type="text/csv", filename=filename)


def export_turni_excel(turni: List["models.Turno"], month_start: date) -> FileResponse:
    """Generate an Excel (or CSV fallback) report for ``turni`` of ``month_start``."""
    title = _build_title(month_start)
    filename = f"{title}.xlsx"
    if Workbook is None:
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", suffix=".xlsx") as tmp:
            writer = csv.writer(tmp)
            writer.writerow([title])
            writer.writerow(["ID", "Data", "Fascia Oraria", "Allenatore"])
            for t in turni:
                coach = f"{t.user.first_name} {t.user.last_name}" if t.user else ""
                writer.writerow([t.id, t.data.isoformat(), t.fascia_oraria, coach])
            tmp_path = tmp.name
        return FileResponse(tmp_path, media_type="application/vnd.ms-excel", filename=filename)
    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".xlsx") as tmp:
        wb = Workbook()
        ws = wb.active
        ws.append([title])
        ws.append(["ID", "Data", "Fascia Oraria", "Allenatore"])
        for t in turni:
            coach = f"{t.user.first_name} {t.user.last_name}" if t.user else ""
            ws.append([t.id, t.data.isoformat(), t.fascia_oraria, coach])
        wb.save(tmp.name)
        tmp_path = tmp.name
    return FileResponse(
        tmp_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )
