import streamlit as st
from datetime import datetime, date, timedelta
from modules.utils import load, save, get_theme_colors, send_telegram, notify, now_myt

EVENT_TYPES = ["Bazaar / Market", "Exhibition", "Campus Event", "Meeting", "Product Launch", "Workshop", "Other"]

def show():
    C = get_theme_colors()
    st.markdown(f"<div class='page-title'>Upcoming Events</div><div class='page-sub'>Plan and track events, bazaars, and exhibitions</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["All Events", "Add Event"])

    with tab2:
        with st.form("event_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title     = st.text_input("Event Title *", placeholder="e.g. IIUM Bazaar Ramadan")
                etype     = st.selectbox("Event Type", EVENT_TYPES)
                location  = st.text_input("Location", placeholder="e.g. IIUM Gombak, Mahallah Square")
            with col2:
                edate     = st.date_input("Event Date", value=date.today() + timedelta(days=7))
                end_date  = st.date_input("End Date (if multi-day)", value=date.today() + timedelta(days=7))
                reminder  = st.selectbox("Remind me", ["1 day before", "3 days before", "1 week before", "No reminder"])

            target      = st.text_input("Target / Goal", placeholder="e.g. Sell 30 units, collect 50 leads")
            notes       = st.text_area("Notes / Checklist", placeholder="What to bring, who's attending, prep needed...", height=100)
            assigned    = st.multiselect("Team members attending", ["Dr. Shirwan", "Eqmal", "Syafa", "Nureen"])

            if st.form_submit_button("Add Event", use_container_width=True):
                if not title.strip():
                    st.error("Event title required.")
                else:
                    events = load("events.json")
                    events.append({
                        "id":        f"EVT{len(events)+1:03d}",
                        "title":     title.strip(),
                        "type":      etype,
                        "location":  location.strip(),
                        "date":      str(edate),
                        "end_date":  str(end_date),
                        "reminder":  reminder,
                        "target":    target.strip(),
                        "notes":     notes.strip(),
                        "assigned":  assigned,
                        "status":    "Upcoming",
                        "created":   datetime.now().isoformat(),
                    })
                    save("events.json", events)
                    notify(
                        f"📅 <b>New Event Added!</b>\n"
                        f"🎪 {title.strip()} ({etype})\n"
                        f"📍 {location.strip() or '—'}\n"
                        f"🗓 {str(edate)}\n"
                        f"👥 {', '.join(assigned) or '—'}\n"
                        f"🎯 {target.strip() or '—'}\n"
                        f"🕐 {now_myt().strftime('%d %b %Y %I:%M %p MYT')}"
                    )
                    st.success(f"Event '{title}' added!")

    with tab1:
        events = load("events.json")
        today = date.today()

        upcoming = sorted([e for e in events if e.get("date","") >= str(today)], key=lambda x: x.get("date",""))
        past     = sorted([e for e in events if e.get("date","") < str(today)],  key=lambda x: x.get("date",""), reverse=True)

        if not events:
            st.info("No events yet. Add your first event.")
            return

        if upcoming:
            st.markdown(f"<div style='font-size:14px;font-weight:600;color:{C['TEXT']};margin-bottom:12px;'>Upcoming ({len(upcoming)})</div>", unsafe_allow_html=True)
            for e in upcoming:
                edate     = e.get("date","")
                days_left = (date.fromisoformat(edate) - today).days
                urgency   = "badge-red" if days_left <= 3 else "badge-yellow" if days_left <= 7 else "badge-blue"
                dlabel    = "Today" if days_left == 0 else f"In {days_left} day{'s' if days_left>1 else ''}"

                with st.expander(f"{e.get('title')}  ·  {edate}  ·  {e.get('type','')}"):
                    col1, col2 = st.columns([2,1])
                    with col1:
                        st.markdown(f"**Location:** {e.get('location','—')}")
                        if e.get("end_date") and e.get("end_date") != edate:
                            st.markdown(f"**End Date:** {e.get('end_date')}")
                        st.markdown(f"**Attending:** {', '.join(e.get('assigned',[])) or '—'}")
                        if e.get("target"):
                            st.markdown(f"**Target:** {e.get('target')}")
                        if e.get("notes"):
                            st.markdown(f"**Notes:**\n{e.get('notes')}")
                    with col2:
                        st.markdown(f"""
                        <div class="qcard" style="text-align:center;padding:12px;">
                            <span class="badge {urgency}">{dlabel}</span>
                            <div style="font-size:11px;color:{C['TEXT2']};margin-top:8px;">{e.get('reminder','')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    new_status = st.selectbox("Status", ["Upcoming","Completed","Cancelled"],
                                               index=["Upcoming","Completed","Cancelled"].index(e.get("status","Upcoming")),
                                               key=f"evts_{e['id']}")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Update Status", key=f"evtu_{e['id']}", use_container_width=True):
                            all_events = load("events.json")
                            for ev in all_events:
                                if ev["id"] == e["id"]:
                                    ev["status"] = new_status
                            save("events.json", all_events)
                            st.success("Updated!")
                            st.rerun()
                    with col_b:
                        if st.button("Delete", key=f"evtd_{e['id']}", use_container_width=True):
                            all_events = load("events.json")
                            all_events = [ev for ev in all_events if ev["id"] != e["id"]]
                            save("events.json", all_events)
                            st.rerun()

        if past:
            st.markdown(f"<div class='divider'></div>", unsafe_allow_html=True)
            with st.expander(f"Past events ({len(past)})"):
                for e in past[:10]:
                    st.markdown(f"- ~~{e.get('title')}~~ &nbsp; {e.get('date')} &nbsp; {e.get('location','')}")
