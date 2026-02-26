from app.models.report_data import Report, Equipment, PhotoEntry
from app.services.report_renderer import render_report_tex
from app.services.pdf_generator_latex import generate_pdf_latex
from app.services.image_processor import resize_image, save_temp_image
from app.utils.file_helpers import generate_output_filename
from datetime import datetime, date
import os
import time
import config
import streamlit as st
def create_report_from_form_data(form_data: dict, uploaded_images: list, is_preview: bool = False) -> str:
    """
    form_data: diccionario con todos los campos del formulario
    uploaded_images: lista de objetos UploadedFile (de Streamlit)
    is_preview: si es True, no sube nada a la nube y genera el PDF localmente
    """
    # Instanciar servicio de nube
    import importlib
    import app.services.nextcloud_service as ns_mod
    import config
    importlib.reload(ns_mod)
    importlib.reload(config)
    from app.services.nextcloud_service import NextcloudService
    cloud = NextcloudService()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Construir objeto Report
    report = Report()

    report.reviewed_by = "MIGUEL AUCAPOMA"
    report.review_date = datetime.now().strftime("%d/%m/%Y")
    report.approved_by = "JUAN LLANOS"
    report.approve_date = datetime.now().strftime("%d/%m/%Y")

    # Datos generales
    report.place = form_data.get("place", "")
    report.start_date = form_data.get("start_date")
    report.end_date = form_data.get("end_date")
    report.personnel = form_data.get("personnel", "").split(",")
    report.personnel = [p.strip() for p in report.personnel if p.strip()]
    report.client = form_data.get("client", "")
    report.status = form_data.get("status", "")
    report.client_approval = form_data.get("client_approval", "")
    report.summary = form_data.get("summary", "")
    report.supervisor = form_data.get("supervisor", "")

    # Calculo de estado de progreso
    report.total_days = form_data.get("total_days", 1)
    report.current_day = form_data.get("current_day", 1)
    report.actual_progress = form_data.get("actual_progress", 0.0)
    
    # 100% / total_days * current_day
    if report.total_days > 0:
        report.expected_progress = (100.0 / report.total_days) * report.current_day
    else:
        report.expected_progress = 0.0
        
    threshold_yellow = report.expected_progress * 0.85
    
    if report.actual_progress >= report.expected_progress:
        report.progress_status_color = "green"
    elif report.actual_progress >= threshold_yellow:
        report.progress_status_color = "yellow"
    else:
        report.progress_status_color = "red"

    # Equipos de medición
    equipment_items = form_data.get("equipment_item", [])
    equipment_names = form_data.get("equipment_name", [])
    equipment_brands = form_data.get("equipment_brand", [])
    equipment_models = form_data.get("equipment_model", [])
    equipment_serials = form_data.get("equipment_serial", [])
    equipment_cal_dates = form_data.get("equipment_cal_date", [])

    for i in range(len(equipment_items)):
        if i < len(equipment_names) and equipment_names[i]:
            report.equipment_list.append(Equipment(
                item=int(equipment_items[i]) if (i < len(equipment_items) and equipment_items[i]) else i+1,
                name=equipment_names[i],
                brand=equipment_brands[i] if i < len(equipment_brands) else "",
                model=equipment_models[i] if i < len(equipment_models) else "",
                serial=equipment_serials[i] if i < len(equipment_serials) else "",
                calibration_date=equipment_cal_dates[i] if i < len(equipment_cal_dates) else ""
            ))

    # Conclusiones/Observaciones
    report.conclusions = [c.strip() for c in form_data.get("conclusions", "").split("\n") if c.strip()]
    report.observations = [o.strip() for o in form_data.get("observations", "").split("\n") if o.strip()]

    # ─── PROCESO DE GENERACIÓN ───
    msg_cloud = " (Omitiendo subida por Vista Previa)" if is_preview else ""
    with st.spinner(f"🚀 Generando reporte{msg_cloud}..."):
        # 1. Procesar imágenes
        captions = form_data.get("photo_captions", [])
        action_dates = form_data.get("photo_dates", [])
        cloud_photos = form_data.get("cloud_photos", [])

        all_entries = []
        
        # Procesar fotos locales
        for i, img in enumerate(uploaded_images):
            try:
                img_bytes = img.read()
                if not img_bytes: continue
                
                resized_bytes = resize_image(img_bytes)
                temp_path = os.path.abspath(save_temp_image(resized_bytes))
                
                if not is_preview:
                    clean_name = "".join(c for c in img.name if c.isalnum() or c in "._-").replace(" ", "_")
                    remote_photo_name = f"{timestamp}_{i}_{clean_name}"
                    if not remote_photo_name.lower().endswith(".jpg"): remote_photo_name += ".jpg"
                    remote_photo_path = f"{config.CLOUD_PHOTOS_PATH}/{remote_photo_name}"
                    
                    cloud.upload_file(temp_path, remote_photo_path)
                
                all_entries.append({
                    "path": temp_path,
                    "caption": captions[i] if i < len(captions) else "Evidencia",
                    "date": action_dates[i] if i < len(action_dates) else datetime.now().date()
                })
            except Exception as e:
                st.error(f"⚠️ Error en foto local {i+1}: {e}")

        # Procesar fotos de la nube (descargar para incluir en PDF)
        offset = len(uploaded_images)
        for i, cloud_name in enumerate(cloud_photos):
            try:
                remote_path = f"{config.CLOUD_PHOTOS_PATH}/{cloud_name}"
                temp_local_path = os.path.abspath(os.path.join("outputs", f"cloud_{timestamp}_{i}_{cloud_name}"))
                
                # Usar caché si es posible o descargar
                success = cloud.download_file(remote_path, temp_local_path)
                if success:
                    all_entries.append({
                        "path": temp_local_path,
                        "caption": captions[offset + i] if (offset + i) < len(captions) else "Evidencia (Nube)",
                        "date": action_dates[offset + i] if (offset + i) < len(action_dates) else datetime.now().date()
                    })
                else:
                    st.error(f"❌ Error al obtener `{cloud_name}`")
            except Exception as e:
                st.error(f"⚠️ Error con foto de nube {cloud_name}: {e}")

        # Registrar en Report
        for entry in all_entries:
            report.photos.append(PhotoEntry(
                image_path=entry["path"],
                caption=entry["caption"],
                action_date=entry["date"]
            ))

        # ─── 2. SISTEMA DE VERSIONES Y DRAFT (JSON) ───
        base_filename_session = form_data.get("base_filename")
        draft_version = form_data.get("draft_version", 0)

        old_version_files = []
        if base_filename_session:
            filename_base = base_filename_session
            version = draft_version + 1
            if draft_version > 0:
                old_version_files.append(f"ICRT_{filename_base}_v{draft_version}.pdf")
        else:
            codigo_limpio = form_data.get("codigo", "reporte").strip().replace(" ", "_").replace("/", "-")
            activity_safe = "".join(c for c in report.activity if c.isalnum() or c in "._-").replace(" ", "_")[:50]
            short_id = datetime.now().strftime("%d%H%M") # Añadir timestamp para ser un nuevo reporte unico
            filename_base = f"{codigo_limpio}_{activity_safe}_{short_id}"
            version = 1
            
        report.version = str(version)

        # 3. Renderizar LaTeX
        tex_content = render_report_tex(report)

        # 4. Generar PDF
        final_filename = f"ICRT_{filename_base}_v{version}"
        if is_preview: final_filename = f"PREVIEW_{final_filename}"
        
        pdf_path = generate_pdf_latex(tex_content, final_filename)

        # 5. GUARDAR BORRADOR (JSON) Y SUBIR PDF
        if not is_preview:
            import json
            import base64
            
            # Preparar datos para el JSON (borrador editable)
            # Necesitamos guardar los bytes de las fotos locales en base64 para que sean editables después
            
            draft_data = {
                "form_data": form_data, # Contiene textos, equipos, etc.
                "local_photos": [], # Guardaremos [nombre, bytes_b64, caption, date]
                "version": version,
                "timestamp": timestamp
            }
            
            # Re-procesar las fotos locales para el JSON
            for i, img in enumerate(uploaded_images):
                img.seek(0)
                b64_data = base64.b64encode(img.read()).decode('utf-8')
                draft_data["local_photos"].append({
                    "name": img.name,
                    "bytes_b64": b64_data,
                    "caption": captions[i] if i < len(captions) else "",
                    "date": str(action_dates[i]) if i < len(action_dates) else str(datetime.now().date())
                })

            json_filename = f"{filename_base}.json"
            json_local_path = os.path.join("outputs", json_filename)
            
            def json_serial(obj):
                """JSON serializer for objects not serializable by default json code"""
                if isinstance(obj, (date, datetime)):
                    return obj.isoformat()
                raise TypeError ("Type %s not serializable" % type(obj))

            with open(json_local_path, "w", encoding="utf-8") as jf:
                json.dump(draft_data, jf, default=json_serial, indent=4)
            
            # Subir PDF
            remote_pdf_path = f"{config.CLOUD_REPORTS_PATH}/{os.path.basename(pdf_path)}"
            cloud.upload_file(pdf_path, remote_pdf_path)
            
            # Subir JSON (Borrador)
            remote_json_path = f"{config.CLOUD_DRAFTS_PATH}/{json_filename}"
            cloud.upload_file(json_local_path, remote_json_path)
            
            # 🗑️ Eliminar versiones anteriores del PDF en la nube
            if old_version_files and not is_preview:
                for old_file in old_version_files:
                    old_remote_path = f"{config.CLOUD_REPORTS_PATH}/{old_file}"
                    cloud.delete_file(old_remote_path)
            
            st.success(f"✅ Versión v{version} subida. Borrador actualizado.")

    # 6. Limpiar temporales
    for photo in report.photos:
        try:
            if os.path.exists(photo.image_path):
                os.remove(photo.image_path)
        except Exception as e:
            print(f"Error borrando temporal: {e}")
            
    return pdf_path
