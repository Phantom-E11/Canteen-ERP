import sqlite3

SQL_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE Branches (
    branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_name TEXT NOT NULL UNIQUE,
    location TEXT
);

CREATE TABLE Menu_Items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT UNIQUE NOT NULL,
    category TEXT CHECK(category IN ('STRICT_UNIT', 'SWALLOW', 'LOOSE_CARB')) NOT NULL,
    unit_price REAL NOT NULL,
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE Staff (
    staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    daily_rate REAL NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (branch_id) REFERENCES Branches(branch_id)
);

CREATE TABLE Customers_Debtors (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,
    full_name TEXT NOT NULL,
    phone_number TEXT,
    company_name TEXT,
    credit_limit REAL DEFAULT 10000.00,
    FOREIGN KEY (branch_id) REFERENCES Branches(branch_id)
);

CREATE TABLE Credit_Ledger (
    credit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    branch_id INTEGER NOT NULL,
    transaction_type TEXT CHECK(transaction_type IN ('DEBT', 'REPAYMENT')) NOT NULL,
    amount REAL NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (customer_id) REFERENCES Customers_Debtors(customer_id),
    FOREIGN KEY (branch_id) REFERENCES Branches(branch_id)
);

CREATE TABLE Procurement_Log (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,
    purchase_date DATE NOT NULL,
    category TEXT NOT NULL,
    item_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_type TEXT NOT NULL,
    total_cost REAL NOT NULL,
    payment_method TEXT CHECK(payment_method IN ('CASH', 'TRANSFER')) NOT NULL,
    FOREIGN KEY (branch_id) REFERENCES Branches(branch_id)
);

CREATE TABLE Ticket_Logs (
    ticket_log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,
    log_date DATE NOT NULL,
    tickets_count INTEGER NOT NULL,
    ticket_value REAL DEFAULT 1000.00,
    total_value REAL GENERATED ALWAYS AS (tickets_count * ticket_value),
    payout_status TEXT CHECK(payout_status IN ('PENDING', 'PAID')) DEFAULT 'PENDING',
    settlement_date DATE,
    FOREIGN KEY (branch_id) REFERENCES Branches(branch_id)
);

CREATE TABLE Inter_Branch_Transfers (
    transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sender_branch_id INTEGER NOT NULL,
    receiver_branch_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    quantity_sent REAL NOT NULL,
    estimated_value REAL NOT NULL,
    FOREIGN KEY (sender_branch_id) REFERENCES Branches(branch_id),
    FOREIGN KEY (receiver_branch_id) REFERENCES Branches(branch_id)
);

CREATE TABLE Daily_Audits (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,
    audit_date DATE NOT NULL,
    cash_in_hand REAL NOT NULL,
    bank_transfers REAL NOT NULL,
    stew_soup_cost REAL NOT NULL,
    staff_wages_paid REAL NOT NULL,
    calculated_gross_revenue REAL,
    calculated_strict_revenue REAL,
    carb_revenue REAL,
    calculated_net_profit REAL,
    carb_yield_ratio REAL,
    FOREIGN KEY (branch_id) REFERENCES Branches(branch_id)
);

CREATE TABLE Audit_Line_Items (
    line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    total_prepped REAL NOT NULL, 
    total_leftover REAL NOT NULL,
    raw_cost REAL DEFAULT 0.0, 
    FOREIGN KEY (audit_id) REFERENCES Daily_Audits(audit_id),
    FOREIGN KEY (item_id) REFERENCES Menu_Items(item_id)
);

CREATE TABLE Daily_Attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id INTEGER NOT NULL,
    staff_id INTEGER NOT NULL,
    status TEXT CHECK(status IN ('PRESENT', 'ABSENT', 'APPROVED_OFF')) NOT NULL,
    wage_earned REAL NOT NULL,
    FOREIGN KEY (audit_id) REFERENCES Daily_Audits(audit_id),
    FOREIGN KEY (staff_id) REFERENCES Staff(staff_id)
);

CREATE TABLE Shift_Roster (
    shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id INTEGER NOT NULL,
    branch_id INTEGER NOT NULL,
    shift_date DATE NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES Staff(staff_id),
    FOREIGN KEY (branch_id) REFERENCES Branches(branch_id),
    UNIQUE(staff_id, shift_date) 
);
"""

def initialize_database():
    try:
        conn = sqlite3.connect('canteen_erp.db')
        cursor = conn.cursor()
        cursor.executescript(SQL_SCHEMA)
        conn.commit()
        conn.close()
        print("[SUCCESS] canteen_erp.db generated and tables created.")
    except sqlite3.Error as error:
        print(f"[ERROR] Failed to execute SQLite script: {error}")

if __name__ == "__main__":
    initialize_database()