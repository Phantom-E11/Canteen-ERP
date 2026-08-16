from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
import bcrypt

# --- SECURITY CONFIGURATION ---
SECRET_KEY = "canteen_super_secret_key_change_in_production"
ALGORITHM = "HS256"

app = FastAPI(title="CanteenOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

@app.on_event("startup")
def startup():
    try:
        with get_db() as conn:
            cur = conn.cursor()
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS Branches (
                id SERIAL PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL, 
                branch_type TEXT DEFAULT 'Main Hub', status TEXT DEFAULT 'Open'
            );
            CREATE TABLE IF NOT EXISTS Staff (
                id SERIAL PRIMARY KEY, full_name TEXT NOT NULL, role TEXT NOT NULL, 
                daily_rate REAL NOT NULL, branch_id INTEGER, status TEXT DEFAULT 'Active'
            );
            CREATE TABLE IF NOT EXISTS Menu_Catalog (
                id SERIAL PRIMARY KEY, item_name TEXT NOT NULL, category TEXT NOT NULL, 
                unit_price REAL NOT NULL, status TEXT DEFAULT 'Active'
            );
            CREATE TABLE IF NOT EXISTS Procurement_Ledger (
                id SERIAL PRIMARY KEY, item_name TEXT NOT NULL, quantity REAL NOT NULL, 
                unit_type TEXT NOT NULL, total_cost REAL NOT NULL, payment_method TEXT NOT NULL, 
                expense_type TEXT DEFAULT 'DAILY_OPEX', date_logged DATE DEFAULT CURRENT_DATE
            );
            CREATE TABLE IF NOT EXISTS Inter_Branch_Transfers (
                id SERIAL PRIMARY KEY, sender_id INTEGER, receiver_id INTEGER, 
                item_name TEXT NOT NULL, quantity REAL NOT NULL, transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Corporate_Tickets (
                id SERIAL PRIMARY KEY, branch_id INTEGER NOT NULL, ticket_count INTEGER NOT NULL, 
                value_per_ticket REAL NOT NULL, total_value REAL NOT NULL, submitted BOOLEAN DEFAULT FALSE, 
                date_logged DATE DEFAULT CURRENT_DATE
            );
            CREATE TABLE IF NOT EXISTS Customers (
                id SERIAL PRIMARY KEY, name TEXT NOT NULL, company_name TEXT, balance REAL DEFAULT 0.0
            );
            CREATE TABLE IF NOT EXISTS Credit_Transactions (
                id SERIAL PRIMARY KEY, customer_id INTEGER NOT NULL, transaction_type TEXT NOT NULL, 
                amount REAL NOT NULL, notes TEXT, transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Evening_Audits (
                id SERIAL PRIMARY KEY, audit_date DATE DEFAULT CURRENT_DATE, cash_counted REAL NOT NULL, 
                bank_transfers REAL NOT NULL, gross_revenue REAL NOT NULL, procurement_deductions REAL NOT NULL, 
                stew_soup_cost REAL DEFAULT 0.0, raw_carb_cost REAL DEFAULT 0.0, payroll_deductions REAL NOT NULL, 
                calculated_strict_revenue REAL DEFAULT 0.0, carb_revenue REAL DEFAULT 0.0, 
                net_profit REAL NOT NULL, leftover_rice_spoons INTEGER NOT NULL, 
                leftover_swallow_wraps INTEGER NOT NULL, carb_yield_ratio REAL DEFAULT 0.0
            );
            CREATE TABLE IF NOT EXISTS Audit_Line_Items (
                id SERIAL PRIMARY KEY, audit_id INTEGER, menu_item_id INTEGER, 
                quantity_sold REAL NOT NULL, revenue REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Admin_Users (
                id SERIAL PRIMARY KEY, username TEXT, password_hash TEXT
            );
            CREATE TABLE IF NOT EXISTS Friday_Schedules (
                id SERIAL PRIMARY KEY, target_date DATE, week_num INTEGER, staff_name TEXT
            );
            CREATE TABLE IF NOT EXISTS Attendance_Log (
                id SERIAL PRIMARY KEY, log_date DATE, staff_id INTEGER, status TEXT
            );
            """)
            
            cur.execute("""
            ALTER TABLE Procurement_Ledger ADD COLUMN IF NOT EXISTS expense_type TEXT DEFAULT 'DAILY_OPEX';
            ALTER TABLE Evening_Audits ADD COLUMN IF NOT EXISTS stew_soup_cost REAL DEFAULT 0.0;
            ALTER TABLE Evening_Audits ADD COLUMN IF NOT EXISTS raw_carb_cost REAL DEFAULT 0.0;
            ALTER TABLE Evening_Audits ADD COLUMN IF NOT EXISTS calculated_strict_revenue REAL DEFAULT 0.0;
            ALTER TABLE Evening_Audits ADD COLUMN IF NOT EXISTS carb_revenue REAL DEFAULT 0.0;
            ALTER TABLE Evening_Audits ADD COLUMN IF NOT EXISTS carb_yield_ratio REAL DEFAULT 0.0;
            """)
            
            cur.execute("SELECT id FROM Admin_Users")
            if not cur.fetchone():
                default_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
                cur.execute("INSERT INTO Admin_Users (username, password_hash) VALUES (%s, %s)", ("admin", default_hash))
            
            conn.commit()
    except Exception as e:
        print(f"CRITICAL DATABASE ERROR: {e}")

# --- PYDANTIC MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UpdateCredentials(BaseModel):
    new_username: str
    new_password: str

class BranchCreate(BaseModel):
    name: str
    location: str

class MenuCreate(BaseModel):
    item_name: str
    category: str
    unit_price: float

class ProcurementItem(BaseModel):
    item: str
    quantity: float
    unit: str
    cost: float
    method: str
    expense_type: str

class TransferItem(BaseModel):
    sender_id: int
    receiver_id: int
    item_name: str
    quantity: float

class TicketItem(BaseModel):
    branchId: int
    count: int
    value: float

class CustomerCreate(BaseModel):
    name: str

class TransactionItem(BaseModel):
    customer_id: int
    transaction_type: str
    amount: float
    notes: str

class StaffCreate(BaseModel):
    name: str
    rate: float

class ScheduleLock(BaseModel):
    target_date: str
    week1: List[str]
    week2: List[str]

class AttendanceRecord(BaseModel):
    staff_id: int
    status: str

class AttendancePayload(BaseModel):
    date: str
    records: List[AttendanceRecord]

class AuditLineItem(BaseModel):
    menu_item_id: int
    quantity: float
    price: float

class AuditItem(BaseModel):
    branch_id: int = 1
    cash: float
    transfers: float
    midDayCash: float
    stewSoupCost: float
    rawCarbCost: float
    payroll: float
    leftoverRice: int
    leftoverSwallow: int
    line_items: List[AuditLineItem]

# --- AUTHENTICATION ---
@app.post("/api/login")
def login(req: LoginRequest):
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT username, password_hash FROM Admin_Users LIMIT 1")
        admin = cur.fetchone()
        
        if admin:
            is_password_correct = bcrypt.checkpw(req.password.encode('utf-8'), admin['password_hash'].encode('utf-8'))
            if req.username == admin['username'] and is_password_correct:
                token = jwt.encode(
                    {"sub": req.username, "exp": datetime.utcnow() + timedelta(hours=12)}, 
                    SECRET_KEY, algorithm=ALGORITHM
                )
                return {"access_token": token, "token_type": "bearer"}
                
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.put("/api/admin/credentials")
def update_credentials(creds: UpdateCredentials):
    new_hash = bcrypt.hashpw(creds.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Admin_Users SET username = %s, password_hash = %s", (creds.new_username, new_hash))
        conn.commit()
    return {"status": "success", "message": "Credentials updated successfully."}

# --- ADMINISTRATION ---
@app.post("/api/branches")
def add_branch(branch: BranchCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Branches (name, location) VALUES (%s, %s)", (branch.name, branch.location))
        conn.commit()
    return {"status": "success"}

@app.get("/api/branches")
def get_branches():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM Branches")
        return cur.fetchall()

@app.post("/api/menu")
def add_menu_item(data: MenuCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Menu_Catalog (item_name, category, unit_price) VALUES (%s, %s, %s)", 
            (data.item_name, data.category, data.unit_price)
        )
        conn.commit()
    return {"status": "success"}

@app.get("/api/menu")
def get_menu():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM Menu_Catalog WHERE status = 'Active'")
        return cur.fetchall()

@app.post("/api/staff")
async def add_staff(staff: StaffCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO staff (full_name, role, daily_rate, status) VALUES (%s, 'Staff', %s, 'Active')", (staff.name, staff.rate))
        conn.commit()
    return {"message": "Staff added successfully"}

@app.get("/api/staff")
async def get_staff():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, full_name as name, daily_rate as rate, status FROM staff WHERE status = 'Active'")
        return cur.fetchall()

@app.put("/api/staff/{id}/deactivate")
def deactivate_staff(id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE staff SET status = 'Inactive' WHERE id = %s", (id,))
        conn.commit()
    return {"status": "success"}

# --- PROCUREMENT & TRANSFERS ---
@app.post("/api/procurement")
def log_procurement(data: ProcurementItem):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO Procurement_Ledger 
               (item_name, quantity, unit_type, total_cost, payment_method, expense_type) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (data.item, data.quantity, data.unit, data.cost, data.method, data.expense_type)
        )
        conn.commit()
    return {"status": "success"}

@app.get("/api/procurement/today")
def get_todays_procurement():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM Procurement_Ledger WHERE date_logged::date = CURRENT_DATE ORDER BY id DESC")
        return cur.fetchall()

@app.post("/api/transfers")
def log_transfer(data: TransferItem):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO Inter_Branch_Transfers 
               (sender_id, receiver_id, item_name, quantity) 
               VALUES (%s, %s, %s, %s)""", 
            (data.sender_id, data.receiver_id, data.item_name, data.quantity)
        )
        conn.commit()
    return {"status": "success"}

# --- CORPORATE TICKETS ---
@app.post("/api/tickets")
def log_ticket(data: TicketItem):
    total = data.count * data.value
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO Corporate_Tickets 
               (branch_id, ticket_count, value_per_ticket, total_value) 
               VALUES (%s, %s, %s, %s)""",
            (data.branchId, data.count, data.value, total)
        )
        conn.commit()
    return {"status": "success"}

@app.get("/api/tickets")
def get_tickets():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT t.id, t.branch_id as "branchId", b.name as "branchName", 
                   t.ticket_count as count, t.value_per_ticket as value, 
                   t.total_value as total, t.submitted, 
                   TO_CHAR(t.date_logged, 'YYYY-MM-DD') as date 
            FROM Corporate_Tickets t 
            JOIN Branches b ON t.branch_id = b.id 
            ORDER BY t.id DESC
        """)
        return cur.fetchall()

@app.post("/api/tickets/submit/{branch_id}")
def archive_branch_tickets(branch_id: int):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE Corporate_Tickets SET submitted = TRUE WHERE branch_id = %s AND submitted = FALSE", (branch_id,))
        conn.commit()
    return {"status": "success"}

# --- FINANCE & CUSTOMER DEBT ---
@app.post("/api/customers")
def add_customer(data: CustomerCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO Customers (name, balance) VALUES (%s, 0.0)", (data.name,))
        conn.commit()
    return {"status": "success"}

@app.get("/api/customers")
def get_customers():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM Customers ORDER BY name ASC")
        customers = cur.fetchall()
        for c in customers:
            cur.execute("""
                SELECT id, transaction_type as type, amount, notes, 
                       TO_CHAR(transaction_date, 'YYYY-MM-DD') as date 
                FROM Credit_Transactions 
                WHERE customer_id = %s ORDER BY id DESC
            """, (c['id'],))
            c['history'] = cur.fetchall()
        return customers

@app.post("/api/finance/transaction")
def log_customer_transaction(data: TransactionItem):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO Credit_Transactions 
               (customer_id, transaction_type, amount, notes) 
               VALUES (%s, %s, %s, %s)""", 
            (data.customer_id, data.transaction_type, data.amount, data.notes)
        )
        if data.transaction_type == 'DEBT':
            cur.execute("UPDATE Customers SET balance = balance + %s WHERE id = %s", (data.amount, data.customer_id))
        elif data.transaction_type == 'REPAYMENT':
            cur.execute("UPDATE Customers SET balance = balance - %s WHERE id = %s", (data.amount, data.customer_id))
        conn.commit()
    return {"status": "success"}

# --- HR & SCHEDULING ---
@app.post("/api/schedule/lock")
def lock_schedule(data: ScheduleLock):
    with get_db() as conn:
        cur = conn.cursor()
        for name in data.week1:
            cur.execute("INSERT INTO Friday_Schedules (target_date, week_num, staff_name) VALUES (%s, 1, %s)", (data.target_date, name))
        for name in data.week2:
            cur.execute("INSERT INTO Friday_Schedules (target_date, week_num, staff_name) VALUES (%s, 2, %s)", (data.target_date, name))
        conn.commit()
    return {"status": "success"}

@app.get("/api/schedule")
def get_schedule():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT TO_CHAR(target_date, 'Mon DD') as date, week_num, staff_name 
            FROM Friday_Schedules 
            WHERE target_date >= CURRENT_DATE 
            ORDER BY target_date ASC, week_num ASC
        """)
        return cur.fetchall()

@app.post("/api/attendance")
def log_attendance(data: AttendancePayload):
    with get_db() as conn:
        cur = conn.cursor()
        for record in data.records:
            cur.execute("INSERT INTO Attendance_Log (log_date, staff_id, status) VALUES (%s, %s, %s)", (data.date, record.staff_id, record.status))
        conn.commit()
    return {"status": "success"}

# --- EVENING AUDIT & ANALYTICS ---
@app.post("/api/audit")
def log_evening_audit(data: AuditItem):
    gross = data.cash + data.transfers
    strict_rev = sum(item.quantity * item.price for item in data.line_items)
    carb_rev = gross - strict_rev
    
    net = gross - data.midDayCash - data.payroll - data.stewSoupCost
    
    # TRUE FINANCIAL YIELD MATH: Carb Revenue divided by the Raw Capital Cost of Carbs cooked.
    yield_ratio = (carb_rev / data.rawCarbCost) if data.rawCarbCost > 0 else 0.0
    
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM Evening_Audits WHERE audit_date = CURRENT_DATE")
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Audit already submitted for today.")

        cur.execute("""
            INSERT INTO Evening_Audits 
            (cash_counted, bank_transfers, gross_revenue, procurement_deductions, stew_soup_cost, raw_carb_cost,
             payroll_deductions, calculated_strict_revenue, carb_revenue, net_profit, 
             leftover_rice_spoons, leftover_swallow_wraps, carb_yield_ratio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (data.cash, data.transfers, gross, data.midDayCash, data.stewSoupCost, data.rawCarbCost,
              data.payroll, strict_rev, carb_rev, net, data.leftoverRice, data.leftoverSwallow, yield_ratio))
        
        audit_id = cur.fetchone()[0]
        
        for item in data.line_items:
            cur.execute("""
                INSERT INTO Audit_Line_Items (audit_id, menu_item_id, quantity_sold, revenue) 
                VALUES (%s, %s, %s, %s)
            """, (audit_id, item.menu_item_id, item.quantity, item.quantity * item.price))
            
        conn.commit()
    return {"status": "success"}

@app.get("/api/dashboard")
def get_dashboard_metrics():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT SUM(gross_revenue) as gross, SUM(net_profit) as net, SUM(cash_counted)+SUM(bank_transfers) as cash_transfers FROM Evening_Audits WHERE audit_date = CURRENT_DATE")
        audit = cur.fetchone() or {"gross": 0, "net": 0, "cash_transfers": 0}
        
        cur.execute("SELECT SUM(total_cost) FROM Procurement_Ledger WHERE date_logged = CURRENT_DATE AND expense_type = 'DAILY_OPEX'")
        proc_row = cur.fetchone()
        proc = proc_row['sum'] if proc_row and proc_row['sum'] else 0
        
        cur.execute("SELECT SUM(amount) FROM Credit_Transactions WHERE transaction_type = 'DEBT' AND transaction_date::date = CURRENT_DATE")
        debt_row = cur.fetchone()
        debt = debt_row['sum'] if debt_row and debt_row['sum'] else 0
        
        cur.execute("SELECT SUM(amount) FROM Credit_Transactions WHERE transaction_type = 'REPAYMENT' AND transaction_date::date = CURRENT_DATE")
        rec_row = cur.fetchone()
        rec = rec_row['sum'] if rec_row and rec_row['sum'] else 0
        
        cur.execute("SELECT TO_CHAR(audit_date, 'Dy') as day, gross_revenue as revenue FROM Evening_Audits WHERE audit_date >= CURRENT_DATE - INTERVAL '7 days' ORDER BY audit_date ASC")
        chart_data = cur.fetchall()
        
        cur.execute("SELECT id FROM Evening_Audits WHERE audit_date = CURRENT_DATE")
        is_locked = bool(cur.fetchone())
        
        return {
            "gross_revenue": audit['gross'] or 0,
            "net_profit": audit['net'] or 0,
            "cash_and_transfers": audit['cash_transfers'] or 0,
            "procurement": proc,
            "new_debt": debt,
            "recovered_debt": rec,
            "chart_data": chart_data,
            "is_audit_locked": is_locked
        }

@app.get("/api/reports/historical")
def get_historical_reports():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT TO_CHAR(audit_date, 'YYYY-MM-DD') as date, 
                   gross_revenue as gross, net_profit as net, 
                   carb_yield_ratio as yield 
            FROM Evening_Audits 
            ORDER BY audit_date ASC LIMIT 30
        """)
        return cur.fetchall()

@app.get("/api/reports/weekly")
def get_weekly_analytics():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. Total Bulk Restock (CUSTOM FINANCIAL WEEK: Saturday to Friday)
        cur.execute("""
            SELECT SUM(total_cost) as total_bulk 
            FROM Procurement_Ledger 
            WHERE expense_type = 'BULK_RESTOCK' 
            AND date_logged >= (DATE_TRUNC('week', CURRENT_DATE + INTERVAL '2 days') - INTERVAL '2 days')::DATE
        """)
        bulk_row = cur.fetchone()
        bulk_total = bulk_row['total_bulk'] if bulk_row and bulk_row['total_bulk'] else 0

        # 2. Daily Profit vs Expense Breakdown (CUSTOM FINANCIAL WEEK: Saturday to Friday)
        cur.execute("""
            SELECT 
                TO_CHAR(a.audit_date, 'Dy') as day,
                a.net_profit as profit,
                (a.procurement_deductions + a.stew_soup_cost + a.payroll_deductions + 
                 COALESCE((SELECT SUM(total_cost) FROM Procurement_Ledger p WHERE p.date_logged = a.audit_date AND p.expense_type = 'BULK_RESTOCK'), 0)
                ) as expenses
            FROM Evening_Audits a
            WHERE a.audit_date >= (DATE_TRUNC('week', CURRENT_DATE + INTERVAL '2 days') - INTERVAL '2 days')::DATE
            ORDER BY a.audit_date ASC
        """)
        chart_data = cur.fetchall()

        return {
            "total_bulk_weekly": bulk_total,
            "comparison_chart": chart_data
        }

    
# --- ACTIVE ALERT ENGINE ---
@app.get("/api/alerts")
def get_active_alerts():
    alerts = []
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT SUM(total_cost) FROM Procurement_Ledger WHERE date_logged = CURRENT_DATE AND expense_type = 'DAILY_OPEX'")
        mid_day_cash = cur.fetchone()['sum'] or 0
        if mid_day_cash > 50000:
            alerts.append({"type": "warning", "category": "Procurement", "message": f"Mid-Day OpEx Accumulator is high: ₦{mid_day_cash:,.2f}."})
            
        cur.execute("""
            SELECT b.name, SUM(t.total_value) as total 
            FROM Corporate_Tickets t JOIN Branches b ON t.branch_id = b.id 
            WHERE t.submitted = FALSE GROUP BY b.name HAVING SUM(t.total_value) > 20000
        """)
        for row in cur.fetchall():
            alerts.append({"type": "info", "category": "Finance", "message": f"Action Required: {row['name']} has ₦{row['total']:,.2f} in unsubmitted tickets."})
            
        cur.execute("SELECT name, balance FROM Customers WHERE balance > 15000")
        for row in cur.fetchall():
            alerts.append({"type": "critical", "category": "Credit", "message": f"Credit Alert: {row['name']} has crossed ₦15,000 in active debt."})
            
        cur.execute("SELECT id FROM Evening_Audits WHERE audit_date = CURRENT_DATE")
        if not cur.fetchone():
            alerts.append({"type": "warning", "category": "Audit", "message": "Today's Evening Audit Reconciliation has not been locked."})
            
        cur.execute("SELECT COUNT(*) FROM Attendance_Log WHERE log_date = CURRENT_DATE AND status = 'ABSENT'")
        absent_count = cur.fetchone()['count'] or 0
        if absent_count > 0:
            alerts.append({"type": "critical", "category": "HR", "message": f"Warning: {absent_count} staff member(s) marked ABSENT today."})

    return alerts