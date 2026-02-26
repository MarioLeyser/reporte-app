import re
from jinja2 import Environment, FileSystemLoader
from config import TEMPLATES_DIR, ASSETS_DIR
from app.models.report_data import Report
from collections import defaultdict
from datetime import date

def tex_escape(text):
    """
    Escapa caracteres especiales de LaTeX
        :param text: el texto a ser escapado
        :return: el texto escapado
    """
    if not isinstance(text, str):
        return text
    
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key=lambda item: -len(item))))
    return regex.sub(lambda match: conv[match.group()], text)

def render_report_tex(report: Report) -> str:
    # Usamos delimitadores personalizados para no entrar en conflicto con LaTeX
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        block_start_string='[*',
        block_end_string='*]',
        variable_start_string='((',
        variable_end_string='))',
        comment_start_string='[#',
        comment_end_string='#]'
    )
    
    # Aplicar escape de LaTeX a todos los strings del reporte
    report.activity = tex_escape(report.activity)
    report.activity_type = tex_escape(report.activity_type)
    report.place = tex_escape(report.place)
    report.client = tex_escape(report.client)
    report.status = tex_escape(report.status)
    report.client_approval = tex_escape(report.client_approval)
    report.summary = tex_escape(report.summary)
    report.supervisor = tex_escape(report.supervisor)
    report.personnel = [tex_escape(p) for p in report.personnel]
    report.observations = [tex_escape(o) for o in report.observations]
    report.conclusions = [tex_escape(c) for c in report.conclusions]
    
    for eq in report.equipment_list:
        eq.name = tex_escape(eq.name)
        eq.brand = tex_escape(eq.brand)
        eq.model = tex_escape(eq.model)
        eq.serial = tex_escape(eq.serial)

    template = env.get_template("report_template.tex")

    # Agrupar fotos por fecha
    photos_by_date = defaultdict(list)
    for photo in report.photos:
        # Escapar el caption de la foto
        photo.caption = tex_escape(photo.caption)
        photos_by_date[photo.action_date].append(photo)

    context = {
        "report": report,
        "photos_by_date": dict(photos_by_date),
        "assets_dir": ASSETS_DIR,
        "format_date": lambda d: d.strftime("%d/%m/%Y") if isinstance(d, date) else d
    }
    return template.render(context)
