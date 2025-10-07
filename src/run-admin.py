# ================== src/run_admin.py ==================
import os, sys, webbrowser
from threading import Timer

# Ensure src folder in path
CUR = os.path.dirname(__file__)
if CUR not in sys.path:
    sys.path.insert(0, CUR)

from main import app  # ✅ no socketio now (Ably version)

if __name__ == "__main__":
    url = "http://127.0.0.1:5000/admin"

    # delay opening browser slightly to allow server start
    def open_browser():
        try:
            webbrowser.open(url)
        except Exception:
            pass

    Timer(1.0, open_browser).start()

    # run flask normally
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)