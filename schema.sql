-- BRANCHES & ADMINISTRATION
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
    status TEXT DEFAULT 'Active',
    FOREIGN KEY(branch_id) REFERENCES Branches(id)
);

CREATE TABLE IF NOT EXISTS Menu_Catalog (
    id SERIAL PRIMARY KEY,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL,
    status TEXT DEFAULT 'Active'
);

-- PROCUREMENT & MID-DAY EXPENSES
CREATE TABLE IF NOT EXISTS Procurement_Ledger (
    id SERIAL PRIMARY KEY,
    item_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit_type TEXT NOT NULL,
    total_cost REAL NOT NULL,
    payment_method TEXT NOT NULL, -- 'CASH' or 'TRANSFER'
    date_logged DATE DEFAULT CURRENT_DATE
);

-- FINANCE: CORPORATE TICKETS
CREATE TABLE IF NOT EXISTS Corporate_Tickets (
    id SERIAL PRIMARY KEY,
    branch_id INTEGER NOT NULL,
    ticket_count INTEGER NOT NULL,
    value_per_ticket REAL NOT NULL,
    total_value REAL NOT NULL,
    submitted BOOLEAN DEFAULT FALSE,
    date_logged DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY(branch_id) REFERENCES Branches(id)
);

-- FINANCE: CUSTOMER DEBT TABS
CREATE TABLE IF NOT EXISTS Customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    company_name TEXT,
    balance REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS Credit_Transactions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL, -- 'DEBT' or 'REPAYMENT'
    amount REAL NOT NULL,
    notes TEXT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(customer_id) REFERENCES Customers(id)
);

-- EVENING AUDIT & RECONCILIATION
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