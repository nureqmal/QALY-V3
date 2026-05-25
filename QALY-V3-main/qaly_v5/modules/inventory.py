import streamlit as st
import pandas as pd
from modules.utils import load, save, save_dict, load_dict, get_theme_colors, send_telegram
def show():
    C = get_theme_colors()
    st.markdown(f"<div class='page-title'>Inventory & Costing</div><div class='page-sub'>Raw materials, stock levels, product cost breakdown</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Inventory", "Product Costing", "Reorder Alerts"])
    # ── Tab 1: Inventory ──────────────────────────────
    with tab1:
        inventory = load("inventory.json")
        with st.expander("Add / Update Raw Material"):
            with st.form("inv_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    mat_name   = st.text_input("Material Name *", placeholder="e.g. Magnesium Chloride")
                    supplier   = st.text_input("Supplier", placeholder="e.g. Sigma-Aldrich")
                with col2:
                    unit        = st.selectbox("Unit", ["g","kg","ml","L","pcs","bottle","pack"])
                    stock_qty   = st.number_input("Current Stock", min_value=0.0, step=0.1)
                    reorder_pt  = st.number_input("Reorder Point", min_value=0.0, step=0.1, help="Alert when stock drops below this")
                with col3:
                    unit_cost   = st.number_input("Unit Cost (RM)", min_value=0.0, step=0.01)
                    last_bought = st.date_input("Last Purchased")
                    notes       = st.text_input("Notes")
                if st.form_submit_button("Save Material", use_container_width=True):
                    if mat_name.strip():
                        # Update if exists, else add
                        found = False
                        for item in inventory:
                            if item.get("name","").lower() == mat_name.strip().lower():
                                item.update({
                                    "supplier": supplier, "unit": unit,
                                    "stock": stock_qty, "reorder": reorder_pt,
                                    "unit_cost": unit_cost, "last_bought": str(last_bought),
                                    "notes": notes,
                                })
                                found = True
                                break
                        if not found:
                            inventory.append({
                                "id": f"MAT{len(inventory)+1:03d}",
                                "name": mat_name.strip(),
                                "supplier": supplier,
                                "unit": unit,
                                "stock": stock_qty,
                                "reorder": reorder_pt,
                                "unit_cost": unit_cost,
                                "last_bought": str(last_bought),
                                "notes": notes,
                            })
                        save("inventory.json", inventory)
                        # Check if newly added/updated item is low stock
                        if stock_qty <= reorder_pt and reorder_pt > 0:
                            send_telegram(
                                f"⚠️ <b>Low Stock Alert!</b>\n"
                                f"📦 {mat_name.strip()}\n"
                                f"📉 Stock: {stock_qty} {unit} (min {reorder_pt})\n"
                                f"🏭 Supplier: {supplier or '—'}"
                            )
                        st.success("Saved!")
                        st.rerun()
                    else:
                        st.error("Material name required.")
        # Display inventory table
        if inventory:
            rows = []
            for item in inventory:
                stock = item.get("stock", 0)
                reorder = item.get("reorder", 0)
                status = "Low" if stock <= reorder and reorder > 0 else "OK"
                value = stock * item.get("unit_cost", 0)
                rows.append({
                    "Material":    item.get("name"),
                    "Stock":       f"{stock} {item.get('unit','')}",
                    "Reorder At":  f"{reorder} {item.get('unit','')}",
                    "Unit Cost":   f"RM {item.get('unit_cost',0):.4f}",
                    "Total Value": f"RM {value:.2f}",
                    "Supplier":    item.get("supplier","—"),
                    "Notes":       item.get("notes","—"),
                    "Status":      status,
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
            total_value = sum(i.get("stock",0) * i.get("unit_cost",0) for i in inventory)
            st.markdown(f"""
            <div class="qcard qcard-accent" style="padding:10px 16px;margin-top:0.75rem;">
                <span style="font-size:13px;color:{C['TEXT2']};">Total inventory value: </span>
                <span style="font-size:16px;font-weight:700;color:{C['ACCENT']};">RM {total_value:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
            # Delete material
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:13px;font-weight:500;color:{C['TEXT']};margin-bottom:8px;'>Delete material</div>", unsafe_allow_html=True)
            mat_names = [i.get("name") for i in inventory]
            col_del1, col_del2 = st.columns([3,1])
            with col_del1:
                to_delete = st.selectbox("Select material to delete", mat_names, key="del_mat")
            with col_del2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Delete", key="del_mat_btn", use_container_width=True):
                    updated = [i for i in inventory if i.get("name") != to_delete]
                    save("inventory.json", updated)
                    st.success(f"{to_delete} deleted.")
                    st.rerun()
        else:
            # Prefill with known Qaly ingredients
            st.info("No inventory yet. Add your raw materials above.")
            if st.button("Load Qaly default ingredients"):
                defaults = [
                    {"id":"MAT001","name":"Magnesium Chloride","supplier":"","unit":"g","stock":1000,"reorder":200,"unit_cost":0.02,"last_bought":"","notes":"Antibacterial active"},
                    {"id":"MAT002","name":"Aloe Vera Extract","supplier":"","unit":"ml","stock":500,"reorder":100,"unit_cost":0.05,"last_bought":"","notes":"Skin soothing"},
                    {"id":"MAT003","name":"Dipropylene Glycol","supplier":"","unit":"ml","stock":500,"reorder":100,"unit_cost":0.03,"last_bought":"","notes":"Carrier"},
                    {"id":"MAT004","name":"Potassium Sorbate","supplier":"","unit":"g","stock":200,"reorder":50,"unit_cost":0.08,"last_bought":"","notes":"Preservative"},
                    {"id":"MAT005","name":"Distilled Water","supplier":"","unit":"ml","stock":5000,"reorder":1000,"unit_cost":0.001,"last_bought":"","notes":"Base"},
                    {"id":"MAT006","name":"Bottle 100ml","supplier":"","unit":"pcs","stock":200,"reorder":50,"unit_cost":1.20,"last_bought":"","notes":"Packaging"},
                    {"id":"MAT007","name":"Label / Sticker","supplier":"","unit":"pcs","stock":200,"reorder":50,"unit_cost":0.30,"last_bought":"","notes":"Packaging"},
                ]
                save("inventory.json", defaults)
                st.success("Default ingredients loaded!")
                st.rerun()
    # ── Tab 2: Product Costing ────────────────────────
    with tab2:
        costing = load("costing.json")
        inventory = load("inventory.json")
        inv_names = [i.get("name") for i in inventory]
        products = ["Qaly 100ml", "Syed 100ml", "Syeda 100ml", "Kimya 100ml", "Couple Set (Syed + Syeda)"]
        selected_product = st.selectbox("Select product to cost", products)
        # Load existing recipe for this product
        recipe = next((c for c in costing if c.get("product") == selected_product), None)
        existing_ingredients = recipe.get("ingredients", []) if recipe else []
        st.markdown(f"<div style='font-size:13px;font-weight:500;color:{C['TEXT']};margin:1rem 0 0.5rem;'>Recipe / Bill of Materials</div>", unsafe_allow_html=True)
        # Ingredient entry
        with st.form(f"costing_{selected_product}", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                if inv_names:
                    ing_name = st.selectbox("Material", inv_names + ["Other (type below)"])
                    ing_name_custom = st.text_input("Custom material (if not in inventory)", label_visibility="visible")
                else:
                    ing_name = "—"
                    ing_name_custom = st.text_input("Material name")
            with col2:
                ing_qty  = st.number_input("Qty used per unit", min_value=0.0, step=0.01)
                ing_unit = st.selectbox("Unit", ["g","ml","pcs","drop"])
            with col3:
                ing_cost = st.number_input("Cost per unit (RM)", min_value=0.0, step=0.0001, format="%.4f")
            if st.form_submit_button("Add Ingredient to Recipe"):
                name_to_use = ing_name_custom if ing_name_custom else ing_name
                if name_to_use and ing_qty > 0:
                    new_ing = {"name": name_to_use, "qty": ing_qty, "unit": ing_unit, "cost_per_unit": ing_cost, "line_cost": round(ing_qty * ing_cost, 4)}
                    existing_ingredients.append(new_ing)
                    # Update or create recipe
                    found = False
                    for c in costing:
                        if c.get("product") == selected_product:
                            c["ingredients"] = existing_ingredients
                            found = True
                    if not found:
                        costing.append({"product": selected_product, "ingredients": existing_ingredients, "overhead": 0, "selling_price": 0})
                    save("costing.json", costing)
                    st.success("Ingredient added!")
                    st.rerun()
        # Show current recipe
        costing = load("costing.json")
        recipe = next((c for c in costing if c.get("product") == selected_product), None)
        if recipe and recipe.get("ingredients"):
            ings = recipe["ingredients"]
            total_mat_cost = sum(i.get("line_cost", 0) for i in ings)
            rows = [{"Material": i["name"], "Qty": f"{i['qty']} {i['unit']}", "Cost/Unit (RM)": f"{i['cost_per_unit']:.4f}", "Line Cost (RM)": f"{i['line_cost']:.4f}"} for i in ings]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            col1, col2 = st.columns(2)
            with col1:
                overhead = st.number_input("Overhead per unit (RM)", min_value=0.0, value=float(recipe.get("overhead",0)), step=0.01, help="Labour, utilities, packaging not in ingredients")
                selling  = st.number_input("Selling price (RM)",     min_value=0.0, value=float(recipe.get("selling_price",0)), step=0.50)
            if st.button("Update Costing", use_container_width=True):
                for c in costing:
                    if c.get("product") == selected_product:
                        c["overhead"] = overhead
                        c["selling_price"] = selling
                save("costing.json", costing)
                st.success("Updated!")
                st.rerun()
            total_cost = total_mat_cost + (recipe.get("overhead",0))
            sp = recipe.get("selling_price",0)
            margin = ((sp - total_cost) / sp * 100) if sp > 0 else 0
            with col2:
                st.markdown(f"""
                <div class="qcard qcard-accent" style="padding:12px 16px;margin-top:0.5rem;">
                    <div style="font-size:12px;color:{C['TEXT2']};margin-bottom:8px;">Cost Summary — {selected_product}</div>
                    <div style="font-size:13px;color:{C['TEXT']};line-height:2;">
                        Material cost: <b>RM {total_mat_cost:.4f}</b><br>
                        Overhead: <b>RM {recipe.get('overhead',0):.2f}</b><br>
                        Total COGS: <b>RM {total_cost:.4f}</b><br>
                        Selling price: <b>RM {sp:.2f}</b><br>
                        Gross margin: <b style="color:{C['ACCENT']};">{margin:.1f}%</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            if st.button("Remove all ingredients for this product", type="secondary"):
                for c in costing:
                    if c.get("product") == selected_product:
                        c["ingredients"] = []
                save("costing.json", costing)
                st.rerun()
        else:
            st.info("No recipe yet for this product. Add ingredients above.")
    # ── Tab 3: Reorder Alerts ─────────────────────────
    with tab3:
        inventory = load("inventory.json")
        low = [i for i in inventory if i.get("stock",0) <= i.get("reorder",0) and i.get("reorder",0) > 0]
        ok  = [i for i in inventory if i.get("stock",0) >  i.get("reorder",0) or i.get("reorder",0) == 0]
        if low:
            st.markdown(f"""
            <div class="qcard" style="border:1px solid #f8717140;background:#3a101020;margin-bottom:1rem;">
                <div style="font-size:14px;font-weight:600;color:
#f87171;margin-bottom:8px;">{len(low)} material{'s' if len(low)>1 else ''} need restocking</div>
            """, unsafe_allow_html=True)
            for i in low:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {C['BORDER']};font-size:13px;">
                    <span style="color:{C['TEXT']};font-weight:500;">{i['name']}</span>
                    <span style="color:
#f87171;">Stock: {i['stock']} {i['unit']} &nbsp;(min {i['reorder']})</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.success("All materials are above reorder levels.")
        if ok:
            with st.expander(f"OK materials ({len(ok)})"):
                for i in ok:
                    st.markdown(f"- **{i['name']}** — {i['stock']} {i['unit']} remaining")
