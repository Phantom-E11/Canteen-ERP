from database import get_db_connection

def log_market_purchase(branch_id, item_name, quantity, total_cost, payment_method, purchase_date, unit_type, category):
    payment_method = payment_method.upper()
    if payment_method not in ["CASH", "TRANSFER"]:
        raise ValueError("Invalid payment method. Must be one of: CASH or TRANSFER.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Procurement_log (branch_id, item_name, quantity, total_cost, payment_method, purchase_date, unit_type, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (branch_id, item_name, quantity, total_cost, payment_method, purchase_date, unit_type, category)
        )
        
def calculate_weekly_spend(branch_id, start_date, end_date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(total_cost) FROM Procurement_log WHERE branch_id = ? AND purchase_date BETWEEN ? AND ?",
            (branch_id, start_date, end_date)
        )
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

def get_daily_cash_expenses(branch_id, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(total_cost) FROM Procurement_log WHERE branch_id = ? AND purchase_date = ? AND payment_method = 'CASH'",
            (branch_id, date)
        )
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

def log_inter_branch_transfer(sender_branch_id, receiver_branch_id, item_name, quantity_sent, estimated_value):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Inter_Branch_Transfers (sender_branch_id, receiver_branch_id, item_name, quantity_sent, estimated_value) VALUES (?, ?, ?, ?, ?)",
            (sender_branch_id, receiver_branch_id, item_name, quantity_sent, estimated_value)
        )