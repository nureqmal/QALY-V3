import streamlit as st
from datetime import datetime, date
from modules.utils import load, save, get_theme_colors, send_telegram, notify, now_myt

MEMBERS = ["Dr. Shirwan", "Eqmal", "Syafa", "Nureen"]

def show():
    C = get_theme_colors()
    st.markdown(f"<div class='page-title'>Team Hub</div><div class='page-sub'>Meeting notes and personal notes</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Meeting Notes", "Personal Notes"])

    # ── Meeting Notes ─────────────────────────────────
    with tab1:
        col_form, col_list = st.columns([1, 1.4])

        with col_form:
            st.markdown(f"<div style='font-size:13px;font-weight:600;color:{C['TEXT']};margin-bottom:12px;'>New Meeting Note</div>", unsafe_allow_html=True)
            with st.form("meeting_form", clear_on_submit=True):
                m_title      = st.text_input("Meeting Title *", placeholder="e.g. Weekly Sync")
                m_date       = st.date_input("Date", value=date.today())
                m_attendees  = st.multiselect("Attendees", MEMBERS, default=MEMBERS)
                m_agenda     = st.text_area("Discussion / Agenda", height=90, placeholder="Key topics discussed...")
                m_decisions  = st.text_area("Decisions Made", height=70, placeholder="What was agreed upon...")
                m_actions    = st.text_area("Action Items", height=90,
                                            placeholder="1. [Name] — task — by [date]\n2. ...")

                if st.form_submit_button("Save Meeting Notes", use_container_width=True):
                    if m_title.strip():
                        notes = load("meeting_notes.json")
                        notes.append({
                            "id":         f"MTG{len(notes)+1:03d}",
                            "title":      m_title.strip(),
                            "date":       str(m_date),
                            "attendees":  m_attendees,
                            "agenda":     m_agenda.strip(),
                            "decisions":  m_decisions.strip(),
                            "actions":    m_actions.strip(),
                            "created_by": st.session_state.get("current_user","?"),
                            "created_at": datetime.now().isoformat(),
                        })
                        save("meeting_notes.json", notes)
                        notify(
                            f"📝 <b>New Meeting Notes!</b>\n"
                            f"📌 {m_title.strip()}\n"
                            f"🗓 {str(m_date)}\n"
                            f"👥 {', '.join(m_attendees) or '—'}\n"
                            f"✅ {m_decisions.strip()[:200] or '—'}\n"
                            f"📋 {m_actions.strip()[:200] or '—'}\n"
                            f"🕐 {now_myt().strftime('%d %b %Y %I:%M %p MYT')}"
                        )
                        st.success("Meeting notes saved!")
                        st.rerun()
                    else:
                        st.error("Title required.")

        with col_list:
            st.markdown(f"<div style='font-size:13px;font-weight:600;color:{C['TEXT']};margin-bottom:12px;'>Previous Meetings</div>", unsafe_allow_html=True)
            notes = load("meeting_notes.json")
            if not notes:
                st.markdown(f"<div style='color:{C['TEXT2']};font-size:13px;'>No meeting notes yet.</div>", unsafe_allow_html=True)
            else:
                filter_member = st.selectbox("Filter by attendee", ["All"] + MEMBERS, key="mtg_filter")
                filtered = notes if filter_member == "All" else [n for n in notes if filter_member in n.get("attendees",[])]
                filtered = sorted(filtered, key=lambda x: x.get("date",""), reverse=True)

                for n in filtered:
                    with st.expander(f"{n.get('title')}  ·  {n.get('date')}"):
                        st.markdown(f"**Attendees:** {', '.join(n.get('attendees',[]))}")
                        if n.get("agenda"):
                            st.markdown(f"**Discussion:**")
                            st.markdown(n.get("agenda"))
                        if n.get("decisions"):
                            st.markdown(f"**Decisions:**")
                            st.markdown(n.get("decisions"))
                        if n.get("actions"):
                            st.markdown(f"**Action Items:**")
                            st.markdown(n.get("actions"))
                        st.markdown(f"<div style='font-size:11px;color:{C['TEXT3']};margin-top:8px;'>Recorded by {n.get('created_by','?')}</div>", unsafe_allow_html=True)

                        if st.button("Delete", key=f"delm_{n['id']}"):
                            all_notes = load("meeting_notes.json")
                            all_notes = [x for x in all_notes if x["id"] != n["id"]]
                            save("meeting_notes.json", all_notes)
                            st.rerun()

    # ── Personal Notes ────────────────────────────────
    with tab2:
        current_user = st.session_state.get("current_user", "Dr. Shirwan")
        st.markdown(f"<div style='font-size:13px;color:{C['TEXT2']};margin-bottom:1rem;'>Private notes for <b style=\"color:{C['TEXT']};\">{current_user}</b> — only visible when logged in as you.</div>", unsafe_allow_html=True)

        all_personal = load("personal_notes.json")
        my_notes = [n for n in all_personal if n.get("owner") == current_user]

        with st.form("personal_note_form", clear_on_submit=True):
            col1, col2 = st.columns([3,1])
            with col1:
                p_title   = st.text_input("Title *", placeholder="e.g. Supplier contact, idea, reminder")
                p_content = st.text_area("Note", height=100, placeholder="Write anything here...")
            with col2:
                p_tag     = st.selectbox("Tag", ["General","Idea","Reminder","Supplier","Finance","Other"])
                p_pinned  = st.checkbox("Pin this note")

            if st.form_submit_button("Save Note", use_container_width=True):
                if p_title.strip():
                    all_personal.append({
                        "id":      f"PN{len(all_personal)+1:04d}",
                        "owner":   current_user,
                        "title":   p_title.strip(),
                        "content": p_content.strip(),
                        "tag":     p_tag,
                        "pinned":  p_pinned,
                        "created": datetime.now().isoformat(),
                    })
                    save("personal_notes.json", all_personal)
                    st.success("Note saved!")
                    st.rerun()
                else:
                    st.error("Title required.")

        if my_notes:
            # Pinned first
            pinned   = [n for n in my_notes if n.get("pinned")]
            unpinned = [n for n in my_notes if not n.get("pinned")]
            ordered  = pinned + sorted(unpinned, key=lambda x: x.get("created",""), reverse=True)

            tag_colors = {
                "General":"badge-purple","Idea":"badge-blue","Reminder":"badge-yellow",
                "Supplier":"badge-green","Finance":"badge-green","Other":"badge-purple",
            }

            for n in ordered:
                pin_icon = "  [Pinned]" if n.get("pinned") else ""
                with st.expander(f"{n.get('title')}{pin_icon}  ·  {n.get('tag','')}"):
                    if n.get("content"):
                        st.markdown(n.get("content"))
                    st.markdown(f"<div style='font-size:11px;color:{C['TEXT3']};'>{n.get('created','')[:16]}</div>", unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        new_pin = st.checkbox("Pinned", value=n.get("pinned",False), key=f"pin_{n['id']}")
                        if new_pin != n.get("pinned"):
                            all_p = load("personal_notes.json")
                            for note in all_p:
                                if note["id"] == n["id"]:
                                    note["pinned"] = new_pin
                            save("personal_notes.json", all_p)
                            st.rerun()
                    with col_b:
                        if st.button("Delete", key=f"delpn_{n['id']}", use_container_width=True):
                            all_p = load("personal_notes.json")
                            all_p = [x for x in all_p if x["id"] != n["id"]]
                            save("personal_notes.json", all_p)
                            st.rerun()
        else:
            st.markdown(f"<div style='color:{C['TEXT2']};font-size:13px;'>No personal notes yet.</div>", unsafe_allow_html=True)
