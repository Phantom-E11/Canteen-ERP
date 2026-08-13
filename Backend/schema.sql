CREATE TABLE IF NOT EXISTS Branches (
    id SERIAL PRIMARY KEY, 
    name TEXT NOT NULL, 
    location TEXT NOT NULL, 
    branch_type TEXT DEFAULT 'Main Hub', 
    status TEXT DEFAULT 'Open'
);

CREATE TABLE IF NOT EXISTS Staff (
    id SERIAL PRIMARY KEY, 
    full_name TEXT NOT NULL, 
    role TEXT NOT NULL, 
    daily_rate REAL NOT NULL, 
    branch_id INTEGER, 
    status TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS Menu_Catalog (
    id SERIAL PRIMARY KEY, 
    item_name TEXT NOT NULL, 
    category TEXT NOT NULL, 
    unit_price REAL NOT NULL, 
    status TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS Procurement_Ledger (
    id SERIAL PRIMARY KEY, 
    item_name TEXT NOT NULL, 
    quantity REAL NOT NULL, 
    unit_type TEXT NOT NULL, 
    total_cost REAL NOT NULL, 
    payment_method TEXT NOT NULL, 
    expense_type TEXT DEFAULT 'DAILY_OPEX', 
    date_logged DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS Inter_Branch_Transfers (
    id SERIAL PRIMARY KEY, 
    sender_id INTEGER, 
    receiver_id INTEGER, 
    item_name TEXT NOT NULL, 
    quantity REAL NOT NULL, 
    transfer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    stew_soup_cost REAL DEFAULT 0.0, 
    payroll_deductions REAL NOT NULL, 
    calculated_strict_revenue REAL DEFAULT 0.0, 
    carb_revenue REAL DEFAULT 0.0, 
    net_profit REAL NOT NULL, 
    leftover_rice_spoons INTEGER NOT NULL, 
    leftover_swallow_wraps INTEGER NOT NULL, 
    carb_yield_ratio REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS Audit_Line_Items (
    id SERIAL PRIMARY KEY, 
    audit_id INTEGER, 
    menu_item_id INTEGER, 
    quantity_sold REAL NOT NULL, 
    revenue REAL NOT NULL
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