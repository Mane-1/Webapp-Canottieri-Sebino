# File: test_helpers.py
# Descrizione: Contiene funzioni di utilità generiche riutilizzate in diverse parti dell'applicazione.

from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple, List
import csv
import tempfile
from fastapi.responses import FileResponse

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover - openpyxl is an optional dep at runtime
    Workbook = None
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

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
    di oggetti datetime di inizio e fine.
    """
    if not orario_str or orario_str.lower() == "personalizzato":
        return datetime.combine(base_date, time.min), datetime.combine(base_date, time.max)
    try:
        if '-' in orario_str:
            start_part, end_part = orario_str.split('-')
            start_time_obj = parse_time_string(start_part.strip())
            end_time_obj = parse_time_string(end_part.strip())
        else:
            start_time_obj = parse_time_string(orario_str.strip())
            end_time_obj = (datetime.combine(base_date, start_time_obj) + timedelta(hours=1)).time()

        start_dt = datetime.combine(base_date, start_time_obj)
        end_dt = datetime.combine(base_date, end_time_obj)
        return start_dt, end_dt
    except Exception:
        return datetime.combine(base_date, time.min), datetime.combine(base_date, time.max)


def export_turni_csv(turni: List["models.Turno"]) -> FileResponse:
    """Generate a CSV report for the given ``turni`` and return it as ``FileResponse``."""
    with tempfile.NamedTemporaryFile("w", delete=False, newline="", suffix=".csv") as tmp:
        writer = csv.writer(tmp)
        writer.writerow(["ID", "Data", "Fascia Oraria", "Allenatore"])
        for t in turni:
            coach = f"{t.user.first_name} {t.user.last_name}" if t.user else ""
            writer.writerow([t.id, t.data.isoformat(), t.fascia_oraria, coach])
        tmp_path = tmp.name
    return FileResponse(tmp_path, media_type="text/csv", filename="turni.csv")


def export_turni_excel(turni: List["models.Turno"]) -> FileResponse:
    """Generate an Excel (or CSV fallback) report for ``turni``."""
    if Workbook is None:
        with tempfile.NamedTemporaryFile("w", delete=False, newline="", suffix=".xlsx") as tmp:
            writer = csv.writer(tmp)
            writer.writerow(["ID", "Data", "Fascia Oraria", "Allenatore"])
            for t in turni:
                coach = f"{t.user.first_name} {t.user.last_name}" if t.user else ""
                writer.writerow([t.id, t.data.isoformat(), t.fascia_oraria, coach])
            tmp_path = tmp.name
        return FileResponse(tmp_path, media_type="application/vnd.ms-excel", filename="turni.xlsx")
    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".xlsx") as tmp:
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Data", "Fascia Oraria", "Allenatore"])
        for t in turni:
            coach = f"{t.user.first_name} {t.user.last_name}" if t.user else ""
            ws.append([t.id, t.data.isoformat(), t.fascia_oraria, coach])
        wb.save(tmp.name)
        tmp_path = tmp.name
    return FileResponse(
        tmp_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="turni.xlsx",
    )
