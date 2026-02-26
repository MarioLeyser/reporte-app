
import os
import requests
import config
from requests.auth import HTTPBasicAuth
import urllib.parse

def diagnose():
    base_url = config.CLOUD_URL
    user = config.CLOUD_USER
    password = config.CLOUD_PASS
    auth = HTTPBasicAuth(user, password)
    verify = False # Deshabilitar verificación SSL por defecto
    
    # Normalizar dav_url para evitar dobles slashes
    dav_url = f"{base_url}/remote.php/dav/files/{user}"
    if dav_url.endswith("/"):
        dav_url = dav_url[:-1]
        
    print(f"DAV URL: {dav_url}")
    
    remote_path = config.CLOUD_DRAFTS_PATH
    if not remote_path.startswith("/"):
        remote_path = "/" + remote_path
        
    print(f"Target Drafts Path: {remote_path}")
    
    # 1. Probar MKCOL recursivo
    parts = [p for p in remote_path.split("/") if p]
    current_path = ""
    for part in parts:
        current_path += "/" + part
        encoded_current = urllib.parse.quote(current_path, safe='/')
        url = dav_url + encoded_current
        print(f"Proband MKCOL en: {url} ...", end=" ")
        try:
            resp = requests.request("MKCOL", url, auth=auth, verify=verify, timeout=10)
            print(f"Status: {resp.status_code}")
        except Exception as e:
            print(f"Error: {e}")
            
    # 2. Probar subida de archivo
    test_file = "outputs/diagnose.json"
    if not os.path.exists("outputs"): os.makedirs("outputs")
    with open(test_file, "w") as f: f.write('{"status": "diagnostics"}')
    
    remote_file_path = f"{remote_path}/diagnose.json"
    encoded_file_path = urllib.parse.quote(remote_file_path, safe='/')
    url = dav_url + encoded_file_path
    
    print(f"Proband PUT en: {url} ...", end=" ")
    try:
        with open(test_file, "rb") as f:
            resp = requests.put(url, data=f, auth=auth, verify=verify, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code not in [201, 204]:
            print(f"Response Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

    # 3. Probar PROPFIND para listar
    print(f"Proband PROPFIND en: {dav_url}{urllib.parse.quote(remote_path, safe='/')} ...", end=" ")
    try:
        headers = {'Depth': '1'}
        url = dav_url + urllib.parse.quote(remote_path, safe='/')
        resp = requests.request("PROPFIND", url, auth=auth, verify=verify, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 207:
            print("Directorio encontrado y accesible.")
        else:
            print(f"Response Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    diagnose()
