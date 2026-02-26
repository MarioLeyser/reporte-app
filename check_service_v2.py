import sys
import os
import inspect

# Add the project root to sys.path
sys.path.append(os.path.abspath("."))

try:
    from app.services.nextcloud_service import NextcloudService
    import app.services.nextcloud_service as ns_mod
    
    print(f"File path: {ns_mod.__file__}")
    print("Methods in class:")
    for name, member in inspect.getmembers(NextcloudService, predicate=inspect.isfunction):
        print(f" - {name}")
except Exception as e:
    print(f"Error: {e}")
