import requests
import os
import config
import urllib.parse
import urllib3
import importlib

# Deshabilitar advertencias de SSL no verificado
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NextcloudService:
    def __init__(self):
        importlib.reload(config)
        self.base_url = config.CLOUD_URL
        self.user = config.CLOUD_USER
        self.password = config.CLOUD_PASS
        # Nextcloud WebDAV endpoint
        self.dav_url = f"{self.base_url}/remote.php/dav/files/{self.user}"
        self.auth = (self.user, self.password)
        self.verify = False  # Deshabilitar verificación SSL

    def _request(self, method, url, **kwargs):
        """Método centralizado para hacer requests con auth y SSL desactivado.
        No usa Session para evitar el error FileNotFoundError con proxies."""
        kwargs.setdefault("auth", self.auth)
        kwargs.setdefault("verify", self.verify)
        kwargs.setdefault("timeout", 10)
        return requests.request(method, url, **kwargs)

    def _encoded_url(self, remote_path):
        """Codifica un path remoto y devuelve la URL WebDAV completa."""
        encoded = urllib.parse.quote(remote_path, safe='/')
        if not encoded.startswith("/"):
            encoded = "/" + encoded
        return self.dav_url + encoded

    def upload_file(self, local_path, remote_path):
        """Sube un archivo a Nextcloud vía WebDAV."""
        url = self._encoded_url(remote_path)
        self._ensure_dir_exists(os.path.dirname(remote_path))
        try:
            with open(local_path, "rb") as f:
                response = self._request("PUT", url, data=f)
            if response.status_code in [201, 204]:
                return True
            else:
                print(f"Error subiendo archivo {local_path}: {response.status_code} {response.text[:200]}")
                return False
        except Exception as e:
            print(f"Excepción en upload_file: {e}")
            return False

    def upload_bytes(self, data_bytes, remote_path):
        """Sube bytes directamente a Nextcloud."""
        url = self._encoded_url(remote_path)
        self._ensure_dir_exists(os.path.dirname(remote_path))
        try:
            response = self._request("PUT", url, data=data_bytes)
            if response.status_code in [201, 204]:
                return True
            else:
                print(f"Error subiendo bytes a {url}: {response.status_code} {response.text[:200]}")
                return False
        except Exception as e:
            print(f"Excepción en upload_bytes: {e}")
            return False

    def _ensure_dir_exists(self, path):
        """Crea directorios recursivamente vía MKCOL."""
        parts = [p for p in path.split("/") if p]
        current_path = ""
        for part in parts:
            current_path += "/" + part
            url = self._encoded_url(current_path)
            try:
                self._request("MKCOL", url, timeout=10)
            except Exception as e:
                print(f"Warning: Fallo al crear directorio {current_path}: {e}")

    def list_files(self, remote_path, extensions=None):
        """Lista archivos en una carpeta de Nextcloud usando PROPFIND.
        Retorna solo los nombres de archivos (no carpetas)."""
        url = self._encoded_url(remote_path)
        headers = {"Depth": "1"}
        try:
            response = self._request("PROPFIND", url, headers=headers)
            if response.status_code == 207:
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(response.content)
                    ns = {'d': 'DAV:'}
                    filenames = []
                    for resp in root.findall('d:response', ns):
                        href_node = resp.find('d:href', ns)
                        if href_node is None or href_node.text is None:
                            continue
                        full_path = urllib.parse.unquote(href_node.text)
                        filename = os.path.basename(full_path.rstrip('/'))
                        propstat = resp.find('d:propstat', ns)
                        if propstat is not None:
                            prop = propstat.find('d:prop', ns)
                            if prop is not None:
                                res_type = prop.find('d:resourcetype', ns)
                                is_collection = (
                                    res_type is not None and
                                    res_type.find('d:collection', ns) is not None
                                )
                                if not is_collection and filename:
                                    if extensions:
                                        if filename.lower().endswith(
                                            tuple(ext.lower() for ext in extensions)
                                        ):
                                            filenames.append(filename)
                                    else:
                                        filenames.append(filename)
                    return sorted(filenames, reverse=True)
                except Exception as e:
                    print(f"Error parseando XML de list_files: {e}")
                    return []
            elif response.status_code == 401:
                print("Error 401: credenciales incorrectas para Nextcloud")
                return []
            elif response.status_code == 404:
                print(f"Error 404: carpeta no encontrada en Nextcloud: {remote_path}")
                return []
            else:
                print(f"Error listando archivos ({remote_path}): HTTP {response.status_code}")
                return []
        except Exception as e:
            print(f"Excepción en list_files: {e}")
            return []

    def download_file(self, remote_path, local_path):
        """Descarga un archivo de Nextcloud a una ruta local."""
        url = self._encoded_url(remote_path)
        try:
            response = self._request("GET", url, timeout=60)
            if response.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(response.content)
                return True
            else:
                print(f"Error descargando {remote_path}: {response.status_code}")
                return False
        except Exception as e:
            print(f"Excepción en download_file: {e}")
            return False

    def download_bytes(self, remote_path):
        """Descarga un archivo de Nextcloud y retorna sus bytes."""
        url = self._encoded_url(remote_path)
        try:
            response = self._request("GET", url, timeout=30)
            if response.status_code == 200:
                return response.content
            else:
                print(f"Error descargando bytes de {remote_path}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Excepción en download_bytes: {e}")
            return None

    def delete_file(self, remote_path):
        """Elimina un archivo de Nextcloud vía WebDAV DELETE."""
        url = self._encoded_url(remote_path)
        try:
            response = self._request("DELETE", url)
            if response.status_code in [200, 204]:
                print(f"Archivo eliminado: {remote_path}")
                return True
            elif response.status_code == 404:
                print(f"Archivo no encontrado (ya eliminado): {remote_path}")
                return True
            else:
                print(f"Error eliminando {remote_path}: {response.status_code} {response.text[:200]}")
                return False
        except Exception as e:
            print(f"Excepción en delete_file: {e}")
            return False
