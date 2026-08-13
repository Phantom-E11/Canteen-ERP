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
    allow_origins=["https://canteen-erp-rouge.vercel.app"], 
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
            
            # Hardcoding schema directly so Render cannot fail to find it
            cur.execute("""
            CREATE TABLE IF NOT EXISTS Branches (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                branch_type TEXT DEFAULT 'Main Hub',
                status TEXT DEFAULT 'Open'
            );
            CREATE TABLE IF NOT EXISTS staff (
                id SERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                daily_rate REAL NOT NULL,
                branch_id INTEGER,
                status TEXT DEFAULT 'Active'
            );
            CREATE TABLE IF NOT EXISTS Procurement_Ledger (
                id SERIAL PRIMARY KEY,
                item_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_type TEXT NOT NULL,
                total_cost REAL NOT NULL,
                payment_method TEXT NOT NULL,
                date_logged DATE DEFAULT CURRENT_DATE
            );
            CREATE TABLE IF NOT EXISTS Corporate_Tickets (
                id SERIAL PRIMARY KEY,
                branch_id INTEGER NOT NULL,
                ticket_count INTEGER NOT NULL,
                value_per_ticket REAL NOT NULL,
                total_value REAL NOT NULL,
                submitted BOOLEAN DEFAULT FALSE,
                date_logged DATE DEFAULT CURRENT_DATE
            );
            CREATE TABLE IF NOT EXISTS Customers (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                company_name TEXT,
                balance REAL DEFAULT 0.0
            );
            CREATE TABLE IF NOT EXISTS Credit_Transactions (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                notes TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS Evening_Audits (
                id SERIAL PRIMARY KEY,
                audit_date DATE DEFAULT CURRENT_DATE,
                cash_counted REAL NOT NULL,
                bank_transfers REAL NOT NULL,
                gross_revenue REAL NOT NULL,
                procurement_deductions REAL NOT NULL,
                payroll_deductions REAL NOT NULL,
                net_profit REAL NOT NULL,
                leftover_rice_spoons INTEGER NOT NULL,
                leftover_swallow_wraps INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Admin_Users (
                id SERIAL PRIMARY KEY, 
                username TEXT, 
                password_hash TEXT
            );
            CREATE TABLE IF NOT EXISTS Friday_Schedules (
                id SERIAL PRIMARY KEY, 
                target_date DATE, 
                week_num INTEGER, 
                staff_name TEXT
            );
            CREATE TABLE IF NOT EXISTS Attendance_Log (
                id SERIAL PRIMARY KEY, 
                log_date DATE, 
                staff_id INTEGER, 
                status TEXT
            );
            """)
            
            cur.execute("SELECT id FROM Admin_Users")
            if not cur.fetchone():
                default_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
                cur.execute("INSERT INTO Admin_Users (username, password_hash) VALUES (%s, %s)", ("admin", default_hash))
            
            conn.commit()
            print("Database tables verified and ready.")
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

class ProcurementItem(BaseModel):
    item: str
    quantity: float
    unit: str
    cost: float
    method: str

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

class AuditItem(BaseModel):
    branch_id: int = 1
    cash: float
    transfers: float
    midDayCash: float
    payroll: float
    leftoverRice: int
    leftoverSwallow: int

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

@app.post("/api/staff")
async def add_staff(staff: StaffCreate):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO staff (full_name, role, daily_rate, status) VALUES (%s, 'Staff', %s, 'Active')", (staff.name, staff.rate))
        conn.commit()
    return {"message": "Staff added successfully"}

@app.get("/api/staff")
async def get_staff():
    try:
        with get_db() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, full_name as name, daily_rate as rate, status FROM staff WHERE status = 'Active'")
            return cur.fetchall()
    except psycopg2.errors.UndefinedTable:
        return []

# --- PROCUREMENT ---
@app.post("/api/procurement")
def log_procurement(data: ProcurementItem):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Procurement_Ledger (item_name, quantity, unit_type, total_cost, payment_method) VALUES (%s, %s, %s, %s, %s)",
            (data.item, data.quantity, data.unit, data.cost, data.method)
        )
        conn.commit()
    return {"status": "success"}

@app.get("/api/procurement/today")
def get_todays_procurement():
    with get_db() as conn:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM Procurement_Ledger WHERE date_logged::date = CURRENT_DATE ORDER BY id DESC")
        return cur.fetchall()

# --- CORPORATE TICKETS ---
@app.post("/api/tickets")
def log_ticket(data: TicketItem):
    total = data.count * data.value
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Corporate_Tickets (branch_id, ticket_count, value_per_ticket, total_value) VALUES (%s, %s, %s, %s)",
            (data.branchId, data.count, data.value, total)
        )
        conn.commit()
    return {"status": "success"}

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
            cur.execute("SELECT id, transaction_type as type, amount, notes, TO_CHAR(transaction_date, 'YYYY-MM-DD') as date FROM Credit_Transactions WHERE customer_id = %s ORDER BY id DESC", (c['id'],))
            c['history'] = cur.fetchall()
        return customers

@app.post("/api/finance/transaction")
def log_customer_transaction(data: TransactionItem):
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Credit_Transactions (customer_id, transaction_type, amount, notes) VALUES (%s, %s, %s, %s)", 
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

@app.post("/api/attendance")
def log_attendance(data: AttendancePayload):
    with get_db() as conn:
        cur = conn.cursor()
        for record in data.records:
            cur.execute("INSERT INTO Attendance_Log (log_date, staff_id, status) VALUES (%s, %s, %s)", (data.date, record.staff_id, record.status))
        conn.commit()
    return {"status": "success"}

# --- EVENING AUDIT & DASHBOARD ---
@app.post("/api/audit")
def log_evening_audit(data: AuditItem):
    gross = data.cash + data.transfers
    net = gross - data.midDayCash - data.payroll
    
    with get_db() as conn:
        cur = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute("SELECT id FROM Evening_Audits WHERE audit_date = %s", (today,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Audit already submitted for today.")

        cur.execute("""
            INSERT INTO Evening_Audits 
            (cash_counted, bank_transfers, gross_revenue, procurement_deductions, payroll_deductions, net_profit, leftover_rice_spoons, leftover_swallow_wraps)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (data.cash, data.transfers, gross, data.midDayCash, data.payroll, net, data.leftoverRice, data.leftoverSwallow))
        conn.commit()
    return {"status": "success", "net_profit": net}

@app.get("/api/dashboard")
def get_dashboard_metrics():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT SUM(gross_revenue), SUM(net_profit), SUM(cash_counted), SUM(bank_transfers) FROM Evening_Audits WHERE audit_date::date = CURRENT_DATE")
        audit_row = cur.fetchone() or (0, 0, 0, 0)
        
        cur.execute("SELECT SUM(total_cost) FROM Procurement_Ledger WHERE date_logged::date = CURRENT_DATE")
        proc_row = cur.fetchone() or (0,)
        
        cur.execute("SELECT SUM(amount) FROM Credit_Transactions WHERE transaction_type = 'DEBT' AND transaction_date::date = CURRENT_DATE")
        new_debt_row = cur.fetchone()
        new_debt = new_debt_row[0] if new_debt_row and new_debt_row[0] is not None else 0
        
        cur.execute("SELECT SUM(amount) FROM Credit_Transactions WHERE transaction_type = 'REPAYMENT' AND transaction_date::date = CURRENT_DATE")
        rec_debt_row = cur.fetchone()
        rec_debt = rec_debt_row[0] if rec_debt_row and rec_debt_row[0] is not None else 0
        
        return {
            "gross_revenue": audit_row[0] if audit_row[0] is not None else 0,
            "net_profit": audit_row[1] if audit_row[1] is not None else 0,
            "cash_and_transfers": ((audit_row[2] or 0) + (audit_row[3] or 0)),
            "procurement": proc_row[0] if proc_row[0] is not None else 0,
            "new_debt": new_debt,
            "recovered_debt": rec_debt
        }