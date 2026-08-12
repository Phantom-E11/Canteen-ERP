from database import get_db_connection

def get_today_credit_metrics(branch_id, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT "
            "COALESCE(SUM(CASE WHEN transaction_type = 'DEBT' THEN amount ELSE 0 END), 0) AS new_debt, "
            "COALESCE(SUM(CASE WHEN transaction_type = 'REPAYMENT' THEN amount ELSE 0 END), 0) AS debt_recovered "
            "FROM Credit_Ledger "
            "WHERE branch_id = ? AND DATE(transaction_date) = ?",
            (branch_id, date)
        )
        result = cursor.fetchone()
        return {
            "total_debt": result[0],
            "total_repayment": result[1]
        }

def get_today_tickets(branch_id, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(tickets_count), 0), COALESCE(SUM(total_value), 0) "
            "FROM Ticket_Logs "
            "WHERE branch_id = ? AND log_date = ?",
            (branch_id, date)
        )
        result = cursor.fetchone()
        return {
            "total_tickets": result[0],
            "total_value": result[1]
        }

def get_today_cash_expenses(branch_id, date):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(total_cost), 0) "
            "FROM Procurement_Log "
            "WHERE branch_id = ? AND purchase_date = ? AND payment_method = 'CASH'",
            (branch_id, date)
        )
        result = cursor.fetchone()
        return {
            "total_cash_expenses": result[0]
        }

def execute_evening_audit(branch_id, audit_date, cash_in_hand, bank_transfers, stew_soup_cost, staff_wages_paid, inventory_data):
    
    credit_metrics = get_today_credit_metrics(branch_id, audit_date)
    ticket_metrics = get_today_tickets(branch_id, audit_date)
    cash_expenses = get_today_cash_expenses(branch_id, audit_date)
    
    new_debt = credit_metrics["total_debt"]
    debt_recovered = credit_metrics["total_repayment"]
    tickets_value = ticket_metrics["total_value"]
    total_cash_spent = cash_expenses["total_cash_expenses"]

    # Everything below must stay indented inside this 'with' block
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        calculated_strict_revenue = 0
        total_carb_cost = 0
    
        # 2. Loop through inventory_data to calculate strict sales and carb costs
        for item in inventory_data:
            cursor.execute("SELECT category, unit_price FROM Menu_Items WHERE item_id = ?", (item['item_id'],))
            result = cursor.fetchone()
            
            category = result[0]
            unit_price = result[1]
            
            if category in ['STRICT_UNIT', 'SWALLOW']:
                calculated_strict_revenue += (item['total_prepped'] - item['total_leftover']) * unit_price
            elif category == 'LOOSE_CARB': 
                total_carb_cost += item['raw_cost']

        # 3. The Reverse Revenue Math 
        total_actual_inflow = cash_in_hand + bank_transfers
        total_sales_revenue = (total_actual_inflow + staff_wages_paid + total_cash_spent + new_debt + tickets_value) - debt_recovered
        
        carb_revenue = total_sales_revenue - calculated_strict_revenue
        calculated_net_profit = total_sales_revenue - (total_carb_cost + stew_soup_cost + staff_wages_paid)
        carb_yield_ratio = (carb_revenue / total_carb_cost) if total_carb_cost > 0 else 0

        # 4. Insert Master Audit
        cursor.execute(
            "INSERT INTO Daily_Audits (branch_id, audit_date, cash_in_hand, bank_transfers, stew_soup_cost, staff_wages_paid, calculated_gross_revenue, calculated_strict_revenue, carb_revenue, calculated_net_profit, carb_yield_ratio) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            (branch_id, audit_date, cash_in_hand, bank_transfers, stew_soup_cost, staff_wages_paid, total_sales_revenue, calculated_strict_revenue, carb_revenue, calculated_net_profit, carb_yield_ratio)
        )
        audit_id = cursor.lastrowid

        # 5. Insert Line Items
        for item in inventory_data:
            cursor.execute(
                "INSERT INTO Audit_Line_Items (audit_id, item_id, total_prepped, total_leftover, raw_cost) VALUES (?, ?, ?, ?, ?)", 
                (audit_id, item['item_id'], item['total_prepped'], item['total_leftover'], item['raw_cost'])
            )