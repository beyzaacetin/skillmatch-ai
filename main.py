import sys
import os

# Ensure 'backend' is in Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

# Import the actual app from backend.main
try:
    from backend.main import app
except Exception as e:
    import traceback
    tb = traceback.format_exc()
    print("=" * 80)
    print("CRITICAL ROOT MAIN IMPORT ERROR:")
    print(tb)
    print("=" * 80)
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    app = FastAPI(title="SkillMatch AI v4 - Fallback Diagnostic Server", version="4.0.0")
    @app.get("/{rest_of_path:path}")
    def fallback_route(rest_of_path: str):
        html_content = f"""
        <html>
            <head><title>Startup Error Traceback</title></head>
            <body style="font-family: monospace; padding: 20px; background: #fff5f5; color: #900; line-height: 1.5;">
                <h1 style="border-bottom: 2px solid #fcc; padding-bottom: 10px;">Critical root main.py Import Error Traceback</h1>
                <pre style="background: #fff; border: 1px solid #ecc; padding: 15px; overflow-x: auto; border-radius: 4px;">{tb}</pre>
                <p style="margin-top: 20px; color: #666; font-size: 12px;">SkillMatch AI v4 - Fallback Diagnostic Server</p>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=200)
