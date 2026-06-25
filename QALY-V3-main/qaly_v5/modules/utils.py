import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
import streamlit as st

# ── Supabase client (cached) ──────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    from supabase import create_client
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# ── Malaysia Time ─────────────────────────────────────────────────────────────
MYT = timezone(timedelta(hours=8))

def now_myt():
    return datetime.now(MYT)
    
def send_telegram(message: str):
    try:
        token   = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        url     = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            "chat_id":    chat_id,
            "text":       message,
            "parse_mode": "HTML",
        }, timeout=5)
    except Exception:
        pass

def send_whatsapp(message: str):
    """Send WhatsApp notification to all team members via CallMeBot API."""
    try:
        members = st.secrets["whatsapp"]["members"]
        # members is a list of dicts: [{phone: "...", apikey: "..."}]
        for m in members:
            phone  = m["phone"]
            apikey = m["apikey"]
            requests.get(
                "https://api.callmebot.com/whatsapp.php",
                params={
                    "phone":   phone,
                    "text":    message,
                    "apikey":  apikey,
                },
                timeout=5,
            )
    except Exception:
        pass

def send_email(subject: str, message: str):
    """Send an email notification via Gmail SMTP (App Password)."""
    try:
        sender    = st.secrets["email"]["sender"]
        password  = st.secrets["email"]["app_password"]
        recipient = st.secrets["email"]["recipient"]
        to_list   = recipient if isinstance(recipient, list) else [r.strip() for r in str(recipient).split(",")]

        msg          = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = ", ".join(to_list)
        msg.attach(MIMEText(message, "plain"))
        msg.attach(MIMEText(message.replace("\n", "<br>"), "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(sender, password)
            server.sendmail(sender, to_list, msg.as_string())
    except Exception:
        pass

def notify(message: str, subject: str = "Kimya Centre — New Update"):
    """Send notification to Telegram, WhatsApp, and Email."""
    send_telegram(message)
    send_whatsapp(message)
    send_email(subject, message)

# ── Core load / save (list-based, e.g. sales.json → key "sales") ─────────────
def _key(filename):
    """Strip .json extension to get Supabase key."""
    return filename.replace(".json", "")

def load(filename):
    """Load a list from Supabase. Returns [] if not found."""
    try:
        sb  = get_supabase()
        key = _key(filename)
        res = sb.table("store").select("value").eq("key", key).execute()
        if res.data:
            val = res.data[0]["value"]
            # val might be a list or a JSON string depending on Supabase driver version
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                return json.loads(val)
            return val if isinstance(val, list) else []
        return []
    except Exception as e:
        st.warning(f"load({filename}) failed: {e}")
        return []

def save(filename, data):
    """Upsert a list into Supabase."""
    try:
        sb  = get_supabase()
        key = _key(filename)
        sb.table("store").upsert({
            "key":        key,
            "value":      data,
            "updated_at": now_myt().isoformat(),
        }).execute()
    except Exception as e:
        st.error(f"save({filename}) failed: {e}")

def load_dict(filename):
    """Load a dict from Supabase. Returns {} if not found."""
    try:
        sb  = get_supabase()
        key = _key(filename)
        res = sb.table("store").select("value").eq("key", key).execute()
        if res.data:
            val = res.data[0]["value"]
            if isinstance(val, dict):
                return val
            if isinstance(val, str):
                return json.loads(val)
            return {}
        return {}
    except Exception as e:
        st.warning(f"load_dict({filename}) failed: {e}")
        return {}

def save_dict(filename, data):
    """Upsert a dict into Supabase."""
    try:
        sb  = get_supabase()
        key = _key(filename)
        sb.table("store").upsert({
            "key":        key,
            "value":      data,
            "updated_at": now_myt().isoformat(),
        }).execute()
    except Exception as e:
        st.error(f"save_dict({filename}) failed: {e}")

# ── Visit logging ─────────────────────────────────────────────────────────────
def log_visit(user):
    visits = load("visits.json")
    _now   = now_myt()
    visits.append({
        "user":      user,
        "timestamp": _now.isoformat(),
        "date":      _now.strftime("%Y-%m-%d"),
    })
    save("visits.json", visits)

# ── ensure_defaults: seed Supabase if tables are empty ───────────────────────
def ensure_defaults():
    if not load("inventory.json"):
        save("inventory.json", DEFAULT_INVENTORY)
    if not load("costing.json"):
        save("costing.json", DEFAULT_COSTING)
    if not load_dict("passcodes.json"):
        save_dict("passcodes.json", {"Dr. Shirwan": "0000", "Eqmal": "1234", "Syafa": "5555", "Nureen": "5678"})

# ── Theme ─────────────────────────────────────────────────────────────────────
def get_theme_colors():
    DM = st.session_state.get("dark_mode", True)
    if DM:
        return {
            "BG":        "#0d0d14",
            "SURFACE":   "#13131f",
            "SURFACE2":  "#1a1a2e",
            "BORDER":    "#2a2a3e",
            "TEXT":      "#e8e6f5",
            "TEXT2":     "#8b88a8",
            "TEXT3":     "#55527a",
            "ACCENT":    "#7c6fea",
            "ACCENT2":   "#a99eff",
            "CARD_BG":   "#16162a",
            "SUCCESS":   "#1a3a2a",
            "SUCCESS_T": "#4ade80",
            "WARN_BG":   "#2a2010",
            "WARN_T":    "#fbbf24",
            "ERR_BG":    "#3a1010",
            "ERR_T":     "#f87171",
        }
    else:
        return {
            "BG":        "#f5f5fb",
            "SURFACE":   "#ffffff",
            "SURFACE2":  "#f0eeff",
            "BORDER":    "#e2e0f0",
            "TEXT":      "#1a1440",
            "TEXT2":     "#6b68a0",
            "TEXT3":     "#a09bcc",
            "ACCENT":    "#534AB7",
            "ACCENT2":   "#7c6fea",
            "CARD_BG":   "#ffffff",
            "SUCCESS":   "#e8faf2",
            "SUCCESS_T": "#0d7a4e",
            "WARN_BG":   "#fffbeb",
            "WARN_T":    "#92400e",
            "ERR_BG":    "#fef2f2",
            "ERR_T":     "#b91c1c",
        }

# ── Constants ─────────────────────────────────────────────────────────────────
PASSCODES = {
    "Dr. Shirwan": "0000",
    "Eqmal":       "1234",
    "Syafa":       "5555",
    "Nureen":      "5678",
}

PRODUCTS = {
    "Qaly 100ml":               30.00,
    "Syed 100ml":               35.00,
    "Syeda 100ml":              35.00,
    "Kimya 100ml":              35.00,
    "Couple Set (Syed+Syeda)":  65.00,
}

CHANNELS = ["Campus Pickup (IIUM)", "Shopee", "Instagram DM", "WhatsApp", "Walk-in", "Other"]
MEMBERS  = ["Dr. Shirwan", "Eqmal", "Syafa", "Nureen"]
STATUSES = ["Pending", "Completed", "Cancelled"]

GFORM_SHEET_ID = "14EvKoF1dFyQeu5ishr6UBgsWniordtn6Ka3SYWl6k_8"
GFORM_GID      = "743510311"

USER_COLORS = {
    "Dr. Shirwan": "#7c6fea",
    "Eqmal":       "#4ade80",
    "Syafa":       "#f472b6",
    "Nureen":      "#60a5fa",
}

# ── Default data ──────────────────────────────────────────────────────────────
DEFAULT_INVENTORY = [
    {"id":"MAT001","name":"Magnesium Chloride","supplier":"","unit":"g",  "stock":1000,"reorder":200,"unit_cost":0.020,"last_bought":"","notes":"Antibacterial active ingredient"},
    {"id":"MAT002","name":"Aloe Vera Extract", "supplier":"","unit":"ml", "stock":500, "reorder":100,"unit_cost":0.050,"last_bought":"","notes":"Skin soothing carrier"},
    {"id":"MAT003","name":"Dipropylene Glycol","supplier":"","unit":"ml", "stock":500, "reorder":100,"unit_cost":0.030,"last_bought":"","notes":"Solvent / carrier"},
    {"id":"MAT004","name":"Potassium Sorbate", "supplier":"","unit":"g",  "stock":200, "reorder":50, "unit_cost":0.080,"last_bought":"","notes":"Natural preservative"},
    {"id":"MAT005","name":"Distilled Water",   "supplier":"","unit":"ml", "stock":5000,"reorder":1000,"unit_cost":0.001,"last_bought":"","notes":"Aqueous base"},
    {"id":"MAT006","name":"Bottle 100ml",      "supplier":"","unit":"pcs","stock":200, "reorder":50, "unit_cost":1.200,"last_bought":"","notes":"Primary packaging"},
    {"id":"MAT007","name":"Label / Sticker",   "supplier":"","unit":"pcs","stock":200, "reorder":50, "unit_cost":0.300,"last_bought":"","notes":"Product label"},
    {"id":"MAT008","name":"Fragrance Oil",     "supplier":"","unit":"ml", "stock":300, "reorder":80, "unit_cost":0.120,"last_bought":"","notes":"For Syed, Syeda, Kimya"},
    {"id":"MAT009","name":"Box / Outer Pack",  "supplier":"","unit":"pcs","stock":100, "reorder":30, "unit_cost":0.500,"last_bought":"","notes":"Optional outer packaging"},
]

DEFAULT_COSTING = [
    {"product":"Qaly 100ml","overhead":2.00,"selling_price":30.00,"ingredients":[
        {"name":"Magnesium Chloride","qty":5.0,  "unit":"g",  "cost_per_unit":0.020,"line_cost":0.1000},
        {"name":"Aloe Vera Extract", "qty":20.0, "unit":"ml", "cost_per_unit":0.050,"line_cost":1.0000},
        {"name":"Dipropylene Glycol","qty":10.0, "unit":"ml", "cost_per_unit":0.030,"line_cost":0.3000},
        {"name":"Potassium Sorbate", "qty":0.5,  "unit":"g",  "cost_per_unit":0.080,"line_cost":0.0400},
        {"name":"Distilled Water",   "qty":64.5, "unit":"ml", "cost_per_unit":0.001,"line_cost":0.0645},
        {"name":"Bottle 100ml",      "qty":1,    "unit":"pcs","cost_per_unit":1.200,"line_cost":1.2000},
        {"name":"Label / Sticker",   "qty":1,    "unit":"pcs","cost_per_unit":0.300,"line_cost":0.3000},
    ]},
    {"product":"Syed 100ml","overhead":2.00,"selling_price":35.00,"ingredients":[
        {"name":"Magnesium Chloride","qty":5.0,  "unit":"g",  "cost_per_unit":0.020,"line_cost":0.1000},
        {"name":"Aloe Vera Extract", "qty":20.0, "unit":"ml", "cost_per_unit":0.050,"line_cost":1.0000},
        {"name":"Dipropylene Glycol","qty":10.0, "unit":"ml", "cost_per_unit":0.030,"line_cost":0.3000},
        {"name":"Potassium Sorbate", "qty":0.5,  "unit":"g",  "cost_per_unit":0.080,"line_cost":0.0400},
        {"name":"Fragrance Oil",     "qty":3.0,  "unit":"ml", "cost_per_unit":0.120,"line_cost":0.3600},
        {"name":"Distilled Water",   "qty":61.5, "unit":"ml", "cost_per_unit":0.001,"line_cost":0.0615},
        {"name":"Bottle 100ml",      "qty":1,    "unit":"pcs","cost_per_unit":1.200,"line_cost":1.2000},
        {"name":"Label / Sticker",   "qty":1,    "unit":"pcs","cost_per_unit":0.300,"line_cost":0.3000},
    ]},
    {"product":"Syeda 100ml","overhead":2.00,"selling_price":35.00,"ingredients":[
        {"name":"Magnesium Chloride","qty":5.0,  "unit":"g",  "cost_per_unit":0.020,"line_cost":0.1000},
        {"name":"Aloe Vera Extract", "qty":20.0, "unit":"ml", "cost_per_unit":0.050,"line_cost":1.0000},
        {"name":"Dipropylene Glycol","qty":10.0, "unit":"ml", "cost_per_unit":0.030,"line_cost":0.3000},
        {"name":"Potassium Sorbate", "qty":0.5,  "unit":"g",  "cost_per_unit":0.080,"line_cost":0.0400},
        {"name":"Fragrance Oil",     "qty":3.0,  "unit":"ml", "cost_per_unit":0.120,"line_cost":0.3600},
        {"name":"Distilled Water",   "qty":61.5, "unit":"ml", "cost_per_unit":0.001,"line_cost":0.0615},
        {"name":"Bottle 100ml",      "qty":1,    "unit":"pcs","cost_per_unit":1.200,"line_cost":1.2000},
        {"name":"Label / Sticker",   "qty":1,    "unit":"pcs","cost_per_unit":0.300,"line_cost":0.3000},
    ]},
    {"product":"Kimya 100ml","overhead":2.00,"selling_price":35.00,"ingredients":[
        {"name":"Magnesium Chloride","qty":5.0,  "unit":"g",  "cost_per_unit":0.020,"line_cost":0.1000},
        {"name":"Aloe Vera Extract", "qty":20.0, "unit":"ml", "cost_per_unit":0.050,"line_cost":1.0000},
        {"name":"Dipropylene Glycol","qty":10.0, "unit":"ml", "cost_per_unit":0.030,"line_cost":0.3000},
        {"name":"Potassium Sorbate", "qty":0.5,  "unit":"g",  "cost_per_unit":0.080,"line_cost":0.0400},
        {"name":"Fragrance Oil",     "qty":3.0,  "unit":"ml", "cost_per_unit":0.120,"line_cost":0.3600},
        {"name":"Distilled Water",   "qty":61.5, "unit":"ml", "cost_per_unit":0.001,"line_cost":0.0615},
        {"name":"Bottle 100ml",      "qty":1,    "unit":"pcs","cost_per_unit":1.200,"line_cost":1.2000},
        {"name":"Label / Sticker",   "qty":1,    "unit":"pcs","cost_per_unit":0.300,"line_cost":0.3000},
    ]},
    {"product":"Couple Set (Syed+Syeda)","overhead":3.00,"selling_price":65.00,"ingredients":[
        {"name":"Magnesium Chloride","qty":10.0, "unit":"g",  "cost_per_unit":0.020,"line_cost":0.2000},
        {"name":"Aloe Vera Extract", "qty":40.0, "unit":"ml", "cost_per_unit":0.050,"line_cost":2.0000},
        {"name":"Dipropylene Glycol","qty":20.0, "unit":"ml", "cost_per_unit":0.030,"line_cost":0.6000},
        {"name":"Potassium Sorbate", "qty":1.0,  "unit":"g",  "cost_per_unit":0.080,"line_cost":0.0800},
        {"name":"Fragrance Oil",     "qty":6.0,  "unit":"ml", "cost_per_unit":0.120,"line_cost":0.7200},
        {"name":"Distilled Water",   "qty":123.0,"unit":"ml", "cost_per_unit":0.001,"line_cost":0.1230},
        {"name":"Bottle 100ml",      "qty":2,    "unit":"pcs","cost_per_unit":1.200,"line_cost":2.4000},
        {"name":"Label / Sticker",   "qty":2,    "unit":"pcs","cost_per_unit":0.300,"line_cost":0.6000},
        {"name":"Box / Outer Pack",  "qty":1,    "unit":"pcs","cost_per_unit":0.500,"line_cost":0.5000},
    ]},
]
