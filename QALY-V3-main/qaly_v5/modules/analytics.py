import streamlit as st
import pandas as pd
from modules.utils import load, get_theme_colors

def show():
    C = get_theme_colors()
    st.markdown(f"<div class='page-title'>Analytics</div><div class='page-sub'>Revenue, product performance, channel breakdown</div>", unsafe_allow_html=True)

    sales = load("sales.json")
    completed = [o for o in sales if o.get("status") == "Completed"]

    if not completed:
        st.info("No completed orders yet.")
        return

    df = pd.DataFrame(completed)
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["net_val"] = df.apply(lambda r: r.get("net", r.get("total", 0)), axis=1)

    total_rev = df["total"].sum()
    total_net = df["net_val"].sum()
    total_qty = df.get("qty", pd.Series([1]*len(df))).sum()

    # KPIs
    col1,col2,col3,col4 = st.columns(4)
    best_product = df.groupby("product")["total"].sum().idxmax() if "product" in df.columns else "—"
    best_channel = df.groupby("channel")["total"].sum().idxmax() if "channel" in df.columns else "—"
    for col, (label, val) in zip([col1,col2,col3,col4],[
        ("GROSS REVENUE",   f"RM {total_rev:,.2f}"),
        ("NET REVENUE",     f"RM {total_net:,.2f}"),
        ("UNITS SOLD",      str(int(total_qty))),
        ("TOP PRODUCT",     best_product.split(" ")[0] if best_product != "—" else "—"),
    ]):
        with col:
            st.markdown(f"""
            <div class="qcard">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="font-size:22px;">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"<div class='divider'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Revenue Trend", "Product Performance", "Channel Analysis"])

    with tab1:
        period = st.radio("Group by", ["Monthly", "Weekly"], horizontal=True)
        df["week"] = df["date"].dt.to_period("W").astype(str)
        group_col = "month" if period == "Monthly" else "week"
        trend = df.groupby(group_col).agg(Gross=("total","sum"), Net=("net_val","sum")).reset_index()
        trend.columns = ["Period","Gross","Net"]
        st.bar_chart(trend.set_index("Period")[["Gross","Net"]], height=300)
        trend_display = trend.copy()
        trend_display["Gross"] = trend_display["Gross"].apply(lambda x: f"RM {x:,.2f}")
        trend_display["Net"]   = trend_display["Net"].apply(lambda x: f"RM {x:,.2f}")
        st.dataframe(trend_display, use_container_width=True, hide_index=True)

    with tab2:
        if "product" not in df.columns:
            st.info("No product data.")
            return
        prod = df.groupby("product").agg(Gross=("total","sum"), Net=("net_val","sum"), Orders=("id","count")).reset_index()
        prod = prod.sort_values("Gross", ascending=False)
        prod["Share"] = (prod["Gross"] / prod["Gross"].sum() * 100).round(1)

        for _, row in prod.iterrows():
            pct = row["Gross"] / prod["Gross"].sum()
            colors = ["#7c6fea","#a99eff","#4ade80","#60a5fa","#f472b6"]
            color = colors[int(row.name) % len(colors)]
            st.markdown(f"""
            <div class="qcard" style="padding:12px 16px;margin-bottom:8px;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div style="font-size:14px;font-weight:600;color:{C['TEXT']};">{row['product']}</div>
                    <div style="font-size:13px;color:{C['ACCENT']};font-weight:600;">RM {row['Gross']:,.2f} &nbsp;<span style="color:{C['TEXT3']};font-weight:400;font-size:12px;">({row['Share']}%)</span></div>
                </div>
                <div style="background:{C['BORDER']};border-radius:99px;height:6px;">
                    <div style="background:{color};width:{pct*100:.0f}%;height:6px;border-radius:99px;"></div>
                </div>
                <div style="font-size:11px;color:{C['TEXT2']};margin-top:6px;">{row['Orders']} orders &nbsp;·&nbsp; Net RM {row['Net']:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        if "channel" not in df.columns:
            st.info("No channel data.")
            return
        ch = df.groupby("channel").agg(Gross=("total","sum"), Orders=("id","count")).reset_index()
        ch = ch.sort_values("Gross", ascending=False)

        colors = ["#7c6fea","#4ade80","#60a5fa","#f472b6","#fbbf24","#a99eff"]
        for i, (_, row) in enumerate(ch.iterrows()):
            pct = row["Gross"] / ch["Gross"].sum()
            color = colors[i % len(colors)]
            st.markdown(f"""
            <div style="margin-bottom:14px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                    <span style="color:{C['TEXT']};font-weight:500;">{row['channel']}</span>
                    <span style="color:{C['TEXT2']};">RM {row['Gross']:,.2f} &nbsp;·&nbsp; {row['Orders']} orders &nbsp;·&nbsp; {pct*100:.0f}%</span>
                </div>
                <div style="background:{C['BORDER']};border-radius:99px;height:8px;">
                    <div style="background:{color};width:{pct*100:.0f}%;height:8px;border-radius:99px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
