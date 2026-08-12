from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
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
    conn = sqlite3.connect("canteenos.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
def startup():
    with open("schema.sql", "r") as f:
        schema = f.read()
    with get_db() as conn:
        conn.executescript(schema)
        
        # Auto-create default admin in database if none exists
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS Admin_Users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT)")
        cur.execute("SELECT id FROM Admin_Users")
        if not cur.fetchone():
            default_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
            cur.execute("INSERT INTO Admin_Users (username, password_hash) VALUES (?, ?)", ("admin", default_hash))

# --- PYDANTIC MODELS ---
class LoginRequest(BaseModel):
    username: str
    password: str

class UpdateCredentials(BaseModel):
    new_username: str
    new_password: str

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

# --- 1. AUTHENTICATION & SECURITY ---
@app.post("/api/login")
def login(req: LoginRequest):
    with get_db() as conn:
        cur = conn.cursor()
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
        conn.execute("UPDATE Admin_Users SET username = ?, password_hash = ?", (creds.new_username, new_hash))
    return {"status": "success", "message": "Credentials updated successfully."}

# --- 2. PROCUREMENT LEDGER ---
@app.post("/api/procurement")
def log_procurement(data: ProcurementItem):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO Procurement_Ledger (item_name, quantity, unit_type, total_cost, payment_method) VALUES (?, ?, ?, ?, ?)",
            (data.item, data.quantity, data.unit, data.cost, data.method)
        )
    return {"status": "success"}

@app.get("/api/procurement/today")
def get_todays_procurement():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM Procurement_Ledger WHERE date_logged = date('now', 'localtime') ORDER BY id DESC")
        return [dict(row) for row in cur.fetchall()]

# --- 3. CORPORATE TICKETS ---
@app.post("/api/tickets")
def log_ticket(data: TicketItem):
    total = data.count * data.value
    with get_db() as conn:
        conn.execute(
            "INSERT INTO Corporate_Tickets (branch_id, ticket_count, value_per_ticket, total_value) VALUES (?, ?, ?, ?)",
            (data.branchId, data.count, data.value, total)
        )
    return {"status": "success"}

@app.post("/api/tickets/submit/{branch_id}")
def archive_branch_tickets(branch_id: int):
    with get_db() as conn:
        conn.execute("UPDATE Corporate_Tickets SET submitted = 1 WHERE branch_id = ? AND submitted = 0", (branch_id,))
    return {"status": "success"}

# --- 4. FINANCE & CUSTOMER DEBT ---
@app.post("/api/finance/transaction")
def log_customer_transaction(data: TransactionItem):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO Credit_Transactions (customer_id, transaction_type, amount, notes) VALUES (?, ?, ?, ?)", 
            (data.customer_id, data.transaction_type, data.amount, data.notes)
        )
        if data.transaction_type == 'DEBT':
            conn.execute("UPDATE Customers SET balance = balance + ? WHERE id = ?", (data.amount, data.customer_id))
        elif data.transaction_type == 'REPAYMENT':
            conn.execute("UPDATE Customers SET balance = balance - ? WHERE id = ?", (data.amount, data.customer_id))
    return {"status": "success"}

# --- 5. EVENING AUDIT & RECONCILIATION ---
@app.post("/api/audit")
def log_evening_audit(data: AuditItem):
    gross = data.cash + data.transfers
    net = gross - data.midDayCash - data.payroll
    
    with get_db() as conn:
        cur = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute("SELECT id FROM Evening_Audits WHERE audit_date = ?", (today,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Audit already submitted for today.")

        conn.execute("""
            INSERT INTO Evening_Audits 
            (cash_counted, bank_transfers, gross_revenue, procurement_deductions, payroll_deductions, net_profit, leftover_rice_spoons, leftover_swallow_wraps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data.cash, data.transfers, gross, data.midDayCash, data.payroll, net, data.leftoverRice, data.leftoverSwallow))
    return {"status": "success", "net_profit": net}

# --- 6. COMMAND CENTER METRICS ---
@app.get("/api/dashboard")
def get_dashboard_metrics():
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT SUM(gross_revenue), SUM(net_profit), SUM(cash_counted), SUM(bank_transfers) FROM Evening_Audits WHERE audit_date = date('now', 'localtime')")
        audit_row = cur.fetchone()
        
        cur.execute("SELECT SUM(total_cost) FROM Procurement_Ledger WHERE date_logged = date('now', 'localtime')")
        proc_row = cur.fetchone()
        
        cur.execute("SELECT SUM(amount) FROM Credit_Transactions WHERE transaction_type = 'DEBT' AND date(transaction_date) = date('now', 'localtime')")
        new_debt = cur.fetchone()[0] or 0
        
        cur.execute("SELECT SUM(amount) FROM Credit_Transactions WHERE transaction_type = 'REPAYMENT' AND date(transaction_date) = date('now', 'localtime')")
        rec_debt = cur.fetchone()[0] or 0
        
        return {
            "gross_revenue": audit_row[0] or 0,
            "net_profit": audit_row[1] or 0,
            "cash_and_transfers": (audit_row[2] or 0) + (audit_row[3] or 0),
            "procurement": proc_row[0] or 0,
            "new_debt": new_debt,
            "recovered_debt": rec_debt
        }