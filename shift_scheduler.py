import sqlite3
from datetime import datetime, timedelta
from database import get_db_connection

def has_reached_max_shifts(staff_id, target_date_str, max_days=6):
    """
    Checks if a staff member is already scheduled for the max_days 
    immediately preceding the target date.
    """
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    start_date = target_date - timedelta(days=max_days)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Shift_Roster WHERE staff_id = ? AND shift_date >= ? AND shift_date < ?",
            (staff_id, start_date.strftime("%Y-%m-%d"), target_date_str)
        )
        count = cursor.fetchone()[0]
        return count >= max_days

def assign_shift(staff_id, branch_id, shift_date, is_emergency_override=False):
    """
    Assigns a shift while enforcing hard constraints (physics) 
    and soft constraints (HR burnout policies).
    """
    # 1. Check the Soft Constraints (Burnout Protection & Policy)
    if not is_emergency_override:
        if has_reached_max_shifts(staff_id, shift_date):
            raise ValueError("BURNOUT_WARNING: Staff member needs rest. Use emergency override to force this shift.")
            
        if has_reached_14_day_limit(staff_id, shift_date):
            raise ValueError("BURNOUT_WARNING: Staff has reached the 10 shifts in 14 days limit. Use emergency override.")
            
        if check_weekend_closure(branch_id, shift_date):
            raise ValueError("POLICY_WARNING: Branch 2 is closed on weekends. Schedule this staff at Alpha Hub instead.")
    # 2. Execute the Database Insert (The Hard Constraint)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Shift_Roster (staff_id, branch_id, shift_date) VALUES (?, ?, ?)",
                (staff_id, branch_id, shift_date)
            )
        except sqlite3.IntegrityError:
            # This triggers via the UNIQUE(staff_id, shift_date) constraint in the database
            raise ValueError("HARD_BLOCK: Staff member is already scheduled for a shift on this exact date.")

def cancel_shift(staff_id, shift_date):
    """
    Removes a scheduled shift to handle sick days or emergencies.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM Shift_Roster WHERE staff_id = ? AND shift_date = ?",
            (staff_id, shift_date)
        )

def log_daily_attendance(audit_id, staff_id, status, wage_earned):
    status = status.upper()
    if status not in ['PRESENT', 'ABSENT', 'APPROVED_OFF']:
        raise ValueError("Status must be PRESENT, ABSENT, or APPROVED_OFF")
        
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Daily_Attendance (audit_id, staff_id, status, wage_earned) VALUES (?, ?, ?, ?)",
            (audit_id, staff_id, status, wage_earned)
        )


def check_weekend_closure(target_branch_id, target_date_str):
    """
    Prevents scheduling at Branch 2 on weekends, 
    forcing staff to crossover to Alpha Hub.
    """
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    
    # In Python, Monday is 0, Saturday is 5, Sunday is 6
    if target_date.weekday() >= 5:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT branch_name FROM Branches WHERE branch_id = ?", (target_branch_id,))
            result = cursor.fetchone()
            
            if result and result[0] == "Branch 2":
                return True # Violation triggered
    return False

def has_reached_14_day_limit(staff_id, target_date_str, max_shifts=10, window_days=14):
    """
    Ensures staff do not exceed 10 shifts in a 14-day rolling window.
    """
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    start_date = target_date - timedelta(days=window_days - 1)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Shift_Roster WHERE staff_id = ? AND shift_date >= ? AND shift_date <= ?",
            (staff_id, start_date.strftime("%Y-%m-%d"), target_date_str)
        )
        count = cursor.fetchone()[0]
        return count >= max_shifts