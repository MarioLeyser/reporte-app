from datetime import date, datetime

def format_date_spanish(d: date) -> str:
    """Formato DD/MM/YYYY"""
    return d.strftime("%d/%m/%Y")

def parse_date_str(date_str: str) -> date:
    """Convierte string DD/MM/YYYY a date"""
    return datetime.strptime(date_str, "%d/%m/%Y").date()
