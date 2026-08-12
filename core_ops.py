from database import get_db_connection

def add_branch(branch_name, location):
    branch_name = branch_name.title()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Branches (branch_name, location) VALUES (?, ?)",
            (branch_name, location)
        )

def add_staff(branch_id, full_name, role, daily_rate):
    full_name = full_name.title()
    role = role.title()
    if daily_rate < 0 or daily_rate == 0:
        raise ValueError("Daily rate cannot be negative or zero.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Staff (branch_id, full_name, role, daily_rate) VALUES (?, ?, ?, ?)",
            (branch_id, full_name, role, daily_rate)
        )

def get_active_staff(branch_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT staff_id, full_name, role, daily_rate FROM Staff WHERE branch_id = ? AND is_active = 1",
            (branch_id,)
        )
        return cursor.fetchall()
def deactivate_staff(staff_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Staff SET is_active = 0 WHERE staff_id = ?",
            (staff_id,)
        )

def add_menu_item(item_name, category, unit_price):
    item_name = item_name.title()
    category = category.upper()
    if category not in ['STRICT_UNIT', 'SWALLOW', 'LOOSE_CARB']:
        raise ValueError("Invalid category. Must be one of: STRICT_UNIT, SWALLOW, LOOSE_CARB.")
    if unit_price < 0 or unit_price == 0:
        raise ValueError("Unit price cannot be negative or zero.")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Menu_Items (item_name, category, unit_price) VALUES (?, ?, ?)",
            (item_name, category, unit_price)
        )
def get_active_menu_items():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT item_id, item_name, category, unit_price FROM Menu_Items WHERE is_active = 1"
        )
        return cursor.fetchall()