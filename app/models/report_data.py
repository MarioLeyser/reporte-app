from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Dict

@dataclass
class Equipment:
    item: int
    name: str
    brand: str
    model: str
    serial: str
    calibration_date: str  # formato DD/MM/YYYY

@dataclass
class PhotoEntry:
    image_path: str          # ruta del archivo (temporal)
    caption: str            # descripción de la foto
    action_date: date       # fecha de la acción
    number: int = 0         # se asigna automáticamente

# Waste dataclass removed as requested

@dataclass
class Report:
    # Encabezado
    title: str = "REPORTE DE ACTIVIDADES Y EVENTOS"
    format_code: str = "ICRT 001 TI CO FO 0011"
    version: str = "2"
    unique_code: str = ""
    reviewed_by: str = "MIGUEL AUCAPOMA"
    review_date: str = "06/10/2023"
    approved_by: str = "JUAN LLANOS"
    approve_date: str = "10/10/2023"

    # Datos del reporte (ingresados por usuario)
    activity: str = ""
    activity_type: str = ""
    place: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    personnel: List[str] = field(default_factory=list)
    client: str = ""
    status: str = ""
    client_approval: str = ""
    
    # Progreso de obra
    total_days: int = 1
    current_day: int = 1
    actual_progress: float = 0.0
    expected_progress: float = 0.0
    progress_status_color: str = "white" # green, yellow, red

    summary: str = ""

    # Evidencia fotográfica
    photos: List[PhotoEntry] = field(default_factory=list)

    # Equipos de medición
    equipment_list: List[Equipment] = field(default_factory=list)

    # Conclusiones
    conclusions: List[str] = field(default_factory=list)
    
    # Observaciones
    observations: List[str] = field(default_factory=list)

    # Supervisor
    supervisor: str = ""

    # Nota final
    replacement_note: str = "Este reporte reemplaza al anterior formato de Actividades y Eventos COG001TITIFO0001"
