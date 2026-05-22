import streamlit as st
from datetime import datetime
st.set_page_config(page_title="Kimya Centre", layout="wide")
if "dark_mode"      not in st.session_state: st.session_state.dark_mode      = True
if "authenticated"  not in st.session_state: st.session_state.authenticated  = False
if "current_user"   not in st.session_state: st.session_state.current_user   = None
if "page"           not in st.session_state: st.session_state.page           = "Dashboard"
if "login_error"    not in st.session_state: st.session_state.login_error    = ""
if "show_change_pw" not in st.session_state: st.session_state.show_change_pw = False
from modules.utils import get_theme_colors, ensure_defaults, log_visit, load_dict, save_dict, MEMBERS
ensure_defaults()
DM = st.session_state.dark_mode
C  = get_theme_colors()
# Load passcodes (allow override from file)
def get_passcodes():
    saved = load_dict("passcodes.json")
    defaults = {"Dr. Shirwan":"0000","Eqmal":"1234","Syafa":"5555","Nureen":"5678"}
    if not saved:
        save_dict("passcodes.json", defaults)
        return defaults
    return saved
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;}}
.main{{background:{C['BG']};}}
.main .block-container{{padding:2rem 2.5rem 3rem;max-width:1280px;}}
#MainMenu,footer{{visibility:hidden;}}
[data-testid="stDecoration"]{{display:none;}}
[data-testid="stSidebar"]{{background:{C['SURFACE']};border-right:1px solid {C['BORDER']};min-width:230px!important;max-width:230px!important;}}
[data-testid="stSidebar"] *{{color:{C['TEXT']}!important;}}
[data-testid="stSidebar"] hr{{border-color:{C['BORDER']}!important;}}
.stButton>button{{background:{C['ACCENT']}!important;color:white!important;border:none!important;border-radius:8px!important;padding:.45rem 1.2rem!important;font-weight:500!important;font-size:13px!important;transition:all .15s!important;width:100%;}}
.stButton>button:hover{{background:{C['ACCENT2']}!important;box-shadow:0 4px 14px {C['ACCENT']}55!important;transform:translateY(-1px)!important;}}
.stTabs [data-baseweb="tab-list"]{{gap:2px;background:{C['SURFACE2']};border-radius:10px;padding:3px;border:1px solid {C['BORDER']};}}
.stTabs [data-baseweb="tab"]{{border-radius:8px;font-size:13px;font-weight:500;color:{C['TEXT2']};padding:6px 16px;}}
.stTabs [aria-selected="true"]{{background:{C['ACCENT']}!important;color:white!important;}}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stSelectbox>div>div,.stNumberInput>div>div>input,.stDateInput>div>div>input{{background:{C['SURFACE2']}!important;border:1px solid {C['BORDER']}!important;border-radius:8px!important;color:{C['TEXT']}!important;font-size:13px!important;}}
label,.stSelectbox label,.stDateInput label,.stNumberInput label{{color:{C['TEXT2']}!important;font-size:12px!important;font-weight:500!important;}}
.stDataFrame{{border-radius:10px;overflow:hidden;border:1px solid {C['BORDER']};}}
.stExpander{{border:1px solid {C['BORDER']}!important;border-radius:10px!important;background:{C['SURFACE']}!important;}}
.stExpander summary{{color:{C['TEXT']}!important;}}
.stProgress>div>div{{background:{C['SURFACE2']}!important;border-radius:99px;}}
.stProgress>div>div>div{{background:{C['ACCENT']}!important;border-radius:99px;}}
.qcard{{background:{C['CARD_BG']};border:1px solid {C['BORDER']};border-radius:14px;padding:1.25rem 1.5rem;margin-bottom:.75rem;}}
.qcard-accent{{background:linear-gradient(135deg,{C['ACCENT']}18,{C['ACCENT']}08);border:1px solid {C['ACCENT']}30;}}
.page-title{{font-size:22px;font-weight:700;color:{C['TEXT']};margin-bottom:2px;letter-spacing:-.02em;}}
.page-sub{{font-size:13px;color:{C['TEXT2']};margin-bottom:1.5rem;}}
.kpi-label{{font-size:11px;font-weight:600;color:{C['TEXT3']};text-transform:uppercase;letter-spacing:.07em;margin-bottom:6px;}}
.kpi-value{{font-size:26px;font-weight:800;color:{C['TEXT']};letter-spacing:-.03em;line-height:1;}}
.kpi-sub{{font-size:12px;color:{C['TEXT2']};margin-top:5px;}}
.badge{{display:inline-block;padding:3px 9px;border-radius:99px;font-size:11px;font-weight:600;letter-spacing:.02em;}}
.badge-green{{background:{C['SUCCESS']};color:{C['SUCCESS_T']};}}
.badge-yellow{{background:{C['WARN_BG']};color:{C['WARN_T']};}}
.badge-red{{background:{C['ERR_BG']};color:{C['ERR_T']};}}
.badge-blue{{background:#0f1f3a;color:#60a5fa;}}
.badge-purple{{background:{C['ACCENT']}20;color:{C['ACCENT2']};}}
.divider{{height:1px;background:{C['BORDER']};margin:1.5rem 0;}}
</style>
""", unsafe_allow_html=True)
# ══════════════════════════════════════════════════════
# LOGIN GATE
# ══════════════════════════════════════════════════════
if not st.session_state.authenticated:
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown(f"""
        <div style="text-align:center;margin:3rem 0 2rem;">
            <div style="width:56px;height:56px;background:linear-gradient(135deg,{C['ACCENT']},{C['ACCENT2']});border-radius:16px;margin:0 auto 14px;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:800;color:white;">Q</div>
            <div style="font-size:20px;font-weight:700;color:{C['TEXT']};letter-spacing:-.02em;">Kimya Centre</div>
            <div style="font-size:12px;color:{C['TEXT3']};margin-top:4px;letter-spacing:.05em;text-transform:uppercase;">Business Suite</div>
        </div>
        """, unsafe_allow_html=True)
        passcodes     = get_passcodes()
        selected_user = st.selectbox("Select your name", list(passcodes.keys()))
        passcode      = st.text_input("Passcode", type="password", max_chars=6, placeholder="Enter passcode")
        if st.session_state.login_error:
            st.markdown(f"<div style='color:{C['ERR_T']};font-size:13px;text-align:center;margin-bottom:.5rem;'>{st.session_state.login_error}</div>", unsafe_allow_html=True)
        if st.button("Sign In", use_container_width=True):
            if passcode == passcodes.get(selected_user, ""):
                st.session_state.authenticated = True
                st.session_state.current_user  = selected_user
                st.session_state.login_error   = ""
                log_visit(selected_user)
                st.rerun()
            else:
                st.session_state.login_error = "Incorrect passcode. Please try again."
                st.rerun()
        st.markdown(f"<div class='divider'></div>", unsafe_allow_html=True)
        # Change passcode section on login page
        with st.expander("Change my passcode"):
            cp_user    = st.selectbox("Your name", list(passcodes.keys()), key="cp_user")
            cp_old     = st.text_input("Current passcode", type="password", max_chars=6, key="cp_old")
            cp_new     = st.text_input("New passcode", type="password", max_chars=6, key="cp_new")
            cp_confirm = st.text_input("Confirm new passcode", type="password", max_chars=6, key="cp_confirm")
            if st.button("Update Passcode", use_container_width=True, key="cp_btn"):
                passcodes = get_passcodes()
                if cp_old != passcodes.get(cp_user,""):
                    st.error("Current passcode is incorrect.")
                elif len(cp_new) < 4:
                    st.error("New passcode must be at least 4 characters.")
                elif cp_new != cp_confirm:
                    st.error("New passcodes do not match.")
                else:
                    passcodes[cp_user] = cp_new
                    save_dict("passcodes.json", passcodes)
                    st.success(f"Passcode updated for {cp_user}!")
    st.stop()
# ══════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="padding:1.4rem 0 1rem;border-bottom:1px solid {C['BORDER']};margin-bottom:1rem;">
        <div style="display:flex;align-items:center;gap:10px;padding:0 4px;">
            <div style="width:36px;height:36px;background:linear-gradient(135deg,{C['ACCENT']},{C['ACCENT2']});border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:800;color:white;flex-shrink:0;">Q</div>
            <div>
                <div style="font-size:13px;font-weight:700;color:{C['TEXT']};letter-spacing:-.01em;">Kimya Centre</div>
                <div style="font-size:10px;color:{C['TEXT3']};letter-spacing:.04em;text-transform:uppercase;">version 2</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    from modules.utils import USER_COLORS
    user     = st.session_state.current_user
    uc       = USER_COLORS.get(user, C["ACCENT"])
    initials = "".join([w[0].upper() for w in user.split()])
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 4px 12px;">
        <div style="width:32px;height:32px;border-radius:8px;background:{uc}22;color:{uc};font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">{initials}</div>
        <div style="font-size:13px;font-weight:500;color:{C['TEXT']};">{user}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<div style='height:1px;background:{C['BORDER']};margin-bottom:10px;'></div>", unsafe_allow_html=True)
    pages = [
        ("Dashboard","Dashboard"),("Sales Tracker","Sales"),("Analytics","Analytics"),
        ("Inventory & Costing","Inventory"),("Production","Production"),
        ("Upcoming Events","Events"),("Team Hub","Team"),
    ]
    for page_key, page_label in pages:
        if st.button(page_label, key=f"nav_{page_key}", use_container_width=True):
            st.session_state.page = page_key
            st.rerun()
    st.markdown(f"<div style='height:1px;background:{C['BORDER']};margin:10px 0;'></div>", unsafe_allow_html=True)
    if st.button("Light Mode" if DM else "Dark Mode", key="theme_toggle", use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    # Change passcode inside app
    with st.expander("Change passcode"):
        passcodes  = get_passcodes()
        ip_old     = st.text_input("Current passcode", type="password", max_chars=6, key="ip_old")
        ip_new     = st.text_input("New passcode",     type="password", max_chars=6, key="ip_new")
        ip_confirm = st.text_input("Confirm",          type="password", max_chars=6, key="ip_confirm")
        if st.button("Update", use_container_width=True, key="ip_btn"):
            if ip_old != passcodes.get(user,""):
                st.error("Wrong current passcode.")
            elif len(ip_new) < 4:
                st.error("Min 4 characters.")
            elif ip_new != ip_confirm:
                st.error("Passcodes don't match.")
            else:
                passcodes[user] = ip_new
                save_dict("passcodes.json", passcodes)
                st.success("Updated!")
    if st.button("Sign Out", key="signout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user  = None
        st.rerun()
    st.markdown(f"""
    <div style="position:fixed;bottom:1rem;left:0;width:230px;text-align:center;">
        <div style="font-size:10px;color:{C['TEXT3']};letter-spacing:.04em;">YOUR SIGNATURE SCENTS.</div>
    </div>
    """, unsafe_allow_html=True)
page = st.session_state.page
if   page == "Dashboard":           from modules import dashboard;  dashboard.show()
elif page == "Sales Tracker":       from modules import sales;       sales.show()
elif page == "Analytics":           from modules import analytics;   analytics.show()
elif page == "Inventory & Costing": from modules import inventory;   inventory.show()
elif page == "Production":          from modules import production;  production.show()
elif page == "Upcoming Events":     from modules import events;      events.show()
elif page == "Team Hub":            from modules import team;        team.show()
