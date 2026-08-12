from database import get_db_connection

def add_customers(branch_id, full_name, phone_number, company_name):
    full_name = full_name.title()
    company_name = company_name.title() if company_name else None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Customers_Debtors (branch_id, full_name, phone_number, company_name) VALUES (?, ?, ?, ?)",
            (branch_id, full_name, phone_number, company_name)
        )

def log_credit_transaction(customer_id, branch_id, transaction_type, amount, notes=None):
    transaction_type = transaction_type.upper()
    if transaction_type not in ["DEBT", "REPAYMENT"]:
        raise ValueError("Invalid transaction type. Must be one of: DEBT or REPAYMENT.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Credit_Ledger (customer_id, branch_id, transaction_type, amount, notes) VALUES (?, ?, ?, ?, ?)",
            (customer_id, branch_id, transaction_type, amount, notes)
        )

def get_customer_credit_balance(customer_id):
  
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN transaction_type = 'DEBT' THEN amount ELSE 0 END), 0) - 
                COALESCE(SUM(CASE WHEN transaction_type = 'REPAYMENT' THEN amount ELSE 0 END), 0)
            FROM Credit_Ledger 
            WHERE customer_id = ?
        ''', (customer_id,))
        
        result = cursor.fetchone()
        
        return result[0]