import streamlit as st
from datetime import date
from modules.utils import load, get_theme_colors, USER_COLORS, MEMBERS, now_myt


def show():
    C   = get_theme_colors()
    now = now_myt()  # Malaysia Time

    st.markdown(f"""
    <div style="margin-bottom:2rem;">
        <div style="font-size:12px;font-weight:500;color:{C['TEXT3']};letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px;">{now.strftime('%A').upper()}</div>
        <div style="font-size:46px;font-weight:800;color:{C['TEXT']};letter-spacing:-.04em;line-height:1;">{now.strftime('%d %B %Y')}</div>
        <div style="font-size:13px;color:{C['TEXT2']};margin-top:6px;">{now.strftime('%I:%M %p')} MYT &nbsp;·&nbsp; Kimya Centre-v2</div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs ─────────────────────────────────────────
    sales     = load("sales.json")
    completed = [o for o in sales if o.get("status") == "Completed"]
    pending   = [o for o in sales if o.get("status") == "Pending"]
    total_rev = sum(o.get("total", 0) for o in completed)
    this_month = now.strftime("%Y-%m")
    month_c   = [o for o in completed if o.get("date", "").startswith(this_month)]
    month_rev = sum(o.get("total", 0) for o in month_c)

    col1, col2, col3, col4 = st.columns(4)
    for col, (label, val, sub) in zip([col1, col2, col3, col4], [
        ("TOTAL REVENUE",   f"RM {total_rev:,.2f}",                          f"{len(completed)} completed orders"),
        ("THIS MONTH",      f"RM {month_rev:,.2f}",                          f"{len(month_c)} orders in {now.strftime('%B')}"),
        ("TOTAL ORDERS",    str(len(sales)),                                  f"{len(pending)} pending"),
        ("AVG ORDER VALUE", f"RM {total_rev / max(len(completed), 1):,.2f}", "per completed order"),
    ]):
        with col:
            st.markdown(f'<div class="qcard"><div class="kpi-label">{label}</div><div class="kpi-value">{val}</div><div class="kpi-sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2])

    # ── LEFT ─────────────────────────────────────────
    with col_l:
        # Recent orders
        st.markdown(f"<div style='font-size:15px;font-weight:600;color:{C['TEXT']};margin-bottom:12px;'>Recent Orders</div>", unsafe_allow_html=True)
        recent = sorted(sales, key=lambda x: x.get("date", ""), reverse=True)[:5]
        if recent:
            for o in recent:
                bc = {"Completed": "badge-green", "Pending": "badge-yellow", "Cancelled": "badge-red"}.get(o.get("status", ""), "badge-purple")
                st.markdown(f"""
                <div class="qcard" style="padding:10px 14px;display:flex;align-items:center;justify-content:space-between;">
                    <div>
                        <div style="font-size:13px;font-weight:600;color:{C['TEXT']};">{o.get('name', '?')}</div>
                        <div style="font-size:11px;color:{C['TEXT2']};margin-top:2px;">{o.get('product', '?')} &nbsp;·&nbsp; {o.get('channel', '?')} &nbsp;·&nbsp; {o.get('date', '?')}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:14px;font-weight:700;color:{C['ACCENT']};">RM {o.get('total', 0):.2f}</div>
                        <span class="badge {bc}" style="margin-top:3px;display:inline-block;">{o.get('status', '?')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='qcard'><div style='color:{C['TEXT2']};font-size:13px;'>No orders yet.</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Production summary
        st.markdown(f"<div style='font-size:15px;font-weight:600;color:{C['TEXT']};margin-bottom:12px;'>Production Summary</div>", unsafe_allow_html=True)
        batches = load("production.json")
        active_batches = [b for b in batches if b.get("status") == "Active"]

        if batches:
            # Aggregate bottled stock across all active batches
            bottled_totals = {}
            base_totals    = {}
            for b in active_batches:
                # Remaining unallocated base
                rem_base_ml = b.get("remaining_base_ml", 0)
                base_totals[b.get("batch_no","?")] = rem_base_ml

                products_list = b.get("products", [])
                for p in products_list:
                    pname = p.get("product", "?")
                    bottled = p.get("remaining", p.get("units", 0))
                    bottled_totals[pname] = bottled_totals.get(pname, 0) + bottled

            # Show bottled stock per product
            if bottled_totals:
                st.markdown(f"<div style='font-size:12px;color:{C['TEXT2']};margin-bottom:8px;'>Bottled stock (ready to sell)</div>", unsafe_allow_html=True)
                for pname, qty in sorted(bottled_totals.items()):
                    color = "#4ade80" if qty > 5 else "#fbbf24" if qty > 0 else "#f87171"
                    st.markdown(f"""
                    <div class="qcard" style="padding:8px 14px;display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <span style="font-size:13px;color:{C['TEXT']};font-weight:500;">{pname}</span>
                        <span style="font-size:14px;font-weight:700;color:{color};">{qty} units</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Show unallocated base
            total_unallocated = sum(base_totals.values())
            if total_unallocated > 0:
                st.markdown(f"""
                <div class="qcard" style="padding:10px 14px;border:1px solid {C['ACCENT']}30;background:{C['ACCENT']}08;margin-top:8px;">
                    <div style="font-size:12px;color:{C['TEXT2']};margin-bottom:2px;">Unallocated base (stored)</div>
                    <div style="font-size:16px;font-weight:700;color:{C['ACCENT']};">{total_unallocated:.0f} ml</div>
                    <div style="font-size:11px;color:{C['TEXT3']};margin-top:2px;">Across {len([v for v in base_totals.values() if v>0])} active batch(es) — ready to bottle on demand</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:12px;color:{C['TEXT2']};margin-bottom:8px;'>Latest batches</div>", unsafe_allow_html=True)
            latest = sorted(batches, key=lambda x: x.get("date", ""), reverse=True)[:3]
            for b in latest:
                bc = "badge-green" if b.get("status") == "Active" else "badge-purple" if b.get("status") == "Completed" else "badge-yellow"
                products_list = b.get("products", [])
                if products_list:
                    prod_label  = ", ".join(p["product"].split(" ")[0] for p in products_list)
                    stock_label = " · ".join(f"{p.get('remaining', p.get('units',0))} {p['product'].split(' ')[0]}" for p in products_list)
                else:
                    prod_label  = b.get("product", "?")
                    stock_label = f"{b.get('units_remaining', b.get('units_produced', 0))} units"
                rem_base = b.get("remaining_base_ml", 0)
                base_info = f" · {rem_base:.0f}ml base stored" if rem_base > 0 else ""
                st.markdown(f"""
                <div class="qcard" style="padding:10px 14px;display:flex;align-items:center;justify-content:space-between;">
                    <div>
                        <div style="font-size:13px;font-weight:600;color:{C['TEXT']};">Batch {b.get('batch_no','?')} &nbsp;·&nbsp; {prod_label}</div>
                        <div style="font-size:11px;color:{C['TEXT2']};margin-top:2px;">{b.get('volume_L',0)}L &nbsp;·&nbsp; {stock_label}{base_info} &nbsp;·&nbsp; {b.get('date','?')}</div>
                    </div>
                    <span class="badge {bc}">{b.get('status','?')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='qcard'><div style='color:{C['TEXT2']};font-size:13px;'>No production records yet.</div></div>", unsafe_allow_html=True)

    # ── RIGHT ─────────────────────────────────────────
    with col_r:
        # Upcoming events
        st.markdown(f"<div style='font-size:15px;font-weight:600;color:{C['TEXT']};margin-bottom:12px;'>Upcoming Events</div>", unsafe_allow_html=True)
        events   = load("events.json")
        today    = date.today()
        upcoming = sorted([e for e in events if e.get("date", "") >= str(today)], key=lambda x: x.get("date", ""))[:4]
        if upcoming:
            for e in upcoming:
                edate     = e.get("date", "")
                days_left = (date.fromisoformat(edate) - today).days
                urgency   = "badge-red" if days_left <= 3 else "badge-yellow" if days_left <= 7 else "badge-blue"
                dlabel    = "Today" if days_left == 0 else f"In {days_left}d"
                st.markdown(f"""
                <div class="qcard" style="padding:10px 14px;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div>
                            <div style="font-size:13px;font-weight:600;color:{C['TEXT']};">{e.get('title','?')}</div>
                            <div style="font-size:11px;color:{C['TEXT2']};margin-top:2px;">{edate} &nbsp;·&nbsp; {e.get('location','')}</div>
                        </div>
                        <span class="badge {urgency}">{dlabel}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='qcard'><div style='color:{C['TEXT2']};font-size:13px;'>No upcoming events.</div></div>", unsafe_allow_html=True)

        # Alert cards
        if pending:
            st.markdown(f"""
            <div class="qcard" style="border:1px solid {C['WARN_T']}40;background:{C['WARN_BG']};">
                <div style="font-size:13px;font-weight:600;color:{C['WARN_T']};">{len(pending)} Pending Order{'s' if len(pending)>1 else ''}</div>
                <div style="font-size:12px;color:{C['TEXT2']};margin-top:3px;">Update in Sales Tracker.</div>
            </div>
            """, unsafe_allow_html=True)

        if active_batches:
            st.markdown(f"""
            <div class="qcard" style="border:1px solid {C['SUCCESS_T']}40;background:{C['SUCCESS']};">
                <div style="font-size:13px;font-weight:600;color:{C['SUCCESS_T']};">{len(active_batches)} Active Batch{'es' if len(active_batches)>1 else ''}</div>
                <div style="font-size:12px;color:{C['TEXT2']};margin-top:3px;">In progress — check Production page.</div>
            </div>
            """, unsafe_allow_html=True)

        # Reorder alerts
        inventory = load("inventory.json")
        low_stock = [i for i in inventory if i.get("stock", 0) <= i.get("reorder", 0) and i.get("reorder", 0) > 0]
        if low_stock:
            items_str = ", ".join(i.get("name", "?") for i in low_stock[:3])
            more      = f" +{len(low_stock)-3} more" if len(low_stock) > 3 else ""
            st.markdown(f"""
            <div class="qcard" style="border:1px solid {C['ERR_T']}40;background:{C['ERR_BG']};">
                <div style="font-size:13px;font-weight:600;color:{C['ERR_T']};">{len(low_stock)} Low Stock Alert{'s' if len(low_stock)>1 else ''}</div>
                <div style="font-size:12px;color:{C['TEXT2']};margin-top:3px;">{items_str}{more} — check Inventory.</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # ── Activity log ──────────────────────────────────
    st.markdown(f"<div style='font-size:15px;font-weight:600;color:{C['TEXT']};margin-bottom:12px;'>System Activity</div>", unsafe_allow_html=True)
    visits = load("visits.json")
    col_act, col_stats = st.columns([3, 2])

    with col_act:
        st.markdown(f"<div style='font-size:12px;color:{C['TEXT2']};margin-bottom:8px;'>Recent logins</div>", unsafe_allow_html=True)
        recent_v = sorted(visits, key=lambda x: x.get("timestamp", ""), reverse=True)[:8]
        if recent_v:
            from datetime import datetime
            for v in recent_v:
                try:
                    from datetime import timezone, timedelta
                    dt  = datetime.fromisoformat(v["timestamp"])
                    # If no tzinfo, assume already MYT (legacy records)
                    ts  = dt.strftime("%d %b %Y &nbsp;·&nbsp; %I:%M %p")
                except:
                    ts = v.get("timestamp", "")
                uc       = USER_COLORS.get(v.get("user", ""), C["ACCENT"])
                initials = "".join([w[0].upper() for w in v.get("user", "?").split()])
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid {C['BORDER']};">
                    <div style="width:30px;height:30px;border-radius:8px;background:{uc}22;color:{uc};font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">{initials}</div>
                    <div>
                        <div style="font-size:13px;font-weight:500;color:{C['TEXT']};">{v.get('user','?')}</div>
                        <div style="font-size:11px;color:{C['TEXT2']};">{ts}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='color:{C['TEXT2']};font-size:13px;'>No activity yet.</div>", unsafe_allow_html=True)

    with col_stats:
        st.markdown(f"<div style='font-size:12px;color:{C['TEXT2']};margin-bottom:8px;'>Login count (all time)</div>", unsafe_allow_html=True)
        total_v = max(len(visits), 1)
        for member in MEMBERS:
            count = sum(1 for v in visits if v.get("user") == member)
            pct   = count / total_v
            uc    = USER_COLORS.get(member, C["ACCENT"])
            st.markdown(f"""
            <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                    <span style="color:{C['TEXT']};font-weight:500;">{member}</span>
                    <span style="color:{C['TEXT2']};">{count}</span>
                </div>
                <div style="background:{C['BORDER']};border-radius:99px;height:6px;">
                    <div style="background:{uc};width:{pct*100:.0f}%;height:6px;border-radius:99px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
