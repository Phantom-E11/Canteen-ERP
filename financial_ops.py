from database import get_db_connection

def log_daily_tickets(branch_id, log_date, tickets_count, ticket_value=1000.00):
    if tickets_count < 0:
        raise ValueError("Ticket count cannot be negative.")
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Ticket_Logs (branch_id, log_date, tickets_count, ticket_value) VALUES (?, ?, ?, ?)",
            (branch_id, log_date, tickets_count, ticket_value)
        )