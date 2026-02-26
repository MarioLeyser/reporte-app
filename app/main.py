import streamlit as st
import os
import base64
import time
import json
from PIL import Image
from datetime import datetime, date
import config


# ────────────────────────────────────────────────
# AUTOSAVE LOCAL (JSON)
# ────────────────────────────────────────────────
LOCAL_DRAFT_PATH = os.path.join("outputs", "draft_local.json")

def save_local_draft():
    """Guarda el estado actual del formulario en un JSON local.
    Se llama automáticamente en cada render del formulario.
    Solo guarda texto/fechas/equipos (NO bytes de fotos por tamaño).
    """
    try:
        os.makedirs("outputs", exist_ok=True)
        ss = st.session_state
        draft = {
            "saved_at": datetime.now().isoformat(),
            "form_data": {
                "actividad":       ss.get("f_actividad", ""),
                "tipo_actividad":  ss.get("f_tipo", "Mantenimiento"),
                "lugar":           ss.get("f_lugar", ""),
                "fecha_inicio":    ss.get("f_fi", date.today()).isoformat() if hasattr(ss.get("f_fi", date.today()), 'isoformat') else str(ss.get("f_fi", "")),
                "fecha_fin":       ss.get("f_ff", date.today()).isoformat() if hasattr(ss.get("f_ff", date.today()), 'isoformat') else str(ss.get("f_ff", "")),
                "personal":        ss.get("f_pers", ""),
                "cliente":         ss.get("f_cli", ""),
                "estado":          ss.get("f_est", "Culminado"),
                "conformidad":     ss.get("f_conf", "Conforme"),
                "supervisor":      ss.get("f_sup", ""),
                "codigo_reporte":  ss.get("f_cod", ""),
                "nombre_reporte":  ss.get("f_nom", ""),
                "total_dias":      ss.get("f_td", 1),
                "dia_actual":      ss.get("f_da", 1),
                "avance_real":     ss.get("f_ar", 0.0),
                "resumen":         ss.get("f_resumen", ""),
                "observaciones":   ss.get("f_obs", ""),
                "conclusiones":    ss.get("f_conc", ""),
            },
            "equipos": ss.get("equipos_list", []),
            "cloud_photos": [
                {"name": p["name"], "caption": p.get("caption", ""),
                 "date": p["date"].isoformat() if hasattr(p.get("date"), 'isoformat') else str(p.get("date", ""))}
                for p in ss.get("form_photos", []) if p.get("type") == "cloud"
            ]
        }
        with open(LOCAL_DRAFT_PATH, "w", encoding="utf-8") as f:
            json.dump(draft, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[autosave] Error guardando borrador local: {e}")


def load_local_draft():
    """Carga borrador local al session_state si existe.
    Retorna True si cargó datos, False si no hay nada.
    """
    try:
        if not os.path.exists(LOCAL_DRAFT_PATH):
            return False
        with open(LOCAL_DRAFT_PATH, "r", encoding="utf-8") as f:
            draft = json.load(f)
        fd = draft.get("form_data", {})
        ss = st.session_state
        ss["f_actividad"]  = fd.get("actividad", "")
        ss["f_tipo"]       = fd.get("tipo_actividad", "Mantenimiento")
        ss["f_lugar"]      = fd.get("lugar", "")
        ss["f_pers"]       = fd.get("personal", "")
        ss["f_cli"]        = fd.get("cliente", "")
        ss["f_est"]        = fd.get("estado", "Culminado")
        ss["f_conf"]       = fd.get("conformidad", "Conforme")
        ss["f_sup"]        = fd.get("supervisor", "")
        ss["f_cod"]        = fd.get("codigo_reporte", "")
        ss["f_nom"]        = fd.get("nombre_reporte", "")
        ss["f_td"]         = fd.get("total_dias", 1)
        ss["f_da"]         = fd.get("dia_actual", 1)
        ss["f_ar"]         = float(fd.get("avance_real", 0.0))
        ss["f_resumen"]    = fd.get("resumen", "")
        ss["f_obs"]        = fd.get("observaciones", "")
        ss["f_conc"]       = fd.get("conclusiones", "")
        try:
            ss["f_fi"] = date.fromisoformat(fd.get("fecha_inicio", date.today().isoformat()))
            ss["f_ff"] = date.fromisoformat(fd.get("fecha_fin",    date.today().isoformat()))
        except Exception:
            pass
        # Equipos
        if draft.get("equipos"):
            ss["equipos_list"] = draft["equipos"]
        # Fotos de nube
        cloud_photos = draft.get("cloud_photos", [])
        if cloud_photos:
            existing_cloud_ids = {p["name"] for p in ss.get("form_photos", []) if p.get("type") == "cloud"}
            for cp in cloud_photos:
                if cp["name"] not in existing_cloud_ids:
                    ss.setdefault("form_photos", []).append({
                        "id":      f"cloud_restored_{cp['name']}",
                        "type":    "cloud",
                        "name":    cp["name"],
                        "caption": cp.get("caption", ""),
                        "date":    date.fromisoformat(cp["date"]) if cp.get("date") else date.today()
                    })
        ss["local_draft_loaded"] = True
        ss["local_draft_saved_at"] = draft.get("saved_at", "")
        return True
    except Exception as e:
        print(f"[autosave] Error cargando borrador local: {e}")
        return False


def delete_local_draft():
    """Elimina el borrador local después de generar el PDF final."""
    try:
        if os.path.exists(LOCAL_DRAFT_PATH):
            os.remove(LOCAL_DRAFT_PATH)
    except Exception:
        pass


# --- CACHING DE NUBE ---
@st.cache_resource
def get_cloud_client():
    from app.services.nextcloud_service import NextcloudService
    return NextcloudService()

@st.cache_data(show_spinner=False)
def get_cached_file_list(path, extensions=None):
    client = get_cloud_client()
    return client.list_files(path, extensions=extensions)

@st.cache_data(show_spinner=False)
def get_cached_photo(path):
    client = get_cloud_client()
    return client.download_bytes(path)

def pdf_to_image(pdf_path):
    """Convierte la primera página de un PDF a imagen PNG para vista previa."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        if len(doc) > 0:
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Zoom 2x para nitidez
            img_bytes = pix.tobytes("png")
            doc.close()
            return img_bytes
    except Exception as e:
        print(f"Error pdf_to_image: {e}")
    return None

st.set_page_config(page_title="Generador de Reportes COG", layout="wide", page_icon="📝")

# ────────────────────────────────────────────────
# CSS Responsivo + Estilo General
# ────────────────────────────────────────────────
def load_custom_css():
    """Inyecta CSS responsivo y estilos de vista previa."""
    # Leer CSS de preview si existe
    preview_css = ""
    css_path = os.path.join("assets", "css", "preview_styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            preview_css = f.read()

    # Leer nuevo CSS premium
    modern_css = ""
    modern_css_path = os.path.join("assets", "css", "modern_styles.css")
    if os.path.exists(modern_css_path):
        with open(modern_css_path, "r", encoding="utf-8") as f:
            modern_css = f.read()

    responsive_css = """
    <style>
    """ + modern_css + """
    
    /* === Ocultar menú y footer (redundante por modern_styles pero por seguridad) === */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    /* === Mejoras generales === */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        font-size: 14px !important;
    }

    .stButton > button {
        min-height: 44px;
        font-size: 15px !important;
        border-radius: 8px;
    }

    .stButton > button[kind="primary"] {
        min-height: 50px;
        font-size: 16px !important;
        font-weight: 600;
    }

    /* === Sección de expanders más compacta === */
    .streamlit-expanderHeader {
        font-size: 16px !important;
        font-weight: 600;
    }

    /* === RESPONSIVE: Pantallas <= 768px === */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1rem;
        }

        /* Columnas en stack vertical */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0 !important;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* Título más pequeño */
        h1 {
            font-size: 1.4rem !important;
        }

        /* Radios horizontales en columna */
        [data-testid="stRadio"] > div {
            flex-direction: column !important;
        }

        /* Data editor scroll horizontal */
        [data-testid="stDataEditor"] {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }

        /* Botones full width */
        .stButton > button {
            width: 100% !important;
        }

        /* File uploader más amigable al tacto */
        [data-testid="stFileUploader"] {
            min-height: 80px;
        }

        /* Inputs más grandes para touch */
        .stTextInput > div > div > input {
            padding: 10px 12px !important;
            font-size: 16px !important;
        }

        .stTextArea > div > div > textarea {
            font-size: 15px !important;
        }

        /* Imagen de evidencia full width */
        [data-testid="stImage"] {
            width: 100% !important;
        }

        /* --- Cámara estilo Nativo en móvil --- */
        [data-testid="stCameraInput"] {
            width: 100% !important;
        }
        
        [data-testid="stCameraInput"] > label {
            display: none;
        }

        [data-testid="stCameraInput"] video {
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            width: 100% !important;
            height: auto !important;
            max-height: 80vh !important;
            object-fit: cover !important;
            border: 2px solid #3b82f6;
        }
        
        /* Ocultar elementos sobrantes del widget de cámara de Streamlit */
        [data-testid="stCameraInput"] > div > div > small {
            display: none;
        }
        
        /* Botones de cámara tipo nativo */
        [data-testid="stCameraInput"] button {
            width: 100% !important;
            height: 70px !important;
            font-size: 20px !important;
            font-weight: bold !important;
            margin-top: 15px !important;
            background-color: #3b82f6 !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }
    }

    /* === RESPONSIVE: entre 769 y 1024px (tablets) === */
    @media (min-width: 769px) and (max-width: 1024px) {
        .block-container {
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }
    }

    """ + preview_css + """
    </style>
    """
    st.markdown(responsive_css, unsafe_allow_html=True)

load_custom_css()

# ────────────────────────────────────────────────
# Session State Initialization
# ────────────────────────────────────────────────
# ────────────────────────────────────────────────
# USUARIOS AUTORIZADOS
# ────────────────────────────────────────────────
# Se leen desde .streamlit/secrets.toml para seguridad
try:
    USERS = st.secrets["users"]
except Exception:
    # Fallback para desarrollo local si no hay secrets
    USERS = {
        "admin": {"password": "admin", "nombre": "Administrador Local"}
    }

# ────────────────────────────────────────────────
# Session State Initialization
# ────────────────────────────────────────────────
# LOGIN TEMPORALMENTE DESACTIVADO
if "logged_in" not in st.session_state:
    st.session_state.logged_in = True
if "current_user" not in st.session_state:
    st.session_state.current_user = {"username": "admin", "nombre": "Administrador"}
if "login_error" not in st.session_state:
    st.session_state.login_error = False

# ── Cargar borrador local al iniciar (solo una vez por sesión) ──
if "local_draft_loaded" not in st.session_state:
    _had_draft = load_local_draft()
    if not _had_draft:
        st.session_state.local_draft_loaded = False

if "app_mode" not in st.session_state:
    st.session_state.app_mode = "inicio"  # "inicio" | "subida_rapida" | "reporte"

if "app_step" not in st.session_state:
    st.session_state.app_step = "formulario"  # "formulario" | "vista_previa" | "generado" (solo para modo reporte)

if "equipos_list" not in st.session_state:
    st.session_state.equipos_list = [
        {"item": 1, "equipo": "EXPLOSIMETRO", "marca": "KALLU", "modelo": "K-100A", "serie": "2108268", "fecha_cal": "11/11/2022"}
    ]

if "preview_data" not in st.session_state:
    st.session_state.preview_data = {}

if "preview_images" not in st.session_state:
    st.session_state.preview_images = []

if "camera_queue" not in st.session_state:
    st.session_state.camera_queue = []

if "form_photos" not in st.session_state:
    st.session_state.form_photos = []

if "last_camera_hash" not in st.session_state:
    st.session_state.last_camera_hash = None

if "camera_key" not in st.session_state:
    st.session_state.camera_key = 0

if "last_upload_hashes" not in st.session_state:
    st.session_state.last_upload_hashes = set()

if "synced_hashes" not in st.session_state:
    st.session_state.synced_hashes = set()


# ────────────────────────────────────────────────
# LISTA DE EQUIPOS PREDEFINIDOS
# ────────────────────────────────────────────────
EQUIPOS_PREDEFINIDOS = [
    {"equipo": "MULTIMETRO", "marca": "SANWA", "modelo": "CD772", "serie": "19115000442"},
    {"equipo": "MULTIMETRO", "marca": "AMPROBE", "modelo": "33XR-A", "serie": "20010105A"},
    {"equipo": "PINZA AMPERIMETRICA", "marca": "REDLINE", "modelo": "PM2016A", "serie": "S/N"},
    {"equipo": "PINZA AMPERIMETRICA", "marca": "FLUKE", "modelo": "375", "serie": "43931493"},
    {"equipo": "PINZA AMPERIMETRICA", "marca": "AMPROBE", "modelo": "AMP-330", "serie": "17013235"},
    {"equipo": "MEGOMETRO", "marca": "SANWA", "modelo": "MG1000", "serie": "21125400086"},
    {"equipo": "TELUROMETRO", "marca": "SANWA", "modelo": "PDR4000", "serie": "21035302290"},
    {"equipo": "EXPLOSIMETRO", "marca": "RKI", "modelo": "GX-3R", "serie": "418042128RN"},
    {"equipo": "EXPLOSIMETRO", "marca": "KALLU ELECTRONIC", "modelo": "K-100A", "serie": "2108268"},
    {"equipo": "OTDR", "marca": "F2H", "modelo": "FH5000", "serie": "E5FHAU1310"},
]

# import time # Ya importado arriba
# import config # Ya importado arriba

# ════════════════════════════════════════════════
#  PANTALLA DE LOGIN
# ════════════════════════════════════════════════
def render_login():
    """Pantalla de inicio de sesión premium."""

    # Logo centrado
    logo_b64 = ""
    try:
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
    except Exception:
        pass

    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" '
        'style="height:72px; width:auto; border-radius:12px; object-fit:contain;">'
        if logo_b64 else
        '<div style="width:72px;height:72px;background:#0056b2;border-radius:14px;'
        'display:flex;align-items:center;justify-content:center;margin:0 auto;">'
        '<span style="font-size:36px;">📝</span></div>'
    )

    st.markdown(f"""
    <div style="max-width:400px; margin:60px auto 0; padding:0 16px;">
        <div style="text-align:center; margin-bottom:32px;">
            {logo_html}
            <h1 style="margin:16px 0 4px; font-size:1.8rem; font-weight:800;
                       letter-spacing:-0.02em; color:#0F172A;">Reportes COG</h1>
            <p style="margin:0; font-size:14px; color:#64748B; font-weight:500;">
                Sistema de Gestión de Reportes · ICRT
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col_form, _ = st.columns([1, 2, 1])
    with col_form:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("""
            <div style="background:#fff; border:1px solid #E2E8F0; border-radius:16px;
                        padding:28px 24px 20px; box-shadow:0 4px 24px rgba(0,86,178,0.08);">
                <p style="font-size:13px; font-weight:700; text-transform:uppercase;
                          letter-spacing:0.08em; color:#64748B; margin:0 0 16px;">Iniciar Sesión</p>
            </div>
            """, unsafe_allow_html=True)

            usuario = st.text_input("👤 Usuario", placeholder="Ej: m.aucapoma",
                                    key="login_user_input")
            password = st.text_input("🔒 Contraseña", type="password",
                                     placeholder="Tu contraseña",
                                     key="login_pass_input")

            if st.session_state.login_error:
                st.error("❌ Usuario o contraseña incorrectos. Inténtalo de nuevo.")

            submitted = st.form_submit_button(
                "Entrar →", use_container_width=True, type="primary"
            )

        if submitted:
            user_data = USERS.get(usuario.strip().lower())
            if user_data and user_data["password"] == password:
                st.session_state.logged_in = True
                st.session_state.current_user = {
                    "username": usuario.strip().lower(),
                    "nombre": user_data["nombre"]
                }
                st.session_state.login_error = False
                st.rerun()
            else:
                st.session_state.login_error = True
                st.rerun()

    st.markdown("""
    <p style="text-align:center; margin-top:32px; font-size:12px; color:#94A3B8;">
        © 2025 ICRT · Acceso restringido al personal autorizado
    </p>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════
#  MODO: INICIO (MENÚ)
# ════════════════════════════════════════════════
def render_inicio():
    """Renderiza el menú de selección inicial (estilo stitch premium dashboard)."""

    user_info = st.session_state.get("current_user", {})
    nombre = user_info.get("nombre", "Usuario")
    username = user_info.get("username", "")
    hora = datetime.now().hour
    saludo = "Buenos días" if hora < 12 else ("Buenas tardes" if hora < 19 else "Buenas noches")
    iniciales = "".join([p[0].upper() for p in nombre.split()[:2]])

    # ── Header con Logo ──
    logo_html = ""
    try:
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                logo_html = f'<img src="data:image/png;base64,{b64}" style="height:48px; width:auto; border-radius:8px; object-fit:contain; margin-right:12px;">'
    except Exception:
        pass

    if not logo_html:
        logo_html = '<div style="width:48px; height:48px; background:#0056b2; border-radius:10px; display:flex; align-items:center; justify-content:center; margin-right:12px;"><span style="color:white; font-size:26px;">📝</span></div>'

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0 24px;">
        <div style="display:flex; align-items:center;">
            {logo_html}
            <div>
                <h1 style="margin:0; font-size:1.2rem; font-weight:800; letter-spacing:-0.02em; color:var(--text-primary);">{saludo}, {nombre.split()[0]}</h1>
                <p style="margin:0; font-size:13px; font-weight:600; color:var(--text-secondary);">@{username}</p>
            </div>
        </div>
        <div style="width:40px; height:40px; border-radius:50%; background:#0056B2; display:flex;
                    align-items:center; justify-content:center; box-shadow:0 2px 8px rgba(0,86,178,0.3);">
            <span style="font-size:14px; font-weight:800; color:white;">{iniciales}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Botón de Cerrar Sesión (sidebar) ──
    with st.sidebar:
        st.markdown(f"**👤 {nombre}**")
        st.caption(f"@{username}")
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.login_error = False
            st.rerun()

    # ── Continúa Reporte (Resume Active Draft) ──
    # Si hay fotos en el form o equipos listados, es probable que haya un reporte en progreso no guardado localmente todavía.
    active_form = len(st.session_state.get('form_photos', [])) > 0 or len(st.session_state.get('equipos_list', [])) > 0
    if active_form:
        st.markdown(f"""
        <div class="stitch-recent-report" style="border-left:4px solid var(--primary); margin-bottom:12px; background:var(--primary-light);">
            <div>
                <p class="stitch-recent-report-title">Reporte no terminado</p>
                <div class="stitch-recent-report-meta">
                    <span class="stitch-recent-report-status warning">En Progreso</span>
                    <span>{len(st.session_state.get('form_photos', []))} fotos | {len(st.session_state.get('equipos_list', []))} equipos añadidos</span>
                </div>
            </div>
            <span style="font-size:24px;">📝</span>
        </div>
        """, unsafe_allow_html=True)
        col_resume1, col_resume2 = st.columns([3, 1])
        with col_resume1:
            if st.button("Continuar Editando", use_container_width=True, type="primary"):
                st.session_state.app_mode = "reporte"
                if st.session_state.get('app_step') == 'generado':
                    st.session_state.app_step = "formulario"
                st.rerun()
        with col_resume2:
            if st.button("🗑️ Borrar", use_container_width=True):
                st.session_state.form_photos = []
                st.session_state.equipos_list = []
                st.session_state.pop("base_filename", None)
                st.session_state.pop("draft_version", None)
                st.rerun()
        st.markdown("<hr style='margin:16px 0 24px 0'>", unsafe_allow_html=True)

    # ── Dashboard (Stats) ──
    st.markdown("<p class='stitch-section-title'>Resumen de Actividad</p>", unsafe_allow_html=True)
    st.markdown("""
    <div class="stitch-stats-container">
        <div class="stitch-stat-item">
            <span class="stitch-stat-number success">85%</span>
            <span class="stitch-stat-label">Completados</span>
        </div>
        <div class="stitch-stat-item">
            <span class="stitch-stat-number warning">15%</span>
            <span class="stitch-stat-label">Pendientes</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Acciones Rápidas (Premium Cards) ──
    st.markdown("<p class='stitch-section-title' style='margin-top:24px;'>Acciones Principales</p>", unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("➕ Nuevo Reporte", use_container_width=True, type="primary", key="btn_inicio_new"):
            st.session_state.form_photos = []
            st.session_state.equipos_list = []
            # Resetear widget keys persistentes si es posible, aunque Streamlit lo maneja al no renderizarlos
            st.session_state.app_mode = "reporte"
            st.session_state.app_step = "formulario"
            st.rerun()
            
    with col_btn2:
        if st.button("📷 Subida Rápida", use_container_width=True, key="btn_inicio_cam"):
            st.session_state.app_mode = "subida_rapida"
            st.rerun()

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Reportes Recientes ──
    st.markdown("<p class='stitch-section-title'>Reportes Recientes</p>", unsafe_allow_html=True)
    
    try:
        import config
        drafts = get_cached_file_list(config.CLOUD_DRAFTS_PATH, extensions=['.json'])
        if not drafts:
            st.info("No hay borradores recientes guardados.")
        else:
            # Sort drafts (newest first assuming timestamps or alphabetical order puts newest last usually if sort reversed)
            recent_drafts = sorted(drafts, reverse=True)[:3]
            for r in recent_drafts:
                display_name = r.replace('.json', '')
                st.markdown(f"""
                <div class="stitch-recent-report">
                    <div>
                        <p class="stitch-recent-report-title">{display_name}</p>
                        <div class="stitch-recent-report-meta">
                            <span class="stitch-recent-report-status warning">Borrador</span>
                            <span>Guardado en nube</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"No se pudieron cargar recientes")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

    # ── Borradores en la Nube ──
    with st.expander("📂 Abrir borrador de la nube"):
        try:
            import config
            import importlib
            importlib.reload(config)
            if st.button("🔄 Actualizar lista", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

            drafts = get_cached_file_list(config.CLOUD_DRAFTS_PATH, extensions=['.json'])

            if not drafts:
                st.info("No hay borradores en la nube.")
            else:
                for d_name in drafts:
                    if st.button(f"📄 {d_name}", key=f"load_{d_name}", use_container_width=True):
                        with st.spinner(f"Cargando {d_name}..."):
                            load_draft_to_session(d_name)
                            st.session_state.app_mode = "reporte"
                            st.session_state.app_step = "formulario"
                            st.rerun()
        except Exception as e:
            st.error(f"Error al listar borradores: {e}")

    # ── Floating Bottom Navigation Bar ──
    st.markdown("<div class='bottom-nav-spacer'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div id='bottom-nav-marker'></div>", unsafe_allow_html=True)
        col_nav1, col_nav2, col_nav3 = st.columns(3)
        with col_nav1:
            st.button("🏠 Inicio", use_container_width=True, key="nav_home_btn_st")
        with col_nav2:
             if st.button("➕ Crear", use_container_width=True, key="nav_rep_btn_st"):
                 st.session_state.form_photos = []
                 st.session_state.equipos_list = []
                 st.session_state.app_mode = "reporte"
                 st.session_state.app_step = "formulario"
                 st.rerun()
        with col_nav3:
             if st.button("👤 Perfil", use_container_width=True, key="nav_prof_btn_st"):
                 st.toast("Página de perfil no implementada aún.")

def load_draft_to_session(draft_name):
    """Descarga un JSON de la nube y restaura el session_state."""
    import json
    import base64
    from datetime import datetime
    import config
    import importlib
    importlib.reload(config)
    
    client = get_cloud_client()
    remote_path = f"{config.CLOUD_DRAFTS_PATH}/{draft_name}"
    local_path = os.path.join("outputs", draft_name)
    
    if client.download_file(remote_path, local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            draft = json.load(f)
            fd = draft.get("form_data", {})
            
            # Recuperar info del borrador
            st.session_state["base_filename"] = draft_name.replace(".json", "")
            st.session_state["draft_version"] = draft.get("version", 0)
            st.session_state["f_unique"] = draft.get("unique_code", "")
            
            # 1. Restaurar campos básicos del formulario
            st.session_state["f_actividad"] = fd.get("activity", "")
            st.session_state["f_tipo"] = fd.get("activity_type", "Mantenimiento")
            st.session_state["f_lugar"] = fd.get("place", "")
            st.session_state["f_pers"] = fd.get("personnel", "")
            st.session_state["f_cli"] = fd.get("client", "")
            st.session_state["f_est"] = fd.get("status", "Culminado")
            st.session_state["f_conf"] = fd.get("client_approval", "Conforme")
            st.session_state["f_sup"] = fd.get("supervisor", "")
            st.session_state["f_cod"] = fd.get("codigo", "")
            st.session_state["f_nom"] = fd.get("nombre", "")
            st.session_state["f_td"] = fd.get("total_days", 1)
            st.session_state["f_da"] = fd.get("current_day", 1)
            st.session_state["f_ar"] = fd.get("actual_progress", 0.0)
            st.session_state["f_resumen"] = fd.get("summary", "")
            st.session_state["f_obs"] = fd.get("observations", "")
            st.session_state["f_conc"] = fd.get("conclusions", "")
            
            # Fechas (convertir de string a date)
            try:
                st.session_state["f_fi"] = datetime.strptime(fd.get("start_date", ""), "%Y-%m-%d").date()
                st.session_state["f_ff"] = datetime.strptime(fd.get("end_date", ""), "%Y-%m-%d").date()
            except:
                pass
            
            # 2. Restaurar Equipos
            st.session_state.equipos_list = []
            eq_names = fd.get("equipment_name", [])
            for i in range(len(eq_names)):
                st.session_state.equipos_list.append({
                    "item": fd.get("equipment_item", [])[i] if i < len(fd.get("equipment_item", [])) else i+1,
                    "equipo": eq_names[i],
                    "marca": fd.get("equipment_brand", [])[i] if i < len(fd.get("equipment_brand", [])) else "",
                    "modelo": fd.get("equipment_model", [])[i] if i < len(fd.get("equipment_model", [])) else "",
                    "serie": fd.get("equipment_serial", [])[i] if i < len(fd.get("equipment_serial", [])) else "",
                    "fecha_cal": fd.get("equipment_cal_date", [])[i] if i < len(fd.get("equipment_cal_date", [])) else ""
                })

            # 3. Restaurar Fotos
            st.session_state.form_photos = []
            
            # Restaurar fotos locales del JSON
            for p in draft.get("local_photos", []):
                try:
                    img_bytes = base64.b64decode(p["bytes_b64"])
                    st.session_state.form_photos.append({
                        "id": f"local_{int(time.time())}_{p['name']}",
                        "type": "local",
                        "name": p["name"],
                        "bytes": img_bytes,
                        "caption": p.get("caption", ""),
                        "date": datetime.strptime(p["date"], "%Y-%m-%d").date() if p.get("date") else datetime.now().date()
                    })
                except:
                    pass
            
            # Restaurar fotos que estaban en la nube
            cloud_photos = fd.get("cloud_photos", [])
            captions = fd.get("photo_captions", [])
            dates = fd.get("photo_dates", [])
            
            # El form_data guardado en el reporte suele tener las clouds al final del listado total de captions/dates
            # Pero para ser más precisos, en el controlador las clouds tienen un offset
            # Vamos a intentar reconstruirlas si el cloud_photos existe
            offset = len(draft.get("local_photos", []))
            for i, c_name in enumerate(cloud_photos):
                st.session_state.form_photos.append({
                    "id": f"cloud_{int(time.time())}_{c_name}",
                    "type": "cloud",
                    "name": c_name,
                    "caption": captions[offset + i] if (offset + i) < len(captions) else "",
                    "date": datetime.strptime(dates[offset + i], "%Y-%m-%d").date() if (offset + i) < len(dates) else datetime.now().date()
                })
            
            return True
    return False

# ════════════════════════════════════════════════
#  MODO: SUBIDA RÁPIDA DE FOTOS
# ════════════════════════════════════════════════
def render_subida_rapida():
    """Interfaz para subir fotos rápidamente (estilo stitch photo_management)."""

    # ── Header ──
    hcol1, hcol2 = st.columns([1, 5])
    with hcol1:
        if st.button("⬅️ Inicio", key="btn_back_subida"):
            st.session_state.app_mode = "inicio"
            st.rerun()
    with hcol2:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; padding:4px 0;">
            <span style="font-size:26px;">📸</span>
            <h2 style="margin:0; font-size:1.25rem; font-weight:700;">Subida Rápida</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stitch-info-box" style="margin:12px 0 24px;">
        <span style="margin-top:2px; font-size:20px;">ℹ️</span>
        <p style="margin:0; font-size:13px; color:#1e40af;">
        Captura fotos aquí. Abajo también puedes adjuntar desde tu galería nativa.</p>
    </div>
    """, unsafe_allow_html=True)

    # Cámara a pantalla completa
    st.markdown("""
    <p style="font-size:12px; font-weight:700; text-transform:uppercase;
                letter-spacing:0.06em; color:#64748b; margin-bottom:8px;">
        📷 Capturadora</p>
    """, unsafe_allow_html=True)
    
    cam_key = f"cam_input_{st.session_state.camera_key}"
    camera_file = st.camera_input("Touch to capture", key=cam_key, label_visibility="collapsed")

    if camera_file:
        import hashlib
        img_bytes = camera_file.getvalue()
        img_hash = hashlib.md5(img_bytes).hexdigest()

        if img_hash != st.session_state.get("last_camera_hash"):
            st.session_state.camera_queue.append({
                "id": f"cam_{int(time.time())}_{len(st.session_state.camera_queue)}",
                "bytes": img_bytes,
                "name": f"capsula_{int(time.time())}.jpg"
            })
            st.session_state.last_camera_hash = img_hash
            st.session_state.camera_key += 1
            st.toast("📸 Foto rápida capturada")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <p style="font-size:12px; font-weight:700; text-transform:uppercase;
                letter-spacing:0.06em; color:#64748b; margin-bottom:8px;">
        📂 Subir desde Galería</p>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Galería Nativa",
        accept_multiple_files=True,
        type=['jpg', 'jpeg', 'png'],
        key="cam_file_uploader",
        label_visibility="collapsed"
    )

    if uploaded_files:
        import hashlib
        nuevos = 0
        for f in uploaded_files:
            f_bytes = f.getvalue()
            f_hash = hashlib.md5(f_bytes).hexdigest()

            if f_hash not in st.session_state.last_upload_hashes:
                st.session_state.camera_queue.append({
                    "id": f"file_{int(time.time())}_{f.name}",
                    "bytes": f_bytes,
                    "name": f.name
                })
                st.session_state.last_upload_hashes.add(f_hash)
                nuevos += 1

        if nuevos > 0:
            st.toast(f"✅ {nuevos} fotos de alta resolución añadidas")
            st.rerun()

    # ── Lista de Espera ──
    if st.session_state.camera_queue:
        st.markdown("<hr>", unsafe_allow_html=True)

        hdr_c1, hdr_c2 = st.columns([3, 1])
        with hdr_c1:
            st.markdown(
                f"<p class='stitch-section-title'>📋 Lista de espera "
                f"<span style='font-weight:500; color:#64748b;'>"
                f"({len(st.session_state.camera_queue)} fotos)</span></p>",
                unsafe_allow_html=True
            )
        with hdr_c2:
            if st.button("🗑️ Limpiar", use_container_width=True, key="btn_limpiar"):
                st.session_state.camera_queue = []
                st.session_state.last_camera_hash = None
                st.session_state.last_upload_hashes = set()
                st.rerun()

        cols = st.columns(min(len(st.session_state.camera_queue), 4))
        to_delete = None

        for idx, item in enumerate(st.session_state.camera_queue):
            with cols[idx % 4]:
                st.image(item["bytes"], use_column_width=True)
                if st.button("🗑️", key=f"del_cam_{item['id']}", help="Quitar de la lista"):
                    to_delete = idx

        if to_delete is not None:
            st.session_state.camera_queue.pop(to_delete)
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("☁️  SINCRONIZAR CON LA NUBE", type="primary", use_container_width=True, key="btn_sync"):
            import importlib
            import hashlib
            import app.services.nextcloud_service as ns_mod
            importlib.reload(ns_mod)
            from app.services.nextcloud_service import NextcloudService
            cloud = NextcloudService()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            subidos = 0
            duplicados = 0
            with st.spinner("Cargando..."):
                items_to_remove = []
                for i, item in enumerate(st.session_state.camera_queue):
                    fname = item["name"]

                    img_hash = hashlib.md5(item["bytes"]).hexdigest()
                    if img_hash in st.session_state.synced_hashes:
                        items_to_remove.append(i)
                        duplicados += 1
                        continue

                    clean_name = "".join(c for c in fname if c.isalnum() or c in "._-").replace(" ", "_")
                    remote_name = f"{timestamp}_QUICK_{i}_{clean_name}"
                    if not remote_name.lower().endswith(".jpg"):
                        remote_name += ".jpg"

                    remote_path = f"{config.CLOUD_PHOTOS_PATH}/{remote_name}"

                    success = False
                    intentos = 0
                    while not success and intentos < 3:
                        intentos += 1
                        success = cloud.upload_bytes(item["bytes"], remote_path)
                        if success:
                            st.session_state.synced_hashes.add(img_hash)
                            items_to_remove.append(i)
                            subidos += 1
                        else:
                            time.sleep(1)

            msg = f"Se subieron {subidos} fotos a la nube."
            if duplicados > 0:
                msg += f" ({duplicados} duplicadas omitidas)"
            st.success(msg)
            st.session_state.camera_queue = []
            st.session_state.last_upload_hashes = set()
            get_cached_file_list.clear()
            st.rerun()



# ════════════════════════════════════════════════
#  PASO 1: FORMULARIO
# ════════════════════════════════════════════════
def render_formulario():
    """Renderiza el formulario de entrada de datos (estilo stitch create_report)."""

    # ── Botón de Retorno ──
    col_back, _ = st.columns([1, 4])
    if col_back.button("⬅️ Inicio", key="btn_back_form"):
        st.session_state.app_mode = "inicio"
        st.rerun()

    # ── Hero / Header ──
    logo_html = ""
    try:
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                logo_html = f'<img src="data:image/png;base64,{b64}" style="height:48px; border-radius:8px; margin-right:14px;">'
    except Exception:
        pass

    if not logo_html:
        logo_html = '<div style="width:48px; height:48px; background:#0056b2; border-radius:10px; display:flex; align-items:center; justify-content:center; margin-right:14px;"><span class="material-symbols-outlined" style="color:white; font-size:26px;">description</span></div>'

    st.markdown(f"""
    <div class="stitch-hero">
        <div style="display:flex; align-items:center;">
            {logo_html}
            <div>
                <h1 style="margin:0; font-size:1.4rem; font-weight:800; letter-spacing:-0.02em;">Reporte Técnico</h1>
                <p style="margin:0; font-size:12px; font-weight:600; text-transform:uppercase;
                          letter-spacing:0.08em; color:#64748b;">Módulo de Inspección</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Barra de pasos ──
    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:12px; font-weight:700; color:#0056b2; text-transform:uppercase; letter-spacing:0.06em;">Paso 1 de 4: Información General</span>
            <span style="font-size:12px; font-weight:600; color:#64748b;">25% Completado</span>
        </div>
        <div class="stitch-step-bar">
            <div class="stitch-step-bar-fill" style="width:25%;"></div>
        </div>
        <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:6px; margin-top:8px;">
            <div>
                <div style="height:3px; background:#0056b2; border-radius:99px;"></div>
                <p style="font-size:10px; font-weight:700; color:#0056b2; text-transform:uppercase; margin:4px 0 0;">General</p>
            </div>
            <div>
                <div style="height:3px; background:#e2e8f0; border-radius:99px;"></div>
                <p style="font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase; margin:4px 0 0;">Avance</p>
            </div>
            <div>
                <div style="height:3px; background:#e2e8f0; border-radius:99px;"></div>
                <p style="font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase; margin:4px 0 0;">Evidencia</p>
            </div>
            <div>
                <div style="height:3px; background:#e2e8f0; border-radius:99px;"></div>
                <p style="font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase; margin:4px 0 0;">Firma</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Datos generales ---
    with st.expander("📝 Datos Generales", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            actividad = st.text_input("Actividad", value="INTEGRACIÓN Y PUESTA EN SERVICIO DE PLACA LATERAL EN GABINETE DE CONTROL DE LA VÁLVULA XV-10020", key="f_actividad")
            tipo_actividad = st.selectbox("Tipo de actividad",
                                          ["Mantenimiento", "Conexionado", "Cableado", "Instalación", "Canalizado", "Otros"], key="f_tipo")
            lugar = st.text_input("Lugar", "Zona Costa", key="f_lugar")
            fecha_inicio = st.date_input("Fecha inicio", datetime.now().date(), key="f_fi")
            fecha_fin = st.date_input("Fecha fin", datetime.now().date(), key="f_ff")
            personal = st.text_input("Personal involucrado", "Miguel Aucapoma, Luis Huayllani, Carlos Diaz", key="f_pers")

        with col2:
            cliente = st.text_input("Cliente", "Transportadora de Gas del Perú", key="f_cli")
            estado = st.radio("Estado", ["Culminado", "En Proceso", "Cancelado"], horizontal=True, key="f_est")
            conformidad = st.radio("Conformidad del cliente", ["Conforme", "No Conforme", "No Sabe"], horizontal=True, key="f_conf")
            supervisor = st.text_input("Supervisor TGP", "Bruno Rojas", key="f_sup")

        # Identificación del reporte
        st.markdown("---")
        c_rep1, c_rep2 = st.columns(2)
        with c_rep1:
            codigo_reporte = st.text_input("Código del reporte", "XV-10020", key="f_cod")
        with c_rep2:
            nombre_reporte = st.text_input("Nombre del reporte", "Integración placa lateral", key="f_nom")

    # --- Avance del Proyecto ---
    with st.expander("📊 Avance del Proyecto"):
        col_prog1, col_prog2, col_prog3 = st.columns(3)
        with col_prog1:
            total_dias = st.number_input("Días Totales (100%)", min_value=1, value=5, key="f_td")
        with col_prog2:
            dia_actual = st.number_input("Día Actual", min_value=1, max_value=total_dias, value=1, key="f_da")
        with col_prog3:
            avance_real = st.number_input("Avance Real (%)", min_value=0.0, max_value=100.0, value=20.0, step=0.1, key="f_ar")

    # Resumen
    with st.expander("📄 Resumen de Actividad"):
        resumen = st.text_area("Descripción detallada",
            "A solicitud del cliente se requiere la instalación y puesta en servicio de placa lateral en gabinete de control de la válvula XV-10020, la instalación del sistema eléctrico será alimentado desde TABLERO TRANSFERENCIA AUTOMÁTICA (TTA).",
            height=100, key="f_resumen")

    # --- Evidencia fotográfica ---
    with st.expander("📷 Evidencia Fotográfica", expanded=True):
        st.info("Añada todas las fotos que necesite (locales o de la nube). Se guardarán en una lista unificada.")
        
        c_src1, c_src2 = st.columns(2)
        with c_src1:
            uploaded_files = st.file_uploader("Subir fotos locales", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="f_imgs")
            if uploaded_files:
                if st.button("➕ Añadir fotos locales al reporte", use_container_width=True):
                    for f in uploaded_files:
                        f.seek(0)
                        bytes_data = f.read()
                        st.session_state.form_photos.append({
                            "id": f"local_{int(time.time())}_{f.name}",
                            "type": "local",
                            "name": f.name,
                            "bytes": bytes_data,
                            "caption": "Se realizó la instalación...",
                            "date": datetime.now().date()
                        })
                    st.toast("✅ Fotos locales añadidas")
                    st.rerun()
        
        with c_src2:
            # Botón de refresco manual
            if st.button("🔄 Actualizar fotos de la nube", use_container_width=True, key="btn_refresh_cloud_photos"):
                get_cached_file_list.clear()
                st.rerun()

            with st.spinner("Cargando fotos de la nube..."):
                fotos_nube = get_cached_file_list(config.CLOUD_PHOTOS_PATH)

            if fotos_nube:
                st.caption(f"☁️ {len(fotos_nube)} fotos disponibles en la nube")
                seleccionadas = st.multiselect("Seleccionar de la nube", fotos_nube, key="f_cloud_sel")
                if seleccionadas:
                    if st.button("➕ Añadir fotos de nube al reporte", use_container_width=True, key="btn_add_cloud_photos"):
                        for cloud_name in seleccionadas:
                            st.session_state.form_photos.append({
                                "id": f"cloud_{int(time.time())}_{cloud_name}",
                                "type": "cloud",
                                "name": cloud_name,
                                "caption": "Evidencia desde la nube...",
                                "date": datetime.now().date()
                            })
                        st.toast("✅ Fotos de nube añadidas")
                        st.rerun()
            else:
                st.info("Sin fotos en la nube aún. Usa 'Subida Rápida' para subir fotos.")

        # --- Mostrar lista unificada de evidencias ---
        if st.session_state.form_photos:
            st.markdown("---")
            st.subheader(f"🖼️ Evidencias en el reporte ({len(st.session_state.form_photos)})")
            
            to_delete_form = None
            for idx, p in enumerate(st.session_state.form_photos):
                st.markdown(f"**Evidencia {idx+1} - {p['type'].upper()}**")
                c_img, c_desc, c_del = st.columns([1, 2, 0.3])
                
                with c_img:
                    if p["type"] == "local":
                        st.image(p["bytes"], use_column_width=True)
                    else:
                        remote_path = f"{config.CLOUD_PHOTOS_PATH}/{p['name']}"
                        with st.spinner("Cargando nube..."):
                            cloud_bytes = get_cached_photo(remote_path)
                            if cloud_bytes:
                                st.image(cloud_bytes, use_column_width=True)
                            else:
                                st.error("No disponible")
                
                with c_desc:
                    # Vincular directamente al session_state
                    p["caption"] = st.text_input(f"Descripción", value=p["caption"], key=f"form_cap_{p['id']}")
                    p["date"] = st.date_input(f"Fecha", value=p["date"], key=f"form_date_{p['id']}")
                
                with c_del:
                    st.write("") # Alineación
                    if st.button("🗑️", key=f"form_del_{p['id']}", help="Eliminar de la lista"):
                        to_delete_form = idx
                
                st.divider()
            
            if to_delete_form is not None:
                st.session_state.form_photos.pop(to_delete_form)
                st.rerun()
        else:
            st.warning("Aún no ha añadido fotos a la evidencia.")


    # --- Equipos de medición ---
    with st.expander("🔧 Equipos de Medición"):
        st.markdown("Agregue equipos desde la lista o edite la tabla.")

        opciones_equipos = [f"{e['equipo']} - {e['marca']} - {e['modelo']}" for e in EQUIPOS_PREDEFINIDOS]
        seleccion = st.selectbox("Seleccionar Equipo", ["Seleccione un equipo..."] + opciones_equipos, key="f_sel_eq")

        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("➕ Agregar Equipo"):
                if seleccion != "Seleccione un equipo...":
                    idx = opciones_equipos.index(seleccion)
                    equipo_data = EQUIPOS_PREDEFINIDOS[idx]
                    nuevo_item = {
                        "item": len(st.session_state.equipos_list) + 1,
                        "equipo": equipo_data["equipo"],
                        "marca": equipo_data["marca"],
                        "modelo": equipo_data["modelo"],
                        "serie": equipo_data["serie"],
                        "fecha_cal": datetime.now().strftime("%d/%m/%Y")
                    }
                    st.session_state.equipos_list.append(nuevo_item)
                    # Forzar persistencia inmediata
                    st.rerun()

        equipos_data = st.data_editor(
            st.session_state.equipos_list,
            num_rows="dynamic",
            column_config={
                "item": "Item",
                "equipo": "Equipo",
                "marca": "Marca",
                "modelo": "Modelo",
                "serie": "Serie",
                "fecha_cal": "Fecha Calibración"
            },
            key="editor_equipos"
        )

    # --- Observaciones y conclusiones ---
    with st.expander("📝 Conclusiones y Observaciones"):
        observaciones = st.text_area("Observaciones", height=100, key="f_obs")
        conclusiones = st.text_area("Conclusiones", height=100, key="f_conc")

    # ── AUTOSAVE LOCAL (se ejecuta en cada render del formulario) ──
    save_local_draft()
    _saved_at = st.session_state.get("local_draft_saved_at", "")
    _ts = datetime.now().strftime("%H:%M:%S")
    st.markdown(
        f'<p style="font-size:11px; color:#94a3b8; text-align:right; margin:0;">'
        f'💾 Borrador guardado localmente · {_ts}</p>',
        unsafe_allow_html=True
    )
    st.session_state["local_draft_saved_at"] = _ts

    # ── Botón Vista Previa (Móvil) ──
    st.markdown("---")
    st.markdown("### 👁️ Vista Previa del Reporte")
    st.caption("Revise los datos antes de generar el PDF. Podrá editar campos en la vista previa.")

    st.markdown("<div class='has-floating-bar'></div>", unsafe_allow_html=True)
    
    col_btn_prev, col_btn_gen = st.columns([1, 1])
    with col_btn_prev:
        usar_vista_previa = st.toggle("🔍 Usar Vista Previa", value=True)
    with col_btn_gen:
        btn_text = "Siguiente: Ver Vista Previa" if usar_vista_previa else "🚀 Generar PDF Final"
        btn_type = "secondary" if usar_vista_previa else "primary"
        submit_btn = st.button(btn_text, type=btn_type, use_container_width=True)

    if submit_btn:
        if not st.session_state.form_photos:
            st.error("Debe añadir al menos una imagen de evidencia.")
        else:
            # Guardar datos en session_state para la vista previa o generación
            form_data = {
                "activity": actividad,
                "activity_type": tipo_actividad,
                "place": lugar,
                "start_date": fecha_inicio,
                "end_date": fecha_fin,
                "personnel": personal,
                "client": cliente,
                "status": estado,
                "client_approval": conformidad,
                "summary": resumen,
                "supervisor": supervisor,
                "codigo": codigo_reporte,
                "nombre": nombre_reporte,
                "observations": observaciones,
                "conclusions": conclusiones,
                "total_days": total_dias,
                "current_day": dia_actual,
                "actual_progress": avance_real,
                "base_filename": st.session_state.get("base_filename"),
                "draft_version": st.session_state.get("draft_version", 0),
                "unique_code": st.session_state.get("f_unique", "")
            }

            # Equipos
            form_data["equipment_item"] = [e["item"] for e in equipos_data]
            form_data["equipment_name"] = [e["equipo"] for e in equipos_data]
            form_data["equipment_brand"] = [e["marca"] for e in equipos_data]
            form_data["equipment_model"] = [e["modelo"] for e in equipos_data]
            form_data["equipment_serial"] = [e["serie"] for e in equipos_data]
            form_data["equipment_cal_date"] = [e["fecha_cal"] for e in equipos_data]

            if usar_vista_previa:
                st.session_state.preview_data = form_data
                st.session_state.preview_photos = st.session_state.form_photos
                st.session_state.preview_images = []
                st.session_state.app_step = "vista_previa"
                st.rerun()
            else:
                data = form_data
                ordered_captions = []
                ordered_dates = []
                ordered_cloud = []
                ordered_local_files_data = []

                class FakeUploadedFile:
                    def __init__(self, name, b): self.name = name; self.b = b
                    def read(self): return self.b
                    def seek(self, p): pass

                for p in st.session_state.get("form_photos", []):
                    ordered_captions.append(p["caption"])
                    ordered_dates.append(p["date"])
                    if p["type"] == "local":
                        ordered_local_files_data.append(FakeUploadedFile(p["name"], p["bytes"]))
                    else:
                        ordered_cloud.append(p["name"])

                data["photo_captions"] = ordered_captions
                data["photo_dates"] = ordered_dates
                data["cloud_photos"] = ordered_cloud

                with st.spinner("Generando PDF final y subiendo a la nube..."):
                    import importlib
                    import app.controllers.report_controller as ctrl_mod
                    importlib.reload(ctrl_mod)
                    pdf_path = ctrl_mod.create_report_from_form_data(data, ordered_local_files_data, is_preview=False)

                st.session_state.pdf_path = pdf_path
                
                # Limpiar sesión
                st.session_state.form_photos = []
                st.session_state.equipos_list = []
                st.session_state.camera_queue = []
                st.session_state.pop("base_filename", None)
                st.session_state.pop("draft_version", None)
                st.session_state.pop("f_unique", None)
                
                st.session_state.app_step = "generado"
                st.rerun()


# ════════════════════════════════════════════════
#  PASO 2: VISTA PREVIA EDITABLE
# ════════════════════════════════════════════════
def render_vista_previa():
    """Renderiza la vista previa editable del reporte."""
    data = st.session_state.preview_data
    images = st.session_state.preview_images

    # Header con botones de navegación
    col_back, col_title, col_gen = st.columns([1, 2, 1])
    with col_back:
        if st.button("⬅️ Volver a Editar", use_container_width=True):
            st.session_state.app_step = "formulario"
            st.rerun()
    with col_title:
        st.markdown("<h2 style='text-align:center; margin:0;'>👁️ Vista Previa del Reporte</h2>", unsafe_allow_html=True)
    with col_gen:
        generate_clicked = st.button("🚀 Generar PDF", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div class="stitch-alert-warning">
        <span class="material-symbols-outlined">warning</span>
        <div>
            <p class="stitch-alert-warning-title">¡Atención!</p>
            <p class="stitch-alert-warning-text">Verifica que todos los datos y fotos sean correctos. Los cambios se reflejarán en el PDF final.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PREVIEW HTML ──
    # Calcular avance esperado
    total_days = data.get("total_days", 1)
    current_day = data.get("current_day", 1)
    actual_progress = data.get("actual_progress", 0)
    expected_progress = (100.0 / total_days) * current_day if total_days > 0 else 0

    threshold_yellow = expected_progress * 0.85
    if actual_progress >= expected_progress:
        progress_color = "green"
        progress_label = "ÓPTIMO"
    elif actual_progress >= threshold_yellow:
        progress_color = "yellow"
        progress_label = "TOLERABLE"
    else:
        progress_color = "red"
        progress_label = "CRÍTICO"

    # Formatear fechas
    def fmt_date(d):
        if isinstance(d, date):
            return d.strftime("%d/%m/%Y")
        return str(d)

    # --- Vista previa HTML (ligera, funciona en móvil) ---
    st.markdown("---")
    col_edit, col_preview_html = st.columns([1, 1])

    with col_preview_html:
        st.markdown("### 📄 Vista Previa del Reporte")

        preview_photos_list = st.session_state.get("preview_photos", [])

        # --- Datos generales usando st.markdown en bloques pequeños ---
        st.markdown("#### ICRT 001 TI CO FO 0011")
        st.caption("REPORTE DE ACTIVIDADES Y EVENTOS")
        st.markdown("---")

        st.markdown(f"**Actividad:** {data.get('activity', '')}")
        st.markdown(f"**Tipo:** {data.get('activity_type', '')}")
        st.markdown(f"**Lugar:** {data.get('place', '')}")
        st.markdown(f"**Fecha:** {fmt_date(data.get('start_date'))} — {fmt_date(data.get('end_date'))}")
        st.markdown(f"**Personal:** {data.get('personnel', '')}")
        st.markdown(f"**Cliente:** {data.get('client', '')}")
        st.markdown(f"**Estado:** {data.get('status', '')}")
        st.markdown(f"**Conformidad:** {data.get('client_approval', '')}")
        st.markdown(f"**Supervisor:** {data.get('supervisor', '')}")

        st.markdown("---")

        # --- Avance ---
        st.markdown("#### 📊 Avance")
        st.markdown(f"Días: **{current_day}/{total_days}** — Esperado: **{expected_progress:.1f}%** — Real: **{actual_progress:.1f}%** — **{progress_label}**")
        st.progress(min(actual_progress / 100.0, 1.0))
        if progress_color == "green":
            st.success(f"✅ {progress_label}")
        elif progress_color == "yellow":
            st.warning(f"⚠️ {progress_label}")
        else:
            st.error(f"🔴 {progress_label}")

        st.markdown("---")

        # --- Resumen ---
        st.markdown("#### 📝 Resumen")
        st.markdown(data.get('summary', ''))

        st.markdown("---")

        # --- Evidencia fotográfica con thumbnails ---
        st.markdown(f"#### 📷 Evidencia Fotográfica ({len(preview_photos_list)} fotos)")
        if preview_photos_list:
            thumb_cols = st.columns(min(len(preview_photos_list), 3))
            for idx_p, ph in enumerate(preview_photos_list):
                with thumb_cols[idx_p % 3]:
                    if ph["type"] == "local" and ph.get("bytes"):
                        st.image(ph["bytes"], caption=f"Foto {idx_p+1}: {ph.get('caption', '')[:40]}", use_column_width=True)
                    elif ph["type"] == "cloud":
                        remote_path = f"{config.CLOUD_PHOTOS_PATH}/{ph['name']}"
                        cloud_bytes = get_cached_photo(remote_path)
                        if cloud_bytes:
                            st.image(cloud_bytes, caption=f"Foto {idx_p+1}: {ph.get('caption', '')[:40]}", use_column_width=True)
                        else:
                            st.info(f"☁️ {ph['name']}")
                    st.caption(f"📅 {fmt_date(ph.get('date', ''))}")
        else:
            st.info("Sin evidencia fotográfica")

        st.markdown("---")

        # --- Equipos como dataframe nativo ---
        eq_names_preview = data.get("equipment_name", [])
        if eq_names_preview:
            st.markdown("#### 🔧 Equipos de Medición")
            import pandas as pd
            eq_df = pd.DataFrame({
                "Item": data.get('equipment_item', list(range(1, len(eq_names_preview)+1))),
                "Equipo": eq_names_preview,
                "Marca": data.get('equipment_brand', ['']*len(eq_names_preview)),
                "Modelo": data.get('equipment_model', ['']*len(eq_names_preview)),
                "Serie": data.get('equipment_serial', ['']*len(eq_names_preview)),
            })
            st.dataframe(eq_df, use_container_width=True, hide_index=True)
            st.markdown("---")

        # --- Observaciones y conclusiones ---
        st.markdown("#### 📝 Observaciones")
        st.markdown(data.get('observations', '') or '—')
        st.markdown("#### ✅ Conclusiones")
        st.markdown(data.get('conclusions', '') or '—')

        st.info("👆 Esta es una vista previa rápida. Use el botón **🚀 Generar PDF** para crear el documento final.")

    with col_edit:
        # ═══════════════════════════════════════
        #  ENCABEZADO DEL REPORTE
        # ═══════════════════════════════════════
        st.markdown("#### ICRT 001 TI CO FO 0011 — Versión 2")
        st.markdown("## 📄 REPORTE DE ACTIVIDADES Y EVENTOS")
        st.caption("Toda la información contenida en el presente documento es confidencial y de propiedad de ICRT, estando prohibida su reproducción total o parcial sin autorización previa de la empresa.")
        st.markdown("---")

        # ═══════════════════════════════════════
        #  DATOS GENERALES (editables)
        # ═══════════════════════════════════════
        st.markdown("### 📋 Datos Generales")

        edited_activity = st.text_input("Actividad", value=data.get("activity", ""), key="prev_actividad")

        col_t, col_l = st.columns(2)
        with col_t:
            edited_tipo = st.text_input("Tipo de Actividad", value=data.get("activity_type", ""), key="prev_tipo")
        with col_l:
            edited_lugar = st.text_input("Lugar", value=data.get("place", ""), key="prev_lugar")

        col_f, col_p = st.columns(2)
        with col_f:
            st.text_input("Fecha", value=f"{fmt_date(data.get('start_date'))} al {fmt_date(data.get('end_date'))}", key="prev_fecha", disabled=True)
        with col_p:
            edited_personal = st.text_input("Personal Involucrado", value=data.get("personnel", ""), key="prev_personal")

        col_c, col_e = st.columns(2)
        with col_c:
            edited_cliente = st.text_input("Cliente", value=data.get("client", ""), key="prev_cliente")
        with col_e:
            edited_estado = st.text_input("Estado", value=data.get("status", ""), key="prev_estado")

        edited_conformidad = st.text_input("Conformidad del Cliente", value=data.get("client_approval", ""), key="prev_conformidad")

        st.markdown("---")

        # ═══════════════════════════════════════
        #  AVANCE DEL PROYECTO
        # ═══════════════════════════════════════
        st.markdown("### 📊 Avance del Proyecto")

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Días Totales", total_days)
        with col_m2:
            st.metric("Día Actual", current_day)
        with col_m3:
            st.metric("Avance Esperado", f"{expected_progress:.1f}%")
        with col_m4:
            st.metric("Avance Real", f"{actual_progress:.1f}%")

        # Barra de progreso nativa
        st.progress(min(actual_progress / 100.0, 1.0))

        # Semáforo de estado
        if progress_color == "green":
            st.success(f"✅ Estado: **{progress_label}** — Cumple o supera lo esperado")
        elif progress_color == "yellow":
            st.warning(f"⚠️ Estado: **{progress_label}** — Ligeramente por debajo del promedio")
        else:
            st.error(f"🔴 Estado: **{progress_label}** — Retraso significativo")

        st.markdown("---")

        # ═══════════════════════════════════════
        #  RESUMEN (editable)
        # ═══════════════════════════════════════
        st.markdown("### 📝 Resumen")
        edited_summary = st.text_area("Edite el resumen de actividad", value=data.get("summary", ""), height=100, key="prev_summary")

        st.markdown("---")

        # ═══════════════════════════════════════
        #  EVIDENCIA FOTOGRÁFICA
        # ═══════════════════════════════════════
        st.markdown("### 📷 Evidencia Fotográfica")
        st.caption("Organiza tus fotos. Usa las flechas para cambiar el orden o el botón rojo para quitar una foto.")

        preview_photos = st.session_state.get("preview_photos", [])
        updated_photos = []

        for i, photo in enumerate(preview_photos):
            st.markdown(f"**Evidencia {i+1} — {'☁️ Nube' if photo['type'] == 'cloud' else '💻 Local'}**")
            
            c_img, c_desc, c_actions = st.columns([1.5, 2, 0.5])
            
            with c_img:
                if photo["type"] == "local":
                    st.image(photo["bytes"], use_column_width=True)
                else:
                    # Cloud image with caching
                    remote_path = f"{config.CLOUD_PHOTOS_PATH}/{photo['name']}"
                    try:
                        with st.spinner("..."):
                            cloud_bytes = get_cached_photo(remote_path)
                        if cloud_bytes:
                            st.image(cloud_bytes, use_column_width=True)
                        else:
                            st.info("No disponible")
                    except Exception:
                        st.error("Error")
            
            with c_desc:
                new_cap = st.text_input(f"Descripción", value=photo["caption"], key=f"edit_cap_{photo['id']}")
                new_date = st.date_input(f"Fecha", value=photo["date"], key=f"edit_date_{photo['id']}")
                # Actualizamos en el objeto temporal
                photo["caption"] = new_cap
                photo["date"] = new_date
            
            with c_actions:
                st.write("") # Spacer
                if i > 0:
                    if st.button("🔼", key=f"up_{photo['id']}", help="Mover arriba"):
                        # Intercambiar con el anterior
                        preview_photos[i], preview_photos[i-1] = preview_photos[i-1], preview_photos[i]
                        st.session_state.preview_photos = preview_photos
                        st.rerun()
                
                if i < len(preview_photos) - 1:
                    if st.button("🔽", key=f"down_{photo['id']}", help="Mover abajo"):
                        # Intercambiar con el siguiente
                        preview_photos[i], preview_photos[i+1] = preview_photos[i+1], preview_photos[i]
                        st.session_state.preview_photos = preview_photos
                        st.rerun()
                
                if st.button("🗑️", key=f"del_{photo['id']}", help="Eliminar foto"):
                    preview_photos.pop(i)
                    st.session_state.preview_photos = preview_photos
                    st.rerun()
            
            st.divider()

        st.markdown("---")

        # ═══════════════════════════════════════
        #  EQUIPOS DE MEDICIÓN (editable)
        # ═══════════════════════════════════════
        equip_names = data.get("equipment_name", [])
        if equip_names:
            st.markdown("### 🔧 Equipos de Medición")
            st.caption("Haga clic en cualquier celda para editarla. Use los botones + o - para agregar o quitar equipos.")

            equipos_preview = []
            for i in range(len(equip_names)):
                equipos_preview.append({
                    "Item": data.get('equipment_item', [])[i] if i < len(data.get('equipment_item', [])) else i+1,
                    "Equipo": equip_names[i],
                    "Marca": data.get('equipment_brand', [])[i] if i < len(data.get('equipment_brand', [])) else '',
                    "Modelo": data.get('equipment_model', [])[i] if i < len(data.get('equipment_model', [])) else '',
                    "Serie": data.get('equipment_serial', [])[i] if i < len(data.get('equipment_serial', [])) else '',
                    "Fecha Calibración": data.get('equipment_cal_date', [])[i] if i < len(data.get('equipment_cal_date', [])) else '',
                })

            edited_equipos = st.data_editor(
                equipos_preview,
                num_rows="dynamic",
                use_container_width=True,
                key="prev_equipos_editor"
            )

            st.markdown("---")

        # ═══════════════════════════════════════
        #  OBSERVACIONES Y CONCLUSIONES (editables)
        # ═══════════════════════════════════════
        st.markdown("### 📝 Observaciones")
        edited_observations = st.text_area("Edite las observaciones", value=data.get("observations", ""), height=80, key="prev_obs")

        st.markdown("### ✅ Conclusiones")
        edited_conclusions = st.text_area("Edite las conclusiones", value=data.get("conclusions", ""), height=80, key="prev_conc")

        st.markdown("---")

        # ═══════════════════════════════════════
        #  SUPERVISOR
        # ═══════════════════════════════════════
        st.markdown("### 👤 Supervisor")
        edited_supervisor = st.text_input("Supervisor TGP", value=data.get("supervisor", ""), key="prev_supervisor")

        st.caption("_Este reporte reemplaza al anterior formato de Actividades y Eventos COG001TITIFO0001_")

        # ── Botones finales ──
        st.markdown("---")
        col_b1, col_b2, col_b3 = st.columns([1, 1, 1])
        with col_b1:
            if st.button("⬅️ Volver al Formulario", use_container_width=True, key="btn_back_bottom"):
                st.session_state.app_step = "formulario"
                st.rerun()
        with col_b3:
            generate_clicked_bottom = st.button("🚀 Generar PDF Final", type="primary", use_container_width=True, key="btn_gen_bottom")

        # ── Generar PDF ──
        if generate_clicked or generate_clicked_bottom:
            # Aplicar ediciones de la vista previa
            data["activity"] = edited_activity
            data["activity_type"] = edited_tipo
            data["place"] = edited_lugar
            data["personnel"] = edited_personal
            data["client"] = edited_cliente
            data["status"] = edited_estado
            data["client_approval"] = edited_conformidad
            data["supervisor"] = edited_supervisor
            data["summary"] = edited_summary
            data["observations"] = edited_observations
            data["conclusions"] = edited_conclusions
            # Reconstruir todo desde la lista unificada de fotos de la sesión (posiblemente reordenada)
            ordered_captions = []
            ordered_dates = []
            ordered_cloud = []
            ordered_local_files_data = []

            class FakeUploadedFile:
                def __init__(self, name, b): self.name = name; self.b = b
                def read(self): return self.b
                def seek(self, p): pass

            for p in st.session_state.get("preview_photos", []):
                ordered_captions.append(p["caption"])
                ordered_dates.append(p["date"])
                if p["type"] == "local":
                    ordered_local_files_data.append(FakeUploadedFile(p["name"], p["bytes"]))
                else:
                    ordered_cloud.append(p["name"])

            data["photo_captions"] = ordered_captions
            data["photo_dates"] = ordered_dates
            data["cloud_photos"] = ordered_cloud

            # Aplicar ediciones de equipos si fueron editados
            if equip_names and edited_equipos:
                data["equipment_item"] = [e.get("Item", i+1) for i, e in enumerate(edited_equipos)]
                data["equipment_name"] = [e.get("Equipo", "") for e in edited_equipos]
                data["equipment_brand"] = [e.get("Marca", "") for e in edited_equipos]
                data["equipment_model"] = [e.get("Modelo", "") for e in edited_equipos]
                data["equipment_serial"] = [e.get("Serie", "") for e in edited_equipos]
                data["equipment_cal_date"] = [e.get("Fecha Calibración", "") for e in edited_equipos]

            with st.spinner("Generando PDF final y subiendo a la nube..."):
                import importlib
                import app.controllers.report_controller as ctrl_mod
                importlib.reload(ctrl_mod)
                # is_preview=False para que sí suba a la nube
                pdf_path = ctrl_mod.create_report_from_form_data(data, ordered_local_files_data, is_preview=False)

            st.session_state.pdf_path = pdf_path
            
            # Limpiar la sesión para que ya no aparezca como "En Progreso" en el Inicio
            st.session_state.form_photos = []
            st.session_state.equipos_list = []
            st.session_state.camera_queue = []
            st.session_state.pop("base_filename", None)
            st.session_state.pop("draft_version", None)
            st.session_state.pop("f_unique", None)
            
            st.session_state.app_step = "generado"
            st.rerun()


# ════════════════════════════════════════════════
#  PASO 3: PDF GENERADO
# ════════════════════════════════════════════════
def render_generado():
    """Muestra el resultado: descarga del PDF."""
    
    st.markdown("""
    <div class="stitch-success-icon-container">
        <div class="stitch-success-icon-bg"></div>
        <div class="stitch-success-icon">
            <span style="font-size:32px;">✅</span>
        </div>
    </div>
    <h2 class="stitch-success-title">Reporte generado correctamente</h2>
    <p class="stitch-success-text">El documento técnico ha sido procesado, validado y guardado en el sistema.</p>
    """, unsafe_allow_html=True)

    pdf_path = st.session_state.get("pdf_path", "")

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        file_size_kb = len(pdf_bytes) / 1024
        
        # Details card
        st.markdown(f"""
        <div class="stitch-data-card">
            <div class="stitch-data-card-header">
                <p class="stitch-data-card-title">Detalles del Registro</p>
            </div>
            <div class="stitch-data-row">
                <span class="stitch-data-label">Archivo PDF</span>
                <span class="stitch-data-value highlight">{os.path.basename(pdf_path)}</span>
            </div>
            <div class="stitch-data-row">
                <span class="stitch-data-label">Tamaño</span>
                <span class="stitch-data-value">{file_size_kb:.1f} KB</span>
            </div>
            <div class="stitch-data-row">
                <span class="stitch-data-label">Generado en</span>
                <span class="stitch-data-value">{datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="📥 Descargar PDF",
            data=pdf_bytes,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Crear Nuevo Reporte", use_container_width=True):
                st.session_state.app_step = "formulario"
                st.session_state.preview_data = {}
                st.session_state.preview_images = []
                st.rerun()
        with col2:
            if st.button("🏠 Volver al Menú Central", use_container_width=True):
                st.session_state.app_mode = "inicio"
                st.rerun()
    else:
        st.error("No se encontró el archivo PDF. Intente generar nuevamente.")
        if st.button("🔄 Volver al formulario"):
            st.session_state.app_step = "formulario"
            st.rerun()


# ════════════════════════════════════════════════
#  ROUTER PRINCIPAL
# ════════════════════════════════════════════════
load_custom_css()

# ── Router Principal ──
# LOGIN TEMPORALMENTE DESACTIVADO — siempre accede directo
if True:
    mode = st.session_state.app_mode
    if mode == "inicio":
        render_inicio()
    elif mode == "subida_rapida":
        render_subida_rapida()
    elif mode == "reporte":
        step = st.session_state.app_step
        if step == "formulario":
            render_formulario()
        elif step == "vista_previa":
            render_vista_previa()
        elif step == "generado":
            render_generado()
        else:
            st.session_state.app_step = "formulario"
            st.rerun()
    else:
        st.session_state.app_mode = "inicio"
        st.rerun()
