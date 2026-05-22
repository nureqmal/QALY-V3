import streamlit as st
from datetime import date, timedelta
from modules.utils import load, save, get_theme_colors, PRODUCTS, MEMBERS, now_myt, send_telegram, notify

PROD_STATUSES = ["Active", "Completed", "On Hold"]
ML_PER_BOTTLE = 100  # all products are 100ml


def show():
    C = get_theme_colors()
    st.markdown("<div class='page-title'>Production</div><div class='page-sub'>Track batches, base stock, bottled units, and pour-on-demand</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["All Batches", "New Batch", "Pour into Bottles"])

    # ══════════════════════════════════════════════════
    # TAB: NEW BATCH
    # ══════════════════════════════════════════════════
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)

        if "new_batch_products" not in st.session_state:
            st.session_state.new_batch_products = []

        col1, col2 = st.columns(2)
        with col1:
            batch_no     = st.text_input("Batch No. *", placeholder="e.g. B001", key="nb_batchno")
            prod_date    = st.date_input("Production Date", value=date.today(), key="nb_date")
            volume_L     = st.number_input("Total Base Volume (Litres)", min_value=0.0, step=0.1, key="nb_vol",
                                           help="Total liquid base produced e.g. 1.0 L")
            duration_hrs = st.number_input("Duration (hours)", min_value=0.0, step=0.5, key="nb_dur")
        with col2:
            pic         = st.multiselect("Person-in-Charge", MEMBERS, key="nb_pic")
            status      = st.selectbox("Batch Status", PROD_STATUSES, key="nb_status")
            expiry_date = st.date_input("Expiry / Best Before",
                                        value=date.today() + timedelta(days=365), key="nb_exp")
            notes       = st.text_area("Notes / Observations", height=89, key="nb_notes",
                                       placeholder="QC notes, adjustments...")

        st.markdown(f"<div style='font-size:13px;font-weight:500;color:{C['TEXT']};margin:1rem 0 .4rem;'>Bottles filled now (optional)</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:12px;color:{C['TEXT2']};margin-bottom:.75rem;'>Add only what you bottle immediately. Leave empty if storing all as base.</div>", unsafe_allow_html=True)

        col_p1, col_p2, col_p3 = st.columns([3, 1, 1])
        with col_p1:
            add_product = st.selectbox("Product", [p for p in PRODUCTS.keys() if "Couple" not in p],
                                       key="nb_addprod", label_visibility="collapsed")
        with col_p2:
            add_units = st.number_input("Units", min_value=1, value=1, key="nb_addunits",
                                        label_visibility="collapsed")
        with col_p3:
            if st.button("Add", use_container_width=True, key="nb_addprodbtn"):
                existing = next((x for x in st.session_state.new_batch_products
                                 if x["product"] == add_product), None)
                if existing:
                    existing["units"] = add_units
                else:
                    st.session_state.new_batch_products.append(
                        {"product": add_product, "units": add_units}
                    )
                st.rerun()

        # Show added bottles
        bottled_ml = 0
        if st.session_state.new_batch_products:
            for bp in st.session_state.new_batch_products:
                bottled_ml += bp["units"] * ML_PER_BOTTLE
                col_s, col_r2 = st.columns([5, 1])
                with col_s:
                    st.markdown(f"""
                    <div class="qcard" style="padding:7px 14px;display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="font-size:13px;color:{C['TEXT']};font-weight:500;">{bp['product']}</span>
                        <span style="font-size:13px;color:{C['ACCENT']};font-weight:600;">{bp['units']} bottles ({bp['units']*ML_PER_BOTTLE} ml)</span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_r2:
                    if st.button("x", key=f"rm_{bp['product']}", use_container_width=True):
                        st.session_state.new_batch_products = [
                            x for x in st.session_state.new_batch_products
                            if x["product"] != bp["product"]
                        ]
                        st.rerun()

        total_vol_ml     = volume_L * 1000
        remaining_base   = max(total_vol_ml - bottled_ml, 0)
        st.markdown(f"""
        <div class="qcard" style="padding:10px 14px;margin-top:.5rem;">
            <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                <div><div class="kpi-label">Total base</div><div style="font-size:16px;font-weight:700;color:{C['TEXT']};">{total_vol_ml:.0f} ml</div></div>
                <div><div class="kpi-label">Bottled now</div><div style="font-size:16px;font-weight:700;color:{C['ACCENT']};">{bottled_ml:.0f} ml ({sum(p['units'] for p in st.session_state.new_batch_products)} units)</div></div>
                <div><div class="kpi-label">Base stored</div><div style="font-size:16px;font-weight:700;color:{C['WARN_T']};">{remaining_base:.0f} ml</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Record Batch", use_container_width=True, key="nb_submit"):
            if not batch_no.strip():
                st.error("Batch number is required.")
            elif volume_L <= 0:
                st.error("Volume must be greater than 0.")
            elif bottled_ml > total_vol_ml:
                st.error(f"Bottled volume ({bottled_ml}ml) exceeds total base ({total_vol_ml:.0f}ml).")
            else:
                batches = load("production.json")
                total_units = sum(p["units"] for p in st.session_state.new_batch_products)
                batches.append({
                    "id":               f"PROD{len(batches)+1:04d}",
                    "batch_no":         batch_no.strip(),
                    "products":         [
                        {
                            "product":   p["product"],
                            "units":     p["units"],       # total ever bottled
                            "remaining": p["units"],       # current bottled stock
                        }
                        for p in st.session_state.new_batch_products
                    ],
                    "date":             str(prod_date),
                    "volume_L":         volume_L,
                    "total_base_ml":    total_vol_ml,
                    "bottled_ml":       float(bottled_ml),
                    "remaining_base_ml":float(remaining_base),
                    "units_produced":   total_units,
                    "units_remaining":  total_units,
                    "duration_hrs":     duration_hrs,
                    "pic":              pic,
                    "status":           status,
                    "expiry_date":      str(expiry_date),
                    "notes":            notes.strip(),
                    "recorded_by":      st.session_state.get("current_user", "?"),
                    "created_at":       now_myt().isoformat(),
                    "pour_log":         [],
                })
                save("production.json", batches)
                notify(
                    f"🧪 <b>New Production Batch!</b>\n"
                    f"📋 Batch: {batch_no.strip()}\n"
                    f"🧴 Base: {volume_L}L ({total_vol_ml:.0f}ml)\n"
                    f"🍶 Bottled now: {total_units} units ({bottled_ml:.0f}ml)\n"
                    f"💾 Base stored: {remaining_base:.0f}ml\n"
                    f"👤 PIC: {', '.join(pic) or '—'}\n"
                    f"🕐 {now_myt().strftime('%d %b %Y %I:%M %p MYT')}"
                )
                st.session_state.new_batch_products = []
                st.success(f"Batch {batch_no.strip()} recorded — {total_units} units bottled, {remaining_base:.0f}ml base stored")
                st.rerun()

    # ══════════════════════════════════════════════════
    # TAB: POUR INTO BOTTLES
    # ══════════════════════════════════════════════════
    with tab3:
        st.markdown(f"<div style='font-size:14px;font-weight:500;color:{C['TEXT']};margin-bottom:4px;'>Pour base into bottles</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:12px;color:{C['TEXT2']};margin-bottom:1rem;'>When you get an order or decide to bottle stored base, record it here. System will deduct from base stock and add to bottled stock.</div>", unsafe_allow_html=True)

        batches = load("production.json")
        active  = [b for b in batches if b.get("status") == "Active" and b.get("remaining_base_ml", 0) > 0]

        if not active:
            st.info("No active batches with stored base. Record a new batch first.")
        else:
            batch_options = {f"Batch {b['batch_no']} — {b['remaining_base_ml']:.0f}ml remaining base": b["id"] for b in active}
            selected_label = st.selectbox("Select batch", list(batch_options.keys()))
            selected_id    = batch_options[selected_label]
            batch          = next(b for b in batches if b["id"] == selected_id)

            remaining_base_ml = batch.get("remaining_base_ml", 0)

            st.markdown(f"""
            <div class="qcard qcard-accent" style="padding:10px 14px;margin-bottom:1rem;">
                <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                    <div><div class="kpi-label">Batch</div><div style="font-size:15px;font-weight:700;color:{C['TEXT']};">{batch['batch_no']}</div></div>
                    <div><div class="kpi-label">Base remaining</div><div style="font-size:15px;font-weight:700;color:{C['WARN_T']};">{remaining_base_ml:.0f} ml</div></div>
                    <div><div class="kpi-label">Can bottle</div><div style="font-size:15px;font-weight:700;color:{C['ACCENT']};">{int(remaining_base_ml // ML_PER_BOTTLE)} units max</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                pour_product = st.selectbox("Product to bottle", [p for p in PRODUCTS.keys() if "Couple" not in p], key="pour_prod")
            with col2:
                max_units = int(remaining_base_ml // ML_PER_BOTTLE)
                pour_units = st.number_input("Units to bottle", min_value=1, max_value=max(max_units, 1),
                                             value=min(1, max_units), key="pour_units")
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Pour & Record", use_container_width=True, key="pour_btn"):
                    ml_used = pour_units * ML_PER_BOTTLE
                    if ml_used > remaining_base_ml:
                        st.error(f"Not enough base. Need {ml_used}ml, have {remaining_base_ml:.0f}ml.")
                    else:
                        all_b = load("production.json")
                        for b in all_b:
                            if b["id"] == selected_id:
                                b["remaining_base_ml"] = remaining_base_ml - ml_used
                                b["bottled_ml"]        = b.get("bottled_ml", 0) + ml_used

                                # Update or add product entry
                                existing_p = next((p for p in b.get("products", []) if p["product"] == pour_product), None)
                                if existing_p:
                                    existing_p["units"]     += pour_units
                                    existing_p["remaining"] += pour_units
                                else:
                                    b.setdefault("products", []).append({
                                        "product":   pour_product,
                                        "units":     pour_units,
                                        "remaining": pour_units,
                                    })

                                b["units_produced"]  = sum(p["units"]     for p in b.get("products", []))
                                b["units_remaining"] = sum(p["remaining"] for p in b.get("products", []))

                                # Log the pour
                                b.setdefault("pour_log", []).append({
                                    "product":    pour_product,
                                    "units":      pour_units,
                                    "ml_used":    ml_used,
                                    "timestamp":  now_myt().isoformat(),
                                    "by":         st.session_state.get("current_user", "?"),
                                })

                                if b["remaining_base_ml"] <= 0 and b["units_remaining"] == 0:
                                    b["status"] = "Completed"

                        save("production.json", all_b)
                        st.success(f"Poured {pour_units} x {pour_product} ({ml_used}ml) from Batch {batch['batch_no']}")
                        st.rerun()

            # Pour log for selected batch
            pour_log = batch.get("pour_log", [])
            if pour_log:
                st.markdown(f"<div style='font-size:12px;font-weight:500;color:{C['TEXT2']};margin:1rem 0 .5rem;'>Pour history for Batch {batch['batch_no']}</div>", unsafe_allow_html=True)
                for entry in reversed(pour_log):
                    try:
                        from datetime import datetime
                        ts = datetime.fromisoformat(entry["timestamp"]).strftime("%d %b %Y %I:%M %p")
                    except:
                        ts = entry.get("timestamp", "")
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid {C['BORDER']};font-size:12px;">
                        <span style="color:{C['TEXT']};">{entry['units']} x {entry['product']}</span>
                        <span style="color:{C['TEXT2']};">{entry['ml_used']}ml &nbsp;·&nbsp; {ts} &nbsp;·&nbsp; {entry.get('by','?')}</span>
                    </div>
                    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # TAB: ALL BATCHES
    # ══════════════════════════════════════════════════
    with tab1:
        batches = load("production.json")
        if not batches:
            st.info("No production batches yet. Add your first batch.")
            return

        # KPIs
        active_list  = [b for b in batches if b.get("status") == "Active"]
        total_L      = sum(b.get("volume_L", 0) for b in batches)
        total_base   = sum(b.get("remaining_base_ml", 0) for b in active_list)
        total_bottled= sum(b.get("units_remaining", 0) for b in active_list)

        col1, col2, col3, col4 = st.columns(4)
        for col, (label, val) in zip([col1, col2, col3, col4], [
            ("TOTAL BATCHES",    str(len(batches))),
            ("ACTIVE BATCHES",   str(len(active_list))),
            ("BASE IN STORAGE",  f"{total_base:.0f} ml"),
            ("BOTTLED IN STOCK", str(total_bottled)),
        ]):
            with col:
                st.markdown(f'<div class="qcard"><div class="kpi-label">{label}</div><div class="kpi-value" style="font-size:22px;">{val}</div></div>', unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Filters
        col1, col2 = st.columns(2)
        with col1: f_status = st.selectbox("Filter status",  ["All"] + PROD_STATUSES, key="fstat")
        with col2: f_search = st.text_input("Search batch no.", key="fsearch_b", placeholder="e.g. B001")

        filtered = batches
        if f_status != "All": filtered = [b for b in filtered if b.get("status") == f_status]
        if f_search:          filtered = [b for b in filtered if f_search.lower() in b.get("batch_no", "").lower()]
        filtered = sorted(filtered, key=lambda x: x.get("date", ""), reverse=True)

        for b in filtered:
            bc           = {"Active": "badge-green", "Completed": "badge-purple", "On Hold": "badge-yellow"}.get(b.get("status", ""), "badge-blue")
            products_list = b.get("products", [])
            prod_label   = ", ".join(p["product"].split(" ")[0] for p in products_list) if products_list else b.get("product", "?")
            rem_base_ml  = b.get("remaining_base_ml", 0)
            total_units  = b.get("units_produced", 0)
            rem_units    = b.get("units_remaining", total_units)

            with st.expander(f"Batch {b.get('batch_no','?')}  ·  {prod_label}  ·  {b.get('date','?')}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Total base made:** {b.get('volume_L',0)} L ({b.get('total_base_ml',0):.0f} ml)")
                    st.write(f"**Base in storage:** {rem_base_ml:.0f} ml")
                    st.write(f"**Can still bottle:** {int(rem_base_ml // ML_PER_BOTTLE)} units")
                with col2:
                    st.write(f"**Duration:** {b.get('duration_hrs',0)} hrs")
                    st.write(f"**PIC:** {', '.join(b.get('pic',[])) or '—'}")
                    st.write(f"**Expiry:** {b.get('expiry_date','—')}")
                    st.write(f"**Recorded by:** {b.get('recorded_by','?')}")
                with col3:
                    st.markdown(f'<span class="badge {bc}">{b.get("status")}</span>', unsafe_allow_html=True)
                    if b.get("notes"):
                        st.write(f"**Notes:** {b.get('notes')}")

                # Per-product bottled stock
                if products_list:
                    st.markdown(f"<div style='font-size:12px;font-weight:500;color:{C['TEXT2']};margin:10px 0 6px;'>Bottled stock per product</div>", unsafe_allow_html=True)
                    for p in products_list:
                        rem  = p.get("remaining", p.get("units", 0))
                        tot  = p.get("units", 0)
                        pct  = rem / max(tot, 1)
                        col_a, col_b2 = st.columns([3, 1])
                        with col_a:
                            st.markdown(f"""
                            <div style="margin-bottom:8px;">
                                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:3px;">
                                    <span style="color:{C['TEXT']};font-weight:500;">{p['product']}</span>
                                    <span style="color:{C['TEXT2']};">{rem}/{tot} bottles remaining</span>
                                </div>
                                <div style="background:{C['BORDER']};border-radius:99px;height:6px;">
                                    <div style="background:{C['ACCENT']};width:{pct*100:.0f}%;height:6px;border-radius:99px;"></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with col_b2:
                            new_rem = st.number_input("", min_value=0, max_value=tot,
                                                      value=rem, key=f"prem_{b['id']}_{p['product'][:4]}",
                                                      label_visibility="collapsed")
                            if new_rem != rem:
                                if st.button("Save", key=f"psave_{b['id']}_{p['product'][:4]}", use_container_width=True):
                                    all_b = load("production.json")
                                    for batch in all_b:
                                        if batch["id"] == b["id"]:
                                            for prod in batch.get("products", []):
                                                if prod["product"] == p["product"]:
                                                    prod["remaining"] = new_rem
                                            batch["units_remaining"] = sum(pr.get("remaining", 0) for pr in batch.get("products", []))
                                    save("production.json", all_b)
                                    st.success("Updated!")
                                    st.rerun()

                # Base stock bar
                total_base_ml = b.get("total_base_ml", b.get("volume_L", 0) * 1000)
                base_pct = rem_base_ml / max(total_base_ml, 1)
                st.markdown(f"""
                <div style="margin:8px 0 4px;">
                    <div style="font-size:11px;color:{C['TEXT2']};margin-bottom:3px;">Base remaining: {rem_base_ml:.0f} / {total_base_ml:.0f} ml</div>
                    <div style="background:{C['BORDER']};border-radius:99px;height:8px;">
                        <div style="background:{C['WARN_T']};width:{base_pct*100:.0f}%;height:8px;border-radius:99px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Status update + delete
                st.markdown("<br>", unsafe_allow_html=True)
                col_a, col_b2, col_c, col_d = st.columns(4)
                with col_a:
                    new_status = st.selectbox("Status", PROD_STATUSES,
                                              index=PROD_STATUSES.index(b.get("status", "Active")),
                                              key=f"pst_{b['id']}")
                with col_b2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Update Status", key=f"pbtn_{b['id']}", use_container_width=True):
                        all_b = load("production.json")
                        for batch in all_b:
                            if batch["id"] == b["id"]:
                                batch["status"] = new_status
                        save("production.json", all_b)
                        st.success("Updated!")
                        st.rerun()
                with col_c:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("")
                with col_d:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Delete Batch", key=f"pdel_{b['id']}", use_container_width=True):
                        all_b = load("production.json")
                        all_b = [x for x in all_b if x["id"] != b["id"]]
                        save("production.json", all_b)
                        st.success("Deleted.")
                        st.rerun()

                # Pour log
                pour_log = b.get("pour_log", [])
                if pour_log:
                    with st.expander(f"Pour history ({len(pour_log)} entries)"):
                        for entry in reversed(pour_log):
                            try:
                                from datetime import datetime
                                ts = datetime.fromisoformat(entry["timestamp"]).strftime("%d %b %Y %I:%M %p")
                            except:
                                ts = entry.get("timestamp", "")
                            st.markdown(f"- {entry['units']} x {entry['product']} ({entry['ml_used']}ml) — {ts} by {entry.get('by','?')}")
