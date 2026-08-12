
import sqlite3
from datetime import date, timedelta

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from database import get_db_connection
import core_ops
import audit_engine
import Financial_Ledger
import financial_ops
import Inventory_yield
import shift_scheduler

# ============================================================
# CanteenOS — Operations Console
# ============================================================

st.set_page_config(
    page_title="CanteenOS",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Theme & Custom CSS (SaaS Look)
# -----------------------------
st.markdown(
    """
    <style>
    /* Hide Streamlit Header and Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Widen the main container and remove top padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 98%;
    }
    
    /* Clean Tab Bar */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; border-radius: 6px; }

    /* Base styling for custom HTML cards */
    .custom-card-green {
        background: linear-gradient(135deg, #1A4D2E 0%, #11331F 100%);
        border-radius: 16px;
        padding: 20px;
        color: white;
        box-shadow: 0 10px 15px -3px rgba(26, 77, 46, 0.3);
        font-family: sans-serif;
        margin-bottom: 15px;
    }
    .custom-card-white {
        background-color: white;
        border-radius: 16px;
        padding: 20px;
        color: #333;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #f0f0f0;
        font-family: sans-serif;
        margin-bottom: 15px;
    }
    .card-title { font-size: 14px; font-weight: 500; opacity: 0.9; margin-bottom: 8px;}
    .card-value { font-size: 28px; font-weight: 700; margin: 0;}
    .card-trend { font-size: 12px; margin-top: 10px; color: #a3e635;}
    .card-trend-dark { font-size: 12px; margin-top: 10px; color: #666;}
    </style>
    """,
    unsafe_allow_html=True,
)

def money(value):
    return f"₦{float(value or 0):,.2f}"

def db_query(sql, params=(), one=False):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows

def safe_call(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        st.success("Operation completed successfully.")
        return True
    except Exception as exc:
        st.error(str(exc))
        return False

def render_clean_table(df, hide_cols=None):
    if hide_cols:
        df = df.drop(columns=[c for c in hide_cols if c in df.columns])
    st.dataframe(df, use_container_width=True, hide_index=True)

def branches():
    return db_query("SELECT branch_id, branch_name, COALESCE(location, '') FROM Branches ORDER BY branch_name")

def active_menu():
    return core_ops.get_active_menu_items()

def branch_label(row):
    return f"{row[1]} — {row[2]}" if row[2] else row[1]

# -----------------------------
# Startup / database state
# -----------------------------
try:
    branch_rows = branches()
except Exception as exc:
    st.error(f"Database connection failed: {exc}")
    st.stop()

if not branch_rows:
    st.warning("CanteenOS is connected, but there are no branches yet. Open **Administration → Branches** and create the first branch.")

# ============================================================
# Sidebar Redesign
# ============================================================
st.sidebar.title("🍽️ CanteenOS")
st.sidebar.caption("Micro-ERP Operations Console")
st.sidebar.divider()

branch_options = {branch_label(b): b[0] for b in branch_rows}
if branch_options:
    selected_branch_label = st.sidebar.selectbox("Operating branch", list(branch_options.keys()))
    selected_branch = branch_options[selected_branch_label]
else:
    selected_branch = None

selected_date = st.sidebar.date_input("Business date", value=date.today())

st.sidebar.divider()
module = st.sidebar.radio(
    "Navigation",
    [
        "Command Center",
        "Evening Audit",
        "Production & Procurement",
        "Finance & Credits",
        "HR & Scheduling",
        "Administration",
    ],
)

st.sidebar.divider()
with st.sidebar.expander("System Info & Disclaimers"):
    st.markdown("**Version:** 1.0.0")
    st.markdown("**Developer:** [Phantom-E11](https://github.com/Phantom-E11)")
    st.caption("Designed for internal use within the canteen management team. Please ensure proper permissions before executing audit writes. Developers are not responsible for any data loss.")
    st.checkbox("I acknowledge", key="disclaimer_acknowledged")

# ============================================================
# Command Center (Upgraded UI)
# ============================================================
if module == "Command Center":
    st.title("Dashboard")
    st.caption("Plan, prioritize, and track branch operations with ease.")

    if selected_branch is None:
        st.info("Create a branch first.")
        st.stop()

    metrics = db_query(
        "SELECT COALESCE(SUM(cash_in_hand),0), COALESCE(SUM(bank_transfers),0), COALESCE(SUM(calculated_gross_revenue),0), COALESCE(SUM(calculated_net_profit),0) FROM Daily_Audits WHERE branch_id = ? AND audit_date = ?",
        (selected_branch, selected_date.isoformat()), one=True,
    )
    cash, transfers, gross, net = metrics or (0, 0, 0, 0)

    debt = db_query(
        "SELECT COALESCE(SUM(CASE WHEN transaction_type='DEBT' THEN amount ELSE 0 END),0), COALESCE(SUM(CASE WHEN transaction_type='REPAYMENT' THEN amount ELSE 0 END),0) FROM Credit_Ledger WHERE branch_id=? AND DATE(transaction_date)=?",
        (selected_branch, selected_date.isoformat()), one=True,
    ) or (0, 0)

    ticket = db_query(
        "SELECT COALESCE(SUM(tickets_count),0), COALESCE(SUM(total_value),0) FROM Ticket_Logs WHERE branch_id=? AND log_date=?",
        (selected_branch, selected_date.isoformat()), one=True,
    ) or (0, 0)

    procurement = db_query("SELECT COALESCE(SUM(total_cost),0) FROM Procurement_Log WHERE branch_id=? AND purchase_date=?", (selected_branch, selected_date.isoformat()), one=True)
    procurement = procurement[0] if procurement else 0

    # Custom HTML Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
            <div class="custom-card-green">
                <div class="card-title">Gross Revenue</div>
                <div class="card-value">{money(gross)}</div>
                <div class="card-trend">↗ Cash + Transfers: {money(cash + transfers)}</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="custom-card-white">
                <div class="card-title">Net Profit</div>
                <div class="card-value">{money(net)}</div>
                <div class="card-trend-dark">After OpEx & Wages</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
            <div class="custom-card-white">
                <div class="card-title">Procurement Spend</div>
                <div class="card-value">{money(procurement)}</div>
                <div class="card-trend-dark">Daily Raw Material Cost</div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
            <div class="custom-card-white">
                <div class="card-title">New Credit/Debt</div>
                <div class="card-value">{money(debt[0])}</div>
                <div class="card-trend-dark">Recovered: {money(debt[1])} | Tickets: {money(ticket[1])}</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("") # Spacer

    # Plotly Charts Section
    recent = db_query(
        "SELECT audit_date, calculated_gross_revenue, calculated_strict_revenue, carb_revenue, calculated_net_profit, carb_yield_ratio FROM Daily_Audits WHERE branch_id=? ORDER BY audit_date ASC LIMIT 7",
        (selected_branch,),
    )
    
    if recent:
        df = pd.DataFrame(recent, columns=["Date", "Gross Revenue", "Strict Revenue", "Carb Revenue", "Net Profit", "Carb Yield Ratio"])
        
        left_col, right_col = st.columns([2, 1])
        
        with left_col:
            st.markdown('<h5>7-Day Revenue vs Profit</h5>', unsafe_allow_html=True)
            # Custom rounded bar chart using Plotly
            fig_bar = px.bar(df, x="Date", y=["Gross Revenue", "Net Profit"], barmode="group", 
                             color_discrete_sequence=['#1A4D2E', '#a3e635'])
            fig_bar.update_layout(
                margin=dict(t=20, b=20, l=0, r=0),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                legend_title_text='',
                xaxis_title="",
                yaxis_title=""
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with right_col:
            st.markdown('<h5>Latest Revenue Split</h5>', unsafe_allow_html=True)
            # Custom Doughnut Chart
            latest_strict = df.iloc[-1]["Strict Revenue"]
            latest_carb = df.iloc[-1]["Carb Revenue"]
            
            if latest_strict + latest_carb > 0:
                fig_pie = go.Figure(data=[go.Pie(labels=['Strict Unit', 'Loose Carb'], values=[latest_strict, latest_carb], hole=.75)])
                fig_pie.update_traces(marker=dict(colors=['#1A4D2E', '#a3e635']), textinfo='percent', hoverinfo='label+value')
                fig_pie.update_layout(
                    margin=dict(t=20, b=20, l=0, r=0), 
                    showlegend=True, 
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No revenue split available for the most recent audit.")

        st.markdown('<h5>Audit Ledger</h5>', unsafe_allow_html=True)
        # Sort descending for the actual table view
        df_desc = df.sort_values(by="Date", ascending=False)
        for col in ["Gross Revenue", "Strict Revenue", "Carb Revenue", "Net Profit"]:
            df_desc[col] = df_desc[col].map(money)
        render_clean_table(df_desc)
    else:
        st.info("No audits have been recorded for this branch yet.")


# ============================================================
# Evening Audit
# ============================================================
elif module == "Evening Audit":
    st.title("🌙 Evening Audit")
    st.caption("Zero-touch end-of-day capture: cumulative production, raw input cost, cash, transfers, OpEx and payroll.")

    if selected_branch is None:
        st.info("Create/select a branch first.")
        st.stop()

    existing = db_query("SELECT audit_id FROM Daily_Audits WHERE branch_id=? AND audit_date=?", (selected_branch, selected_date.isoformat()), one=True)
    if existing:
        st.warning(f"An audit already exists for {selected_date.isoformat()} (Audit #{existing[0]}). Submitting another audit will create a duplicate record.")

    with st.form("evening_audit_form"):
        st.subheader("1. Financial Inputs")
        col1, col2 = st.columns(2)
        with col1:
            cash_in_hand = st.number_input("Cash in hand (₦)", min_value=0.0, step=500.0)
            bank_transfers = st.number_input("Bank transfers (₦)", min_value=0.0, step=500.0)
        with col2:
            stew_soup_cost = st.number_input("Stew & soup daily OpEx (₦)", min_value=0.0, step=500.0)
            staff_wages_paid = st.number_input("Staff wages paid / expected cash deduction (₦)", min_value=0.0, step=500.0)

        st.subheader("2. Dynamic Production Ledger")
        
        menu = active_menu()
        inventory_data = []

        if not menu:
            st.warning("No active menu items exist. Add menu items in Administration.")
        else:
            # Group items for cleaner UI
            strict_items = [m for m in menu if m[2] in ['STRICT_UNIT', 'SWALLOW']]
            carb_items = [m for m in menu if m[2] == 'LOOSE_CARB']

            tab_strict, tab_carbs = st.tabs(["Unit & Swallow Items", "Loose Carbs (Raw Input)"])

            with tab_strict:
                for item_id, item_name, category, unit_price in strict_items:
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.markdown(f"**{item_name}**<br/><span style='color:gray; font-size:0.9em;'>{money(unit_price)}</span>", unsafe_allow_html=True)
                    prepped = c2.number_input("Prepped", min_value=0.0, step=1.0, key=f"p_{selected_branch}_{item_id}_{selected_date}")
                    leftover = c3.number_input("Leftover", min_value=0.0, step=1.0, key=f"l_{selected_branch}_{item_id}_{selected_date}")
                    
                    inventory_data.append({"item_id": item_id, "total_prepped": prepped, "total_leftover": leftover, "raw_cost": 0.0})

            with tab_carbs:
                for item_id, item_name, category, unit_price in carb_items:
                    c1, c2 = st.columns([2, 2])
                    c1.markdown(f"**{item_name}**<br/><span style='color:gray; font-size:0.9em;'>{category}</span>", unsafe_allow_html=True)
                    cost = c2.number_input("Raw Input Cost (₦)", min_value=0.0, step=500.0, key=f"c_{selected_branch}_{item_id}_{selected_date}")
                    
                    inventory_data.append({"item_id": item_id, "total_prepped": 0.0, "total_leftover": 0.0, "raw_cost": cost})

        st.write("") 
        submitted = st.form_submit_button("Execute Evening Audit", type="primary", use_container_width=True)

    if submitted:
        if not menu:
            st.error("Cannot execute an audit without active menu items.")
        else:
            try:
                audit_engine.execute_evening_audit(
                    selected_branch, selected_date.isoformat(), cash_in_hand, bank_transfers, stew_soup_cost, staff_wages_paid, inventory_data
                )
                st.success("Evening audit committed successfully.")
                st.rerun()
            except Exception as exc:
                st.error(f"Audit failed: {exc}")

# ============================================================
# Production & Procurement
# ============================================================
elif module == "Production & Procurement":
    st.title("🥘 Production & Procurement")

    tabs = st.tabs(["Market Purchase", "Inter-Branch Transfer", "Spend Overview"])

    with tabs[0]:
        with st.form("purchase_form"):
            item_name = st.text_input("Item purchased")
            category = st.text_input("Category", placeholder="e.g. Rice, Protein, Vegetable")
            col1, col2 = st.columns(2)
            quantity = col1.number_input("Quantity", min_value=0.0, step=1.0)
            unit_type = col2.text_input("Unit type", placeholder="kg, bag, crate, etc.")
            total_cost = col1.number_input("Total cost (₦)", min_value=0.0, step=500.0)
            payment_method = col2.selectbox("Payment method", ["CASH", "TRANSFER"])

            if st.form_submit_button("Log Purchase", type="primary"):
                if not item_name.strip() or not unit_type.strip():
                    st.error("Item name and unit type are required.")
                else:
                    if safe_call(Inventory_yield.log_market_purchase, selected_branch, item_name.strip(), quantity, total_cost, payment_method, selected_date.isoformat(), unit_type.strip(), category.strip()):
                        st.rerun()

    with tabs[1]:
        other_branches = [b for b in branch_rows if b[0] != selected_branch]
        if not other_branches:
            st.info("Create another branch to enable inter-branch transfers.")
        else:
            with st.form("transfer_form"):
                receiver_map = {branch_label(b): b[0] for b in other_branches}
                receiver_label = st.selectbox("Receiver branch", list(receiver_map.keys()))
                transfer_item = st.text_input("Item")
                transfer_qty = st.number_input("Quantity sent", min_value=0.0, step=1.0)
                estimated_value = st.number_input("Estimated value (₦)", min_value=0.0, step=500.0)

                if st.form_submit_button("Record Transfer", type="primary"):
                    safe_call(Inventory_yield.log_inter_branch_transfer, selected_branch, receiver_map[receiver_label], transfer_item.strip(), transfer_qty, estimated_value)

    with tabs[2]:
        spend = db_query("SELECT purchase_date, category, item_name, quantity, unit_type, total_cost, payment_method FROM Procurement_Log WHERE branch_id=? ORDER BY purchase_date DESC, purchase_id DESC LIMIT 100", (selected_branch,))
        if spend:
            df = pd.DataFrame(spend, columns=["Date", "Category", "Item", "Quantity", "Unit", "Total Cost", "Payment"])
            df["Total Cost"] = df["Total Cost"].map(money)
            render_clean_table(df)
        else:
            st.info("No procurement records yet.")

# ============================================================
# Finance & Credits
# ============================================================
elif module == "Finance & Credits":
    st.title("💳 Finance & Credits")
    tabs = st.tabs(["Customers", "Credit Transaction", "Tickets", "Ledger"])

    with tabs[0]:
        with st.form("customer_form"):
            c1, c2 = st.columns(2)
            full_name = c1.text_input("Full name")
            phone = c2.text_input("Phone number")
            company = st.text_input("Company (optional)")
            if st.form_submit_button("Add Customer", type="primary"):
                if not full_name.strip():
                    st.error("Full name is required.")
                else:
                    safe_call(Financial_Ledger.add_customers, selected_branch, full_name.strip(), phone.strip(), company.strip())

        customers = db_query("SELECT customer_id, full_name, phone_number, company_name, credit_limit FROM Customers_Debtors WHERE branch_id=? ORDER BY full_name", (selected_branch,))
        if customers:
            df = pd.DataFrame(customers, columns=["ID", "Name", "Phone", "Company", "Credit Limit"])
            df["Credit Limit"] = df["Credit Limit"].map(money)
            render_clean_table(df, hide_cols=["ID"])

    with tabs[1]:
        customers = db_query("SELECT customer_id, full_name FROM Customers_Debtors WHERE branch_id=? ORDER BY full_name", (selected_branch,))
        if not customers:
            st.info("Add a customer first.")
        else:
            customer_map = {f"{c[1]}": c[0] for c in customers}
            with st.form("credit_form"):
                customer_label = st.selectbox("Customer", list(customer_map.keys()))
                tx_type = st.selectbox("Transaction", ["DEBT", "REPAYMENT"])
                amount = st.number_input("Amount (₦)", min_value=0.0, step=500.0)
                notes = st.text_input("Notes")
                if st.form_submit_button("Post Transaction", type="primary"):
                    safe_call(Financial_Ledger.log_credit_transaction, customer_map[customer_label], selected_branch, tx_type, amount, notes.strip() or None)

    with tabs[2]:
        with st.form("ticket_form"):
            ticket_count = st.number_input("Tickets sold", min_value=0, step=1)
            ticket_value = st.number_input("Ticket value (₦)", min_value=0.0, value=1000.0, step=100.0)
            if st.form_submit_button("Log Tickets", type="primary"):
                safe_call(financial_ops.log_daily_tickets, selected_branch, selected_date.isoformat(), ticket_count, ticket_value)

    with tabs[3]:
        ledger = db_query("SELECT cl.transaction_date, cd.full_name, cl.transaction_type, cl.amount, cl.notes FROM Credit_Ledger cl JOIN Customers_Debtors cd ON cd.customer_id=cl.customer_id WHERE cl.branch_id=? ORDER BY cl.transaction_date DESC LIMIT 100", (selected_branch,))
        if ledger:
            df = pd.DataFrame(ledger, columns=["Date", "Customer", "Type", "Amount", "Notes"])
            df["Amount"] = df["Amount"].map(money)
            render_clean_table(df)
        else:
            st.info("No credit transactions yet.")

# ============================================================
# HR & Scheduling
# ============================================================
elif module == "HR & Scheduling":
    st.title("👥 HR & Scheduling")
    tabs = st.tabs(["Roster", "Assign Shift", "Attendance", "Staff History"])

    with tabs[0]:
        roster = db_query("SELECT sr.shift_id, s.staff_id, s.full_name, s.role, b.branch_name, sr.shift_date FROM Shift_Roster sr JOIN Staff s ON s.staff_id=sr.staff_id JOIN Branches b ON b.branch_id=sr.branch_id WHERE sr.shift_date=? ORDER BY b.branch_name, s.full_name", (selected_date.isoformat(),))
        if roster:
            df = pd.DataFrame(roster, columns=["Shift ID", "Staff ID", "Name", "Role", "Branch", "Date"])
            render_clean_table(df, hide_cols=["Shift ID", "Staff ID"])
        else:
            st.info("No shifts scheduled for this date.")

    with tabs[1]:
        staff_all = db_query("SELECT staff_id, full_name, role, branch_id FROM Staff WHERE is_active=1 ORDER BY full_name")
        if not staff_all:
            st.info("No active staff available.")
        else:
            staff_map = {f"{s[1]} — {s[2]}": s for s in staff_all}
            branch_map = {branch_label(b): b[0] for b in branch_rows}

            with st.form("assign_shift_form"):
                staff_label = st.selectbox("Staff", list(staff_map.keys()))
                roster_branch_label = st.selectbox("Assignment branch", list(branch_map.keys()))
                roster_date = st.date_input("Shift date", value=selected_date)
                emergency = st.checkbox("Emergency override")

                if st.form_submit_button("Assign Shift", type="primary"):
                    staff_id = staff_map[staff_label][0]
                    try:
                        shift_scheduler.assign_shift(staff_id, branch_map[roster_branch_label], roster_date.isoformat(), is_emergency_override=emergency)
                        st.success("Shift assigned.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    with tabs[2]:
        audits = db_query("SELECT audit_id, audit_date FROM Daily_Audits WHERE branch_id=? ORDER BY audit_date DESC, audit_id DESC LIMIT 30", (selected_branch,))
        scheduled_staff = db_query("SELECT DISTINCT s.staff_id, s.full_name, s.role, s.daily_rate FROM Shift_Roster sr JOIN Staff s ON s.staff_id=sr.staff_id WHERE sr.branch_id=? AND sr.shift_date=? AND s.is_active=1 ORDER BY s.full_name", (selected_branch, selected_date.isoformat()))

        if not audits:
            st.info("Run an Evening Audit first so attendance has an audit_id.")
        elif not scheduled_staff:
            st.info("No active staff are scheduled for this branch/date.")
        else:
            audit_map = {f"Audit #{a[0]} — {a[1]}": a[0] for a in audits}
            with st.form("attendance_form"):
                audit_label = st.selectbox("Linked audit", list(audit_map.keys()))

                attendance_data = []
                for staff_id, name, role, rate in scheduled_staff:
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.markdown(f"**{name}**<br/><span style='color:gray; font-size:0.9em;'>{money(rate)}/day</span>", unsafe_allow_html=True)
                    status = c2.selectbox("Status", ["PRESENT", "ABSENT", "APPROVED_OFF"], key=f"att_{selected_branch}_{staff_id}_{selected_date}")
                    wage = c3.number_input("Wage earned", min_value=0.0, value=float(rate if status == "PRESENT" else 0), step=500.0, key=f"wage_{selected_branch}_{staff_id}_{selected_date}")
                    attendance_data.append((staff_id, status, wage))

                st.write("")
                if st.form_submit_button("Save Attendance", type="primary"):
                    try:
                        for staff_id, status, wage in attendance_data:
                            shift_scheduler.log_daily_attendance(audit_map[audit_label], staff_id, status, wage)
                        st.success("Attendance records saved.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    with tabs[3]:
        staff_rows = db_query("SELECT s.staff_id, s.full_name, s.role, s.daily_rate, s.is_active, b.branch_name FROM Staff s JOIN Branches b ON b.branch_id=s.branch_id ORDER BY s.is_active DESC, s.full_name")
        if staff_rows:
            df = pd.DataFrame(staff_rows, columns=["ID", "Name", "Role", "Daily Rate", "Active", "Branch"])
            df["Daily Rate"] = df["Daily Rate"].map(money)
            df["Active"] = df["Active"].map({1: "ACTIVE", 0: "INACTIVE"})
            render_clean_table(df, hide_cols=["ID"])

# ============================================================
# Administration
# ============================================================
elif module == "Administration":
    st.title("⚙️ Administration")
    tabs = st.tabs(["Branches", "Menu", "Staff", "System Health"])

    with tabs[0]:
        with st.form("branch_form"):
            c1, c2 = st.columns(2)
            branch_name = c1.text_input("Branch name")
            location = c2.text_input("Location")
            if st.form_submit_button("Create Branch", type="primary"):
                if not branch_name.strip():
                    st.error("Branch name is required.")
                else:
                    safe_call(core_ops.add_branch, branch_name.strip(), location.strip())
                    st.rerun()

        rows = branches()
        if rows:
            render_clean_table(pd.DataFrame(rows, columns=["ID", "Branch", "Location"]), hide_cols=["ID"])

    with tabs[1]:
        with st.form("menu_form"):
            c1, c2, c3 = st.columns(3)
            item_name = c1.text_input("Item name")
            category = c2.selectbox("Category", ["STRICT_UNIT", "SWALLOW", "LOOSE_CARB"])
            unit_price = c3.number_input("Unit price (₦)", min_value=0.0, step=100.0)

            if st.form_submit_button("Add Menu Item", type="primary"):
                if not item_name.strip():
                    st.error("Item name is required.")
                else:
                    safe_call(core_ops.add_menu_item, item_name.strip(), category, unit_price)
                    st.rerun()

        menu_rows = db_query("SELECT item_id, item_name, category, unit_price, is_active FROM Menu_Items ORDER BY is_active DESC, item_name")
        if menu_rows:
            df = pd.DataFrame(menu_rows, columns=["ID", "Item", "Category", "Unit Price", "Active"])
            df["Unit Price"] = df["Unit Price"].map(money)
            df["Active"] = df["Active"].map({1: "ACTIVE", 0: "INACTIVE"})
            render_clean_table(df, hide_cols=["ID"])

    with tabs[2]:
        with st.form("staff_form"):
            staff_branch_map = {branch_label(b): b[0] for b in branch_rows}
            if not staff_branch_map:
                st.info("Create a branch first.")
                st.form_submit_button("Create Staff", disabled=True)
            else:
                staff_branch_label = st.selectbox("Branch", list(staff_branch_map.keys()))
                c1, c2 = st.columns(2)
                full_name = c1.text_input("Full name")
                role = c2.text_input("Role")
                daily_rate = c1.number_input("Daily rate (₦)", min_value=0.0, step=500.0)

                if st.form_submit_button("Onboard Staff", type="primary"):
                    if not full_name.strip() or not role.strip():
                        st.error("Name and role are required.")
                    else:
                        safe_call(core_ops.add_staff, staff_branch_map[staff_branch_label], full_name.strip(), role.strip(), daily_rate)
                        st.rerun()

        st.divider()
        st.subheader("Deactivate staff")
        active_rows = db_query("SELECT staff_id, full_name, role, daily_rate FROM Staff WHERE is_active=1 ORDER BY full_name")
        if active_rows:
            staff_deactivate_map = {f"{r[1]} — {r[2]}": r[0] for r in active_rows}
            staff_to_deactivate = st.selectbox("Active staff member", list(staff_deactivate_map.keys()))
            if st.button("Deactivate Staff", type="secondary"):
                safe_call(core_ops.deactivate_staff, staff_deactivate_map[staff_to_deactivate])
                st.rerun()

    with tabs[3]:
        checks = []
        required = ["Branches", "Menu_Items", "Staff", "Customers_Debtors", "Credit_Ledger", "Procurement_Log", "Ticket_Logs", "Inter_Branch_Transfers", "Daily_Audits", "Audit_Line_Items", "Daily_Attendance", "Shift_Roster"]
        existing_tables = {r[0] for r in db_query("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in required:
            checks.append({"Check": f"Table: {table}", "Status": "OK ✅" if table in existing_tables else "MISSING ❌"})

        indexes = db_query("PRAGMA index_list('Shift_Roster')")
        unique_lock = any(len(row) > 2 and row[2] == 1 for row in indexes)
        checks.append({"Check": "Shift_Roster unique lock", "Status": "OK ✅" if unique_lock else "REVIEW ⚠️"})

        render_clean_table(pd.DataFrame(checks))