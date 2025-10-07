# ================== src/main.py ==================
# Flask + SSE (Server-Sent Events) realtime chat — no Socket.IO required
from datetime import datetime, timezone
import json, os, time, uuid, sqlite3, threading
from queue import Queue, Empty
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, render_template, session, Response
from flask_cors import CORS
from dotenv import load_dotenv
# ---- extra routes (তোমার প্রজেক্টে আছে) ----
from routes.contact import contact_bp
from routes.ai import ai_bp
# ---------- OpenAI (optional auto-reply when no agent online) ----------
from openai import OpenAI


load_dotenv()

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPL_DIR  = os.path.join(BASE_DIR, "templates")
DB_PATH    = os.path.join(BASE_DIR, "dms_ai.db")

ADMIN_USER = os.getenv("ADMIN_USER", "admin").strip()
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123").strip()
SECRET_KEY = os.getenv("SECRET_KEY") or "dev-key"
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# ---------- Flask ----------
app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPL_DIR)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    TEMPLATES_AUTO_RELOAD=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # production এ True দেবে যদি HTTPS থাকে
)
CORS(app)

now = lambda: time.time()

# ---------- DB ----------
def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_db():
    con = db(); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cid TEXT, role TEXT, content TEXT, ts REAL,
        mid TEXT,
        seen_by_agent INTEGER DEFAULT 0,
        seen_by_client INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS clients(
        cid TEXT PRIMARY KEY,
        created REAL,
        last_seen REAL,
        online INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS agent_status(
        id INTEGER PRIMARY KEY CHECK (id=1),
        online INTEGER DEFAULT 0,
        name TEXT,
        last_seen REAL
    )""")
    cur.execute("INSERT OR IGNORE INTO agent_status(id,online,name,last_seen) VALUES(1,0,'Admin',0)")
    # --- lightweight migration: add last_seen if missing
    try:
        cur.execute("SELECT last_seen FROM agent_status LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute("ALTER TABLE agent_status ADD COLUMN last_seen REAL")
        cur.execute("UPDATE agent_status SET last_seen = 0 WHERE id=1")
    cur.execute("""CREATE TABLE IF NOT EXISTS contact_submissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, phone TEXT, topic TEXT, message TEXT, ts REAL
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_cid_ts ON messages(cid,ts)")
    con.commit(); con.close()

ensure_db()

def add_msg(cid, role, content, mid=None):
    mid = mid or f"{'a' if role=='agent' else ('b' if role=='bot' else 'u')}_{uuid.uuid4().hex[:12]}"
    con = db(); cur = con.cursor()
    cur.execute("INSERT INTO messages(cid,role,content,ts,mid) VALUES(?,?,?,?,?)",
                (cid, role, content, now(), mid))
    con.commit(); con.close()
    return mid

def last_msgs(cid, limit=50):
    con = db(); cur = con.cursor()
    cur.execute("""SELECT role,content,ts,mid,seen_by_agent,seen_by_client
                   FROM messages WHERE cid=? ORDER BY id DESC LIMIT ?""", (cid, limit))
    rows = cur.fetchall(); con.close()
    out = []
    for role, content, ts, mid, sba, sbc in reversed(rows):
        out.append({
            "role": role, "content": content, "ts": ts, "mid": mid,
            "seen_by_agent": int(sba or 0), "seen_by_client": int(sbc or 0)
        })
    return out

def unseen_mids(cid, whose):
    # whose: 'user' -> unseen by agent   |  'agent' -> unseen by client
    sql = ("SELECT mid FROM messages WHERE cid=? AND role='user' AND COALESCE(seen_by_agent,0)=0"
           if whose == 'user'
           else "SELECT mid FROM messages WHERE cid=? AND role IN('agent','bot') AND COALESCE(seen_by_client,0)=0")
    con = db(); cur = con.cursor()
    cur.execute(sql, (cid,))
    out = [r[0] for r in cur.fetchall() if r[0]]
    con.close()
    return out

def mark_seen(mids, by):
    if not mids: return
    col = "seen_by_agent" if by == "agent" else "seen_by_client"
    con = db(); cur = con.cursor()
    q = ",".join(["?"] * len(mids))
    cur.execute(f"UPDATE messages SET {col}=1 WHERE mid IN ({q})", mids)
    con.commit(); con.close()

def touch_client(cid, online=True):
    t = now()
    con = db(); cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO clients(cid,created,last_seen,online) VALUES(?,?,?,?)",
                (cid, t, t, 1 if online else 0))
    cur.execute("UPDATE clients SET last_seen=?, online=? WHERE cid=?",
                (t, 1 if online else 0, cid))
    con.commit(); con.close()

def set_agent_status(on: bool, name="Admin"):
    """online ফ্ল্যাগ আপডেট + last_seen = এখন (toggle মুহূর্ত)"""
    t = now()
    con = db(); cur = con.cursor()
    cur.execute("UPDATE agent_status SET online=?, name=?, last_seen=? WHERE id=1", (1 if on else 0, name, t))
    con.commit(); con.close()

def get_agent_presence():
    con = db(); cur = con.cursor()
    cur.execute("SELECT online, last_seen FROM agent_status WHERE id=1")
    row = cur.fetchone(); con.close()
    if not row:
        return False, 0.0
    return bool(row[0]), float(row[1] or 0)

def agent_online():
    on, _ = get_agent_presence()
    return on

# ---------- Tiny in-process Pub/Sub for SSE ----------
class Hub:
    def __init__(self):
        self.lock = threading.Lock()
        self.channels = {}  # name -> set(Queue)

    def subscribe(self, name: str):
        q = Queue()
        with self.lock:
            self.channels.setdefault(name, set()).add(q)

        def stream():
            try:
                yield "retry: 10000\n\n"  # auto-retry 10s
                while True:
                    try:
                        item = q.get(timeout=15)  # keep-alive every ~15s
                        ev   = item.get("event", "message")
                        data = json.dumps(item.get("data", {}), ensure_ascii=False)
                        yield f"event: {ev}\n" f"data: {data}\n\n"
                    except Empty:
                        # heartbeat comment
                        yield ": ping\n\n"
            finally:
                with self.lock:
                    self.channels.get(name, set()).discard(q)
        return stream()

    def publish(self, name: str, event: str, data: dict):
        with self.lock:
            subs = list(self.channels.get(name, set()))
        msg = {"event": event, "data": data}
        for q in subs:
            try:
                q.put_nowait(msg)
            except:
                pass

hub = Hub()

def broadcast_users(event, data):
    con = db(); cur = con.cursor()
    cur.execute("SELECT cid FROM clients")
    cids = [r[0] for r in cur.fetchall()]
    con.close()
    for c in cids:
        hub.publish(f"user:{c}", event, data)

# ---------- Auth ----------
def login_required(fn):
    @wraps(fn)
    def wrap(*a, **k):
        if not session.get("admin_logged_in"):
            return render_template("dms-admin.html", logged_in=False)
        return fn(*a, **k)
    return wrap

@app.post("/admin/login")
def admin_login():
    data = request.get_json(silent=True) or {}
    if (data.get("username","").strip()==ADMIN_USER and
        data.get("password","").strip()==ADMIN_PASS):
        session["admin_logged_in"] = True
        session.permanent = True
        set_agent_status(True)
        on, last_seen = get_agent_presence()
        # broadcast online to admin tabs + all users
        hub.publish("admin","agent_status",{"online":on,"last_seen":last_seen,"ts":now()})
        broadcast_users("agent_status", {"online": on, "last_seen": last_seen, "ts": now()})
        return jsonify({"ok":True})
    return jsonify({"ok":False,"error":"invalid_credentials"}), 401

@app.post("/admin/logout")
@login_required
def admin_logout():
    set_agent_status(False)
    session.clear()
    on, last_seen = get_agent_presence()
    hub.publish("admin","agent_status",{"online":on,"last_seen":last_seen,"ts":now()})
    broadcast_users("agent_status", {"online": on, "last_seen": last_seen, "ts": now()})
    return jsonify({"ok":True})

# ---------- SSE streams ----------
@app.get("/sse/stream/<cid>")
def sse_user(cid):
    touch_client(cid, True)
    return Response(
        hub.subscribe(f"user:{cid}"),
        mimetype="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"}
    )

@app.get("/sse/admin")
@login_required
def sse_admin():
    return Response(
        hub.subscribe("admin"),
        mimetype="text/event-stream",
        headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"}
    )

# ---------- Status / Presence ----------
@app.get("/api/status")
def api_status():
    on, last_seen = get_agent_presence()
    return jsonify({"online": on, "last_seen": last_seen, "ts": now()})

@app.post("/api/agent/online")
@login_required
def api_agent_online():
    on = bool((request.get_json(silent=True) or {}).get("online"))
    set_agent_status(on)
    cur_on, last_seen = get_agent_presence()
    hub.publish("admin","agent_status",{"online":cur_on,"last_seen":last_seen,"ts":now()})
    broadcast_users("agent_status", {"online": cur_on, "last_seen": last_seen, "ts": now()})
    return jsonify({"ok":True,"online":cur_on, "last_seen": last_seen})

@app.post("/api/client/heartbeat")
def api_heartbeat():
    cid = (request.json or {}).get("cid","").strip()
    if not cid: return jsonify({"ok":False,"error":"missing_cid"}), 400
    touch_client(cid, True)
    return jsonify({"ok":True})

@app.get("/api/client/presence/<cid>")
def api_presence(cid):
    """Chatbot UI last-seen/online ব্যাজের জন্য—raw timestamp ফেরত দেয়"""
    con = db(); cur = con.cursor()
    cur.execute("SELECT last_seen, online FROM clients WHERE cid=?", (cid,))
    row = cur.fetchone(); con.close()
    last_seen = float(row[0]) if row else 0.0
    online    = bool(row[1]) if row else False
    return jsonify({
        "cid": cid,
        "online": online,
        "last_seen": last_seen,
        "last_seen_iso": datetime.fromtimestamp(last_seen, tz=timezone.utc).isoformat() if last_seen else None,
        "ts": now()
    })

# ---------- Typing / Seen ----------
@app.post("/api/typing")
def api_typing():
    """
    body: { cid, who:'client'|'agent'|'bot', state:true|false }
    effect:
      - who == 'agent' -> push to user stream (chatbot dots দেখাবে)
      - who == 'client' -> push to admin stream (dashboard dots দেখাবে)
    """
    data = request.get_json() or {}
    cid   = (data.get("cid") or "").strip()
    who   = (data.get("who") or "client").strip()
    state = bool(data.get("state"))
    if not cid:
        return jsonify({"ok":False,"error":"missing_cid"}), 400

    if who == "agent":
        # 🔔 admin typing → user chatbot
        hub.publish(f"user:{cid}", "typing", {"who":"agent", "state": state, "ts": now()})
    else:
        # 🔔 client typing → admin dashboard
        hub.publish("admin", "typing", {"cid": cid, "who": "user", "state": state, "ts": now()})
    return jsonify({"ok": True})

@app.post("/api/seen")
def api_seen():
    """
    body: { cid, mids?:[...], who:'agent'|'client' }
    - writes seen flags
    - emits SSE 'seen' to the opposite side
    """
    data = request.get_json() or {}
    cid  = (data.get("cid") or "").strip()
    mids = data.get("mids") or []
    who  = (data.get("who") or "agent").strip()
    if not cid:
        return jsonify({"ok":False,"error":"missing_cid"}), 400

    if not mids:
        mids = unseen_mids(cid, "user" if who == "agent" else "agent")

    mark_seen(mids, by=who)
    if who == "agent":
        hub.publish(f"user:{cid}", "seen", {"who":"agent", "mids": mids, "ts": now()})
    else:
        hub.publish("admin", "seen", {"cid": cid, "mids": mids, "ts": now()})
    return jsonify({"ok": True, "mids": mids})

# ---------- Messages ----------
@app.post("/api/client/message")
def api_client_message():
    """
    User -> Server
    - Save DB
    - Push to admin SSE
    - If admin offline: auto AI reply (push to user SSE + save DB)
    """
    data = request.get_json() or {}
    cid  = (data.get("cid") or "").strip()
    text = (data.get("text") or "").strip()
    temp = (data.get("tempId") or "").strip()
    if not cid or not text:
        return jsonify({"ok":False,"error":"missing_fields"}), 400

    touch_client(cid, True)
    mid = add_msg(cid, "user", text)

    # Admin dashboards realtime
    hub.publish("admin", "message", {
        "cid":cid,"role":"user","text":text,"mid":mid,"tempId":temp,"ts":now()
    })
    # Sidebar unread refresh
    hub.publish("admin", "clients_list_changed", {"cid":cid})

    # If no live agent -> AI auto reply
    if not agent_online() and OPENAI_KEY:
        reply = ask_openai_sync(text)
        bot_mid = add_msg(cid, "bot", reply)
        # Push to user's SSE stream
        hub.publish(f"user:{cid}", "message", {
            "role":"bot","text":reply,"mid":bot_mid,"ts":now()
        })
        # Also notify admin tabs (history sync)
        hub.publish("admin", "message", {
            "cid":cid,"role":"bot","text":reply,"mid":bot_mid,"ts":now()
        })

    return jsonify({"ok":True,"mid":mid})

@app.post("/api/agent/message")
@login_required
def api_agent_message():
    """
    Agent -> Server
    - Save DB
    - Push to user SSE
    - Mirror to other admin tabs
    """
    data = request.get_json() or {}
    cid  = (data.get("cid") or "").strip()
    text = (data.get("text") or "").strip()
    if not cid or not text:
        return jsonify({"ok":False,"error":"missing_fields"}), 400

    mid = add_msg(cid, "agent", text)

    # push to user
    hub.publish(f"user:{cid}", "message", {"role":"agent","text":text,"mid":mid,"ts":now()})
    # push to admin tabs
    hub.publish("admin", "message", {"cid":cid,"role":"agent","text":text,"mid":mid,"ts":now()})
    hub.publish("admin", "clients_list_changed", {"cid":cid})

    return jsonify({"ok":True,"mid":mid})

@app.get("/api/chat/history/<cid>")
def api_history(cid):
    return jsonify(last_msgs(cid))

@app.get("/api/clients")
def api_clients():
    con = db(); cur = con.cursor()
    cur.execute("SELECT cid,last_seen,online FROM clients ORDER BY last_seen DESC")
    rows = cur.fetchall()
    out=[]
    for cid,last_seen,online in rows:
        cur.execute("""SELECT COUNT(1) FROM messages
                       WHERE cid=? AND role='user' AND COALESCE(seen_by_agent,0)=0""",(cid,))
        unread = cur.fetchone()[0] or 0
        out.append({
            "cid":cid,
            "last_seen":float(last_seen or 0),
            "online":bool(online),
            "unread":int(unread)
        })
    con.close()
    return jsonify({"clients":out})

@app.delete("/api/clients/<cid>")
@login_required
def api_delete_client(cid):
    con = db(); cur = con.cursor()
    cur.execute("DELETE FROM messages WHERE cid=?", (cid,))
    cur.execute("DELETE FROM clients WHERE cid=?", (cid,))
    con.commit(); con.close()
    hub.publish("admin","clients_list_changed",{"cid":cid})
    hub.publish(f"user:{cid}","deleted",{"cid":cid})
    return jsonify({"ok":True})

# ---------- FAQ / AI ----------
from openai import OpenAI
import logging, traceback, os
from flask import request, jsonify, render_template

# Load the key safely
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "").strip()
client = None
if OPENAI_KEY:
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        logging.info("✅ OpenAI client initialized successfully")
    except Exception as e:
        logging.error(f"❌ OpenAI client init failed: {e}")
else:
    logging.warning("⚠️ OPENAI_API_KEY not found — AI in offline mode")

# -------------------- Prompt Setup --------------------
SYSTEM_PROMPT = (
    "You are the AI assistant for DMS MEHEDI. Answer in clear, concise English. "
    "Focus areas: Web Development (Next.js/React), SEO/SEM, Google Ads, Shopify Dropshipping, "
    "and Analytics. When asked pricing, give typical ranges and suggest contacting directly. "
    "Use bullet points when helpful; keep paragraphs short. Do not invent any private data."
)

# -------------------- Main Function --------------------
def ask_openai_sync(question: str) -> str:
    """Ask OpenAI model safely with error handling"""
    if not client:
        return "Thanks! An agent will reply shortly. (AI offline in dev mode.)"

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (question or '').strip()},
            ],
        )
        answer = (resp.choices[0].message.content or "").strip()
        return answer or "Thanks for your message. Please try again shortly."
    except Exception as e:
        logging.error(f"❌ OpenAI API error: {e}")
        logging.error(traceback.format_exc())
        return "Sorry—our AI is busy right now. Please try again in a moment."

# -------------------- Flask Routes --------------------
@app.get("/faq")
def faq_page():
    """Render FAQ page"""
    return render_template("faq.html")

@app.post("/api/ai")
def api_ai():
    """Handle frontend chatbot request"""
    try:
        q = (request.json or {}).get("question", "").strip()
        if not q:
            return jsonify({"ok": False, "error": "empty"}), 200

        ai_response = ask_openai_sync(q)
        return jsonify({"ok": True, "text": ai_response, "sources": []}), 200
    except Exception as e:
        logging.error(f"API error: {e}")
        return jsonify({"ok": False, "error": "server"}), 500

  # <-- খুব জরুরি
# ---------- Contact (Dynamic Form) ----------
@app.get("/contact")
def contact_page():
    return send_from_directory(STATIC_DIR, "contact.html")

app.register_blueprint(contact_bp)

# ---------- Pages ----------
@app.get("/admin")
def admin_page():
    return render_template("dms-admin.html",
        logged_in=bool(session.get("admin_logged_in")))

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    target = os.path.join(STATIC_DIR, path)
    if path and os.path.exists(target):
        return send_from_directory(STATIC_DIR, path)
    # default portfolio landing (static/index.html)
    return send_from_directory(STATIC_DIR, "index.html")
@app.get("/api/health")
def health():
    return {"ok": True, "ai_key_loaded": bool(OPENAI_KEY)}, 200
# ---------- Run ----------
if __name__ == "__main__":
    # Dev server supports streaming fine.
    # Production: gunicorn -k gevent -w 1 app:app  (বা gthread)
    app.run(host="127.0.0.1", port=5000, debug=True, threaded=True)