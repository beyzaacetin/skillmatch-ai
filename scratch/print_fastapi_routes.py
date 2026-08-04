import sys
sys.path.append('backend')
from main import app

print("=== REGISTERED FASTAPI ROUTES ===")
for route in app.routes:
    # Print the route path and methods
    methods = getattr(route, "methods", None)
    if methods:
        print(f"{list(methods)} {route.path}")
    else:
        print(f"[-] {route.path}")
