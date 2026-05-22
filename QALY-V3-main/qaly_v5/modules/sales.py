import streamlit as st
import pandas as pd
import io
from datetime import datetime, date
from modules.utils import load, save, load_dict, save_dict, get_theme_colors, PRODUCTS, CHANNELS, STATUSES, GFORM_SHEET_ID, GFORM_GID, now_myt, send_telegram, notify 


def build_csv_url(sheet_id, gid):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data(ttl=30)
def fetch_orders(url):
    try:
        df = pd.read_csv(url)
        return df, None
    except Exception as e:
        return None, str(e)


# ── P&L helpers ───────────────────────────────────────

def get_cogs_map():
    costing = load("costing.json")
    result  = {}
    for c in costing:
        mat_cost = sum(i.get("line_cost", 0) for i in c.get("ingredients", []))
        result[c["product"]] = round(mat_cost + c.get("overhead", 0), 4)
    return result


def filter_sales(sales, period, year, month=None):
    out = []
    for o in sales:
        try:
            dt = date.fromisoformat(o.get("date", ""))
        except:
            continue
        if period == "Monthly" and month:
            if dt.year == year and dt.month == month:
                out.append(o)
        elif period == "Yearly":
            if dt.year == year:
                out.append(o)
        else:
            out.append(o)
    return out


def val_color(val, positive_good=True):
    if val > 0:   return "#4ade80" if positive_good else "#f87171"
    elif val < 0: return "#f87171" if positive_good else "#4ade80"
    return "#8b88a8"


# ── Main ──────────────────────────────────────────────

def show():
    C = get_theme_colors()
    st.markdown("<div class='page-title'>Sales Tracker</div><div class='page-sub'>Live Google Form orders + Shopee / manual entries + P&L</div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Google Form Orders", "Shopee / Manual", "All Manual Orders", "P&L Statement"])

    # ── Tab 1: Google Form ────────────────────────────
    with tab1:
        cfg       = load_dict("config.json")
        auto_url  = build_csv_url(GFORM_SHEET_ID, GFORM_GID)
        saved_url = cfg.get("gsheet_url", auto_url)

        with st.expander("Connection settings", expanded=(not cfg.get("gsheet_url"))):
            st.markdown(f"""
            <div class="qcard qcard-accent" style="margin-bottom:1rem;">
                <div style="font-size:13px;font-weight:600;color:{C['TEXT']};margin-bottom:6px;">How to enable live sync</div>
                <div style="font-size:12px;color:{C['TEXT2']};line-height:1.9;">
                    1. Open your Google Spreadsheet (form responses)<br>
                    2. File &gt; Share &gt; Publish to web<br>
                    3. Select the correct sheet tab &gt; CSV format &gt; Publish<br>
                    4. Paste the published CSV URL below
                </div>
            </div>
            """, unsafe_allow_html=True)
            csv_url = st.text_input("Published CSV URL", value=saved_url,
                                    placeholder="https://docs.google.com/spreadsheets/d/.../pub?output=csv")
            if st.button("Save & Connect", use_container_width=True, key="save_url"):
                cfg["gsheet_url"] = csv_url
                save_dict("config.json", cfg)
                st.cache_data.clear()
                st.success("Saved!")
                st.rerun()

        active_url = cfg.get("gsheet_url", auto_url)
        col_refresh, col_info = st.columns([1, 3])
        with col_refresh:
            if st.button("Refresh Now", use_container_width=True, key="refresh_gsheet"):
                st.cache_data.clear()
                st.rerun()
        with col_info:
            st.markdown(f"<div style='font-size:12px;color:{C['TEXT2']};padding-top:8px;'>Auto-refreshes every 30 seconds</div>", unsafe_allow_html=True)

        with st.spinner("Loading orders from Google Form..."):
            df, err = fetch_orders(active_url)

        # ── Detect new Google Form orders & push WA notification ──
        if df is not None and not df.empty and not err:
            cfg2          = load_dict("config.json")
            col_map       = cfg2.get("col_map", {})
            last_count    = cfg2.get("gform_last_count", 0)
            current_count = len(df)

            if current_count > last_count:
                new_rows = df.iloc[last_count:current_count]
                for _, row in new_rows.iterrows():
                    name_col    = col_map.get("name")
                    product_col = col_map.get("product")
                    qty_col     = col_map.get("qty")
                    channel_col = col_map.get("channel")
                    date_col    = col_map.get("date")

                    cust_name = str(row[name_col]).strip()    if name_col    and name_col    in row else "—"
                    product   = str(row[product_col]).strip() if product_col and product_col in row else "—"
                    qty       = str(row[qty_col]).strip()     if qty_col     and qty_col     in row else "—"
                    channel   = str(row[channel_col]).strip() if channel_col and channel_col in row else "—"
                    timestamp = str(row[date_col]).strip()    if date_col    and date_col    in row else now_myt().strftime("%d %b %Y %I:%M %p")

                    notify(
                        f"📋 New Google Form Order!\n"
                        f"👤 {cust_name}\n"
                        f"📦 {product} x{qty}\n"
                        f"📍 {channel}\n"
                        f"🕐 {timestamp}"
                    )

                cfg2["gform_last_count"] = current_count
                save_dict("config.json", cfg2)

        if err:
            st.error(f"Could not fetch data: {err}")
            st.markdown(f"""
            <div class="qcard" style="border:1px solid {C['WARN_T']}40;background:{C['WARN_BG']};">
                <div style="font-size:13px;font-weight:600;color:{C['WARN_T']};">Spreadsheet not published yet</div>
                <div style="font-size:12px;color:{C['TEXT2']};margin-top:4px;line-height:1.7;">
                    File → Share → Publish to web → response sheet tab → CSV → Publish. Paste URL above.
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif df is not None and not df.empty:
            st.markdown(f"""
            <div style="display:flex;gap:12px;margin-bottom:1rem;flex-wrap:wrap;">
                <span class="badge badge-green">{len(df)} total responses</span>
                <span class="badge badge-purple">Live from Google Form</span>
            </div>
            """, unsafe_allow_html=True)

            cols      = df.columns.tolist()
            saved_map = cfg.get("col_map", {})

            with st.expander("Column mapping"):
                c1, c2, c3, c4, c5 = st.columns(5)
                def safe_idx(key):
                    v = saved_map.get(key)
                    return cols.index(v) if v in cols else 0
                with c1: cn = st.selectbox("Name",      cols, index=safe_idx("name"),    key="cn")
                with c2: cp = st.selectbox("Product",   cols, index=safe_idx("product"), key="cp")
                with c3: cq = st.selectbox("Quantity",  cols, index=safe_idx("qty"),     key="cq")
                with c4: cc = st.selectbox("Channel",   cols, index=safe_idx("channel"), key="cc")
                with c5: cd = st.selectbox("Timestamp", cols, index=safe_idx("date"),    key="cd")
                if st.button("Save mapping"):
                    cfg["col_map"] = {"name": cn, "product": cp, "qty": cq, "channel": cc, "date": cd}
                    save_dict("config.json", cfg)
                    st.success("Mapping saved!")

            display_cols = [c for c in [
                cfg.get("col_map", {}).get("date"),
                cfg.get("col_map", {}).get("name"),
                cfg.get("col_map", {}).get("product"),
                cfg.get("col_map", {}).get("qty"),
                cfg.get("col_map", {}).get("channel"),
            ] if c and c in df.columns]

            show_df = df[display_cols] if display_cols else df
            try:
                sort_col = show_df.columns[0]
                if show_df.columns.tolist().count(sort_col) == 1:
                    show_df = show_df.sort_values(sort_col, ascending=False)
            except Exception:
                pass
            st.dataframe(show_df, use_container_width=True, hide_index=True)
        else:
            st.info("No responses found. Make sure the sheet is published and has data.")

    # ── Tab 2: Shopee / Manual ────────────────────────
    with tab2:
        st.markdown(f"<div style='font-size:14px;font-weight:500;color:{C['TEXT']};margin-bottom:1rem;'>Record Shopee sale or any manual order</div>", unsafe_allow_html=True)

        with st.form("shopee_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                name    = st.text_input("Customer Name")
                product = st.selectbox("Product", list(PRODUCTS.keys()))
                qty     = st.number_input("Qty", min_value=1, value=1)
            with col2:
                channel    = st.selectbox("Channel", CHANNELS)
                status     = st.selectbox("Status", STATUSES)
                order_date = st.date_input("Date", value=datetime.today())
            with col3:
                selling_price = st.number_input(
                    "Selling Price (RM)", min_value=0.0,
                    value=float(PRODUCTS.get(product if product in PRODUCTS else list(PRODUCTS.keys())[0], 30)),
                    step=0.50
                )
                profit = st.number_input("Net Profit (RM)", min_value=0.0, value=0.0, step=0.50,
                                         help="Take-home after fees, shipping, discounts")
                notes  = st.text_input("Notes / Order ID", placeholder="Shopee order ID etc.")

            total = selling_price * qty
            st.markdown(f"""
            <div class="qcard" style="padding:10px 14px;">
                <span style="font-size:12px;color:{C['TEXT2']};">Gross: </span><span style="font-weight:700;color:{C['TEXT']};">RM {total:.2f}</span>
                &nbsp;&nbsp;&nbsp;
                <span style="font-size:12px;color:{C['TEXT2']};">Net Profit: </span><span style="font-weight:700;color:{C['ACCENT']};">RM {profit:.2f}</span>
            </div>
            """, unsafe_allow_html=True)

            if st.form_submit_button("Save Order", use_container_width=True):
                orders = load("sales.json")
                orders.append({
                    "id":            f"ORD{len(orders)+1:04d}",
                    "name":          name.strip() or "—",
                    "product":       product,
                    "qty":           qty,
                    "selling_price": selling_price,
                    "total":         total,
                    "net":           profit,
                    "channel":       channel,
                    "status":        status,
                    "date":          str(order_date),
                    "notes":         notes.strip(),
                    "recorded_by":   st.session_state.get("current_user", "?"),
                })
                save("sales.json", orders)
                notify(
                    f"🛒 <b>New Order!</b>\n"
                    f"👤 {name.strip() or '—'}\n"
                    f"📦 {product} x{qty}\n"
                    f"💰 RM {total:.2f} gross\n"
                    f"📍 {channel}\n"
                    f"🕐 {now_myt().strftime('%d %b %Y %I:%M %p MYT')}"
                )
                st.success(f"Saved — RM {total:.2f} gross / RM {profit:.2f} net")

    # ── Tab 3: All Manual Orders ──────────────────────
    with tab3:
        orders = load("sales.json")
        if not orders:
            st.info("No manual orders yet.")
        else:
            f_status = st.selectbox("Filter status", ["All"] + STATUSES, key="fs3")
            filtered = sorted(
                [o for o in orders if f_status == "All" or o.get("status") == f_status],
                key=lambda x: x.get("date", ""), reverse=True
            )

            total_gross = sum(o.get("total", 0) for o in filtered if o.get("status") == "Completed")
            total_net   = sum(o.get("net",   0) for o in filtered if o.get("status") == "Completed")
            st.markdown(f"""
            <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:1rem;">
                <span class="badge badge-purple">{len(filtered)} orders</span>
                <span class="badge badge-green">RM {total_gross:,.2f} gross</span>
                <span class="badge badge-blue">RM {total_net:,.2f} net</span>
            </div>
            """, unsafe_allow_html=True)

            for o in filtered:
                bc = {"Completed": "badge-green", "Pending": "badge-yellow", "Cancelled": "badge-red"}.get(o.get("status", ""), "badge-purple")
                with st.expander(f"{o.get('id')}  ·  {o.get('name')}  ·  {o.get('product')}  ·  RM {o.get('total',0):.2f}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Product:** {o.get('product')} x{o.get('qty')}")
                        st.write(f"**Channel:** {o.get('channel')}")
                        st.write(f"**Date:** {o.get('date')}")
                    with c2:
                        st.write(f"**Gross:** RM {o.get('total', 0):.2f}")
                        st.write(f"**Net Profit:** RM {o.get('net', 0):.2f}")
                        st.write(f"**Recorded by:** {o.get('recorded_by', '?')}")
                    if o.get("notes"):
                        st.write(f"**Notes:** {o.get('notes')}")

                    st.markdown(f"<div style='height:1px;background:{C['BORDER']};margin:.75rem 0;'></div>", unsafe_allow_html=True)

                    col_upd, col_del = st.columns([2, 1])
                    with col_upd:
                        ns = st.selectbox("Update status", STATUSES,
                                          index=STATUSES.index(o.get("status", "Pending")),
                                          key=f"s3_{o['id']}")
                        if st.button("Update Status", key=f"b3_{o['id']}", use_container_width=True):
                            all_o = load("sales.json")
                            for order in all_o:
                                if order["id"] == o["id"]:
                                    order["status"] = ns
                            save("sales.json", all_o)
                            st.success("Updated!")
                            st.rerun()
                    with col_del:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("Delete Order", key=f"del3_{o['id']}", use_container_width=True):
                            all_o = load("sales.json")
                            all_o = [order for order in all_o if order["id"] != o["id"]]
                            save("sales.json", all_o)
                            st.success(f"Order {o['id']} deleted.")
                            st.rerun()

    # ── Tab 4: P&L Statement ──────────────────────────
    with tab4:
        now      = now_myt()
        all_sales = load("sales.json")
        cogs_map = get_cogs_map()

        if not cogs_map:
            st.warning("No costing data found. Set up product costing in Inventory & Costing first.")
        else:
            # Period selector
            col1, col2, col3 = st.columns(3)
            with col1:
                period = st.selectbox("Period", ["Monthly", "Yearly", "All Time"], key="pl_period")
            with col2:
                years_avail = sorted(set(
                    date.fromisoformat(o["date"]).year
                    for o in all_sales if o.get("date")
                ), reverse=True) or [now.year]
                year = st.selectbox("Year", years_avail, key="pl_year") if period != "All Time" else now.year
            with col3:
                month_names_short = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                if period == "Monthly":
                    month_idx = st.selectbox("Month", range(1, 13),
                                             format_func=lambda m: month_names_short[m-1],
                                             index=now.month - 1, key="pl_month")
                else:
                    month_idx = None

            month_names_long = ["January","February","March","April","May","June",
                                "July","August","September","October","November","December"]
            if period == "Monthly" and month_idx:
                period_label = f"{month_names_long[month_idx-1]} {year}"
            elif period == "Yearly":
                period_label = str(year)
            else:
                period_label = "All Time"

            filtered_sales = filter_sales(all_sales, period, year, month_idx)
            completed      = [o for o in filtered_sales if o.get("status") == "Completed"]

            # Compute P&L
            revenue    = sum(o.get("total", 0) for o in completed)
            total_cogs = 0
            cogs_rows  = []
            product_qty = {}
            for o in completed:
                p   = o.get("product", "Unknown")
                qty = o.get("qty", 1)
                product_qty[p] = product_qty.get(p, 0) + qty
            for product, qty in product_qty.items():
                uc        = cogs_map.get(product, 0)
                line      = uc * qty
                total_cogs += line
                cogs_rows.append({"Product": product, "Units Sold": qty, "COGS/Unit": uc, "Total COGS": line})

            gross_profit = revenue - total_cogs
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            # KPI cards
            col1, col2, col3, col4 = st.columns(4)
            for col, (label, val, fmt, good) in zip([col1, col2, col3, col4], [
                ("REVENUE",      revenue,      "RM", True),
                ("COGS",         total_cogs,   "RM", False),
                ("GROSS PROFIT", gross_profit, "RM", True),
                ("GROSS MARGIN", gross_margin, "%",  True),
            ]):
                val_str = f"RM {val:,.2f}" if fmt == "RM" else f"{val:.1f}%"
                vc      = val_color(val, good)
                with col:
                    st.markdown(f"""
                    <div class="qcard">
                        <div class="kpi-label">{label}</div>
                        <div style="font-size:22px;font-weight:800;color:{vc};letter-spacing:-.03em;line-height:1;">{val_str}</div>
                        <div class="kpi-sub">{len(completed)} orders · {period_label}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            col_l, col_r = st.columns([3, 2])

            with col_l:
                st.markdown(f"<div style='font-size:14px;font-weight:600;color:{C['TEXT']};margin-bottom:10px;'>P&L — {period_label}</div>", unsafe_allow_html=True)

                for label, val, good, is_total in [
                    ("Revenue",               revenue,      True,  False),
                    ("Cost of Goods Sold",    -total_cogs,  False, False),
                    ("Gross Profit",          gross_profit, True,  True),
                ]:
                    vc     = val_color(val, good)
                    prefix = "− " if val < 0 else ""
                    bg     = f"background:{C['ACCENT']}10;" if is_total else ""
                    bt     = f"border-top:2px solid {C['BORDER']};" if is_total else ""
                    fw     = "font-weight:700;" if is_total else "font-weight:400;"
                    fs     = "font-size:15px;" if is_total else "font-size:13px;"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;padding:10px 14px;{bg}{bt}border-radius:{'10px' if is_total else '6px'};margin-bottom:4px;">
                        <span style="color:{C['TEXT']};{fw}{fs}">{label}</span>
                        <span style="color:{vc};{fw}{fs}">{prefix}RM {abs(val):,.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)

                margin_color = "#4ade80" if gross_margin >= 40 else "#fbbf24" if gross_margin >= 20 else "#f87171"
                hint         = "Healthy margin" if gross_margin >= 40 else "Review pricing or COGS" if gross_margin >= 20 else "Low margin — check costing"
                st.markdown(f"""
                <div style="margin-top:1rem;">
                    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                        <span style="color:{C['TEXT2']};">Gross margin</span>
                        <span style="color:{margin_color};font-weight:600;">{gross_margin:.1f}%</span>
                    </div>
                    <div style="background:{C['BORDER']};border-radius:99px;height:10px;">
                        <div style="background:{margin_color};width:{min(gross_margin,100):.0f}%;height:10px;border-radius:99px;"></div>
                    </div>
                    <div style="font-size:11px;color:{C['TEXT3']};margin-top:4px;">{hint}</div>
                </div>
                """, unsafe_allow_html=True)

            with col_r:
                st.markdown(f"<div style='font-size:14px;font-weight:600;color:{C['TEXT']};margin-bottom:10px;'>COGS Breakdown</div>", unsafe_allow_html=True)
                if cogs_rows:
                    colors = ["#7c6fea","#4ade80","#f472b6","#60a5fa","#fbbf24","#a99eff"]
                    for i, row in enumerate(sorted(cogs_rows, key=lambda x: x["Total COGS"], reverse=True)):
                        pct   = row["Total COGS"] / max(total_cogs, 0.01)
                        color = colors[i % len(colors)]
                        st.markdown(f"""
                        <div class="qcard" style="padding:10px 14px;margin-bottom:6px;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                                <span style="font-size:13px;font-weight:500;color:{C['TEXT']};">{row['Product']}</span>
                                <span style="font-size:13px;font-weight:700;color:{color};">RM {row['Total COGS']:,.2f}</span>
                            </div>
                            <div style="background:{C['BORDER']};border-radius:99px;height:5px;margin-bottom:5px;">
                                <div style="background:{color};width:{pct*100:.0f}%;height:5px;border-radius:99px;"></div>
                            </div>
                            <div style="font-size:11px;color:{C['TEXT2']};">{row['Units Sold']} units · RM {row['COGS/Unit']:,.4f}/unit · {pct*100:.0f}% of COGS</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='qcard'><div style='color:{C['TEXT2']};font-size:13px;'>No completed sales in this period.</div></div>", unsafe_allow_html=True)

            # Monthly trend
            if period in ["Yearly", "All Time"] and completed:
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:14px;font-weight:600;color:{C['TEXT']};margin-bottom:10px;'>Monthly Trend</div>", unsafe_allow_html=True)

                monthly = {}
                for o in completed:
                    try:    mk = date.fromisoformat(o["date"]).strftime("%Y-%m")
                    except: continue
                    monthly.setdefault(mk, {"revenue": 0, "cogs": 0, "orders": 0})
                    monthly[mk]["revenue"] += o.get("total", 0)
                    monthly[mk]["cogs"]    += cogs_map.get(o.get("product",""), 0) * o.get("qty", 1)
                    monthly[mk]["orders"]  += 1

                if monthly:
                    df_trend = pd.DataFrame([
                        {"Month": mk, "Revenue": v["revenue"], "Gross Profit": v["revenue"] - v["cogs"]}
                        for mk, v in sorted(monthly.items())
                    ])
                    st.bar_chart(df_trend.set_index("Month"), height=240, color=["#7c6fea","#4ade80"])

            # Export
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                wb       = writer.book
                title_f  = wb.add_format({"bold":True,"font_size":13,"bg_color":"#534AB7","font_color":"white","border":1,"align":"center","font_name":"Calibri"})
                head_f   = wb.add_format({"bold":True,"bg_color":"#f0eeff","border":1,"font_name":"Calibri"})
                money_f  = wb.add_format({"num_format":"RM #,##0.00","border":1,"font_name":"Calibri"})
                pct_f    = wb.add_format({"num_format":"0.0%","border":1,"font_name":"Calibri"})
                norm_f   = wb.add_format({"border":1,"font_name":"Calibri"})
                green_f  = wb.add_format({"bold":True,"font_color":"#0d7a4e","border":1,"num_format":"RM #,##0.00","font_name":"Calibri"})
                red_f    = wb.add_format({"bold":True,"font_color":"#b91c1c","border":1,"num_format":"RM #,##0.00","font_name":"Calibri"})
                total_f  = wb.add_format({"bold":True,"bg_color":"#7c6fea","font_color":"white","border":1,"num_format":"RM #,##0.00","font_name":"Calibri"})

                ws = wb.add_worksheet("P&L Summary")
                ws.merge_range("B2:E2", f"QALY — P&L STATEMENT  |  {period_label}", title_f)
                ws.write("B4", "Generated", head_f)
                ws.write("C4", now_myt().strftime("%d %b %Y %I:%M %p MYT"), norm_f)
                for i, (lbl, val, fmt) in enumerate([
                    ("Revenue",           revenue,      green_f),
                    ("Cost of Goods Sold",total_cogs,   red_f),
                    ("Gross Profit",      gross_profit, total_f),
                ], start=6):
                    ws.write(i, 1, lbl, head_f)
                    ws.write(i, 2, val, fmt)
                ws.write(10, 1, "Gross Margin",     head_f)
                ws.write(10, 2, gross_margin / 100, pct_f)
                ws.write(11, 1, "Completed Orders", head_f)
                ws.write(11, 2, len(completed),     norm_f)
                ws.set_column("B:B", 26); ws.set_column("C:C", 18)

                if cogs_rows:
                    pd.DataFrame(cogs_rows).to_excel(writer, sheet_name="COGS Breakdown", index=False)
                    writer.sheets["COGS Breakdown"].set_column("A:A", 28)
                    writer.sheets["COGS Breakdown"].set_column("B:D", 16)

            col_dl, col_hint = st.columns([1, 2])
            with col_dl:
                st.download_button(
                    "Download Excel",
                    data=output.getvalue(),
                    file_name=f"Qaly_PL_{period_label.replace(' ','_')}.xlsx",
                    use_container_width=True
                )
            with col_hint:
                st.markdown(f"<div style='font-size:12px;color:{C['TEXT2']};padding-top:10px;'>2 sheets: P&L Summary + COGS Breakdown</div>", unsafe_allow_html=True)
