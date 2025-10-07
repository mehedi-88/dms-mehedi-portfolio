# src/routes/contact.py
from flask import Blueprint, request, jsonify, current_app, send_from_directory
import os, time, re, smtplib, sqlite3
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+
from dotenv import load_dotenv

load_dotenv()

# ---------- Paths ----------
ROOT_DIR   = os.path.dirname(os.path.dirname(__file__))          # src/
STATIC_DIR = os.path.join(ROOT_DIR, "static")
DB_PATH    = os.path.join(ROOT_DIR, "dms_ai.db")

# ---------- Blueprint ----------
# সব API এর জন্য prefix `/api`
contact_bp = Blueprint("contact", __name__, url_prefix="/api")

# ---------- Helpers ----------
def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# ---- Rate-limit (in-memory) ----
rate_limit_storage = defaultdict(list)
MAX_REQUESTS = 3
TIME_WINDOW = 300  # 5 min

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    rate_limit_storage[ip] = [t for t in rate_limit_storage[ip] if now - t < TIME_WINDOW]
    if len(rate_limit_storage[ip]) >= MAX_REQUESTS:
        return True
    rate_limit_storage[ip].append(now)
    return False

# ---- Validators ----
def validate_email(email: str) -> bool:
    return re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", (email or "")) is not None

def validate_phone(phone: str) -> bool:
    if not (phone or "").strip():
        return True  # optional
    clean = re.sub(r"[\s\-\(\)]+", "", phone)
    return re.match(r"^\+?[1-9]\d{0,15}$", clean) is not None

# ---- Optional email sender (only if creds exist) ----
def try_send_email(name: str, email: str, phone: str, service: str, message: str) -> bool:
    smtp_server = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    smtp_port   = int(os.getenv("EMAIL_PORT", "587"))
    user        = os.getenv("EMAIL_HOST_USER")
    password    = os.getenv("EMAIL_HOST_PASSWORD")
    to_addr     = os.getenv("EMAIL_TO") or user

    # যদি .env ক্রেডেনশিয়াল না থাকে, ইমেইল স্কিপ — কিন্তু API OK থাকবে
    if not user or not password:
        current_app.logger.info("[MAIL] skipped (no credentials)")
        return False

    body = (
        "New contact form submission:\n\n"
        f"Name   : {name}\n"
        f"Email  : {email}\n"
        f"Phone  : {phone or 'Not provided'}\n"
        f"Service: {service}\n\n"
        f"Message:\n{message}\n\n"
        "---\nSent from DMS MEHEDI Website"
    )

    msg = MIMEMultipart()
    msg["From"] = formataddr(("DMS MEHEDI Site", user))
    msg["To"] = to_addr
    msg["Subject"] = f"New Contact Form Submission from {name}"
    if email:
        msg["Reply-To"] = email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    current_app.logger.info(f"[MAIL] sending via {smtp_server}:{smtp_port} as {user} → {to_addr}")
    with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
    current_app.logger.info("[MAIL] sent OK")
    return True

# ---------- Routes ----------

# (Optional) স্ট্যাটিক কন্টাক্ট পেজ সার্ভ করতে চাইলে:
@contact_bp.route("/contact-page", methods=["GET"])
def serve_contact_page():
    # /api/contact-page -> static/contact.html
    return send_from_directory(STATIC_DIR, "contact.html")

@contact_bp.route("/contact/test", methods=["GET"])
def test_contact():
    return jsonify({
        "message": "Contact API is working",
        "endpoints": {
            "POST /api/contact": "Submit contact form",
            "GET /api/contact/status": "Agent online window",
            "GET /api/contact/test": "This test endpoint"
        }
    }), 200

@contact_bp.route("/contact/status", methods=["GET"])
def contact_status():
    """Online window (Bangladesh time): 10:00 → 02:59"""
    try:
        tz = ZoneInfo("Asia/Dhaka")
        hour = datetime.now(tz).hour
        tz_name = "Asia/Dhaka"
    except Exception:
        hour = datetime.now().hour
        tz_name = "SERVER_LOCAL"
    online = (hour >= 10) or (hour <= 2)
    return jsonify({"online": online, "hour": hour, "tz": tz_name}), 200

@contact_bp.route("/contact", methods=["POST"])
def handle_contact():
    try:
        # rate limit
        ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        if is_rate_limited(ip):
            return jsonify({"success": False, "error": "Too many requests. Try again later."}), 429

        data = request.get_json(silent=True) or request.form.to_dict()

        # honeypot
        if (data.get("honeypot") or "").strip():
            return jsonify({"success": False, "error": "Spam detected"}), 400

        # fields (বহু নাম সাপোর্ট)
        name    = (data.get("name") or data.get("fullname") or data.get("fullName") or "").strip()
        email   = (data.get("email") or "").strip()
        phone   = (data.get("phone") or data.get("mobile") or data.get("tel") or "").strip()
        service = (data.get("service") or data.get("serviceInterest") or data.get("subject") or "").strip()
        message = (data.get("message") or data.get("msg") or data.get("content") or "").strip()

        # validate
        errors = {}
        if not name or len(name) < 2:
            errors["name"] = "Name is required and must be at least 2 characters"
        if not email:
            errors["email"] = "Email is required"
        elif not validate_email(email):
            errors["email"] = "Please enter a valid email address"
        if phone and not validate_phone(phone):
            errors["phone"] = "Please enter a valid phone number"
        if not service:
            errors["service"] = "Please select a service"
        if not message or len(message) < 10:
            errors["message"] = "Message is required and must be at least 10 characters"

        if errors:
            return jsonify({"success": False, "errors": errors}), 400

        # save to DB (যেমন আগেরটা করতো)
        con = db(); cur = con.cursor()
        cur.execute("""
            INSERT INTO contact_submissions(name,email,phone,topic,message,ts)
            VALUES(?,?,?,?,?,?)
        """, (name, email, phone, service, message, time.time()))
        con.commit(); con.close()

        # optional email
        emailed = False
        try:
            emailed = try_send_email(name, email, phone, service, message)
        except Exception:
            current_app.logger.exception("[MAIL] failed")

        return jsonify({
            "success": True,
            "emailed": bool(emailed),
            "message": "Thanks! We’ve received your message — DMS MEHEDI"
        }), 200

    except Exception:
        current_app.logger.exception("[CONTACT] error")
        return jsonify({
            "success": False,
            "error": "Failed to send message. Please try again or contact us directly."
        }), 500