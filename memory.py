import sqlite3

DATABASE = "employee.db"


def connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = connect()
    c = conn.cursor()

    # -----------------------------
    # Customers
    # -----------------------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # -----------------------------
    # Chats
    # -----------------------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        user_message TEXT,
        ai_reply TEXT,
        admin_reply TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id)
        REFERENCES customers(id)
    )
    """)
    
    c.execute("""
CREATE TABLE IF NOT EXISTS notifications (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    customer_id INTEGER,

    message TEXT,

    is_read INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


    # -----------------------------
    # Orders
    # -----------------------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        service TEXT,
        invoice TEXT UNIQUE,
        payment_invoice TEXT,
        amount INTEGER,
        delivery TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id)
        REFERENCES customers(id)
    )
    """)

    # -----------------------------
    # Payments
    # -----------------------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        filename TEXT,
        status TEXT DEFAULT 'Waiting',
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(order_id)
        REFERENCES orders(id)
    )
    """)

    # -----------------------------
    # Admin Logs
    # -----------------------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS admin_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# ===============================
# CUSTOMER FUNCTIONS
# ===============================

def create_customer(name, phone):

    conn = connect()
    c = conn.cursor()

    c.execute(
        "SELECT id FROM customers WHERE phone=?",
        (phone,)
    )

    customer = c.fetchone()

    if customer:
        conn.close()
        return customer["id"]

    c.execute(
        """
        INSERT INTO customers(
            name,
            phone
        )
        VALUES(?,?)
        """,
        (
            name,
            phone
        )
    )

    customer_id = c.lastrowid

    conn.commit()
    conn.close()

    return customer_id


def get_customer(customer_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT *
        FROM customers
        WHERE id=?
        """,
        (customer_id,)
    )

    customer = c.fetchone()

    conn.close()

    return customer
    
# ===============================
# CHAT FUNCTIONS
# ===============================

def save_chat(customer_id, user_message, ai_reply):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO chats(
            customer_id,
            user_message,
            ai_reply
        )
        VALUES(?,?,?)
        """,
        (
            customer_id,
            user_message,
            ai_reply
        )
    )

    conn.commit()
    conn.close()


def get_recent_chats(customer_id, limit=10):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT
            user_message,
            ai_reply
        FROM chats
        WHERE customer_id=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            customer_id,
            limit
        )
    )

    rows = c.fetchall()

    conn.close()

    return list(reversed(rows))


def get_all_chats(customer_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT
            id,
            user_message,
            ai_reply,
            created_at
        FROM chats
        WHERE customer_id=?
        ORDER BY id ASC
        """,
        (customer_id,)
    )

    rows = c.fetchall()

    conn.close()

    return rows


def delete_chat(chat_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        DELETE FROM chats
        WHERE id=?
        """,
        (chat_id,)
    )

    conn.commit()
    conn.close()


def clear_customer_chats(customer_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        DELETE FROM chats
        WHERE customer_id=?
        """,
        (customer_id,)
    )

    conn.commit()
    conn.close()


def count_chats():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT COUNT(*)
        FROM chats
        """
    )

    total = c.fetchone()[0]

    conn.close()

    return total   
    
# ===============================
# ORDER FUNCTIONS
# ===============================

SERVICES = {
    "Unlimited Airtel Data Activation": 53000,
    "Monthly Premium Files": 4000,
    "Weekly Premium Files": 1000
}


def generate_invoice():

    conn = connect()
    c = conn.cursor()

    c.execute(
        "SELECT COUNT(*) FROM orders"
    )

    total = c.fetchone()[0] + 1

    conn.close()

    return f"AAM-{total:06d}"


def pending_order_exists(customer_id, service):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT id FROM orders
        WHERE customer_id=?
        AND service=?
        AND status='pending'
        """,
        (
            customer_id,
            service
        )
    )

    result = c.fetchone()

    conn.close()

    return result is not None


def create_order(customer_id, service):

    invoice = generate_invoice()

    amount = SERVICES.get(service, 0)

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO orders(
            customer_id,
            service,
            invoice,
            amount,
            status
        )
        VALUES(?,?,?,?,?)
        """,
        (
            customer_id,
            service,
            invoice,
            amount,
            "pending"
        )
    )

    order_id = c.lastrowid

    conn.commit()
    conn.close()

    return order_id, invoice
    
def save_invoice(customer_id, invoice):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        UPDATE orders
        SET payment_invoice = ?,
            status = 'Waiting Verification'
        WHERE customer_id = ?
        AND status = 'Pending'
        """,
        (
            invoice,
            customer_id
        )
    )

    conn.commit()
    conn.close()    


def get_orders():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT
            orders.id,
            customers.name,
            customers.phone,
            orders.service,
            orders.invoice,
            orders.amount,
            orders.status,
            orders.created_at
        FROM orders
        JOIN customers
        ON customers.id = orders.customer_id
        ORDER BY orders.id DESC
        """
    )

    rows = c.fetchall()

    conn.close()

    return rows


def get_order(order_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT *
        FROM orders
        WHERE id=?
        """,
        (order_id,)
    )

    order = c.fetchone()

    conn.close()

    return order


def update_order_status(order_id, status):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        UPDATE orders
        SET status=?
        WHERE id=?
        """,
        (
            status,
            order_id
        )
    )

    conn.commit()
    conn.close()


def delete_order(order_id):

    conn = connect()
    c = conn.cursor()

    try:

        # Delete payment records belonging to this order first.
        # This prevents foreign-key errors when the order has a receipt.
        try:
            c.execute(
                """
                DELETE FROM payments
                WHERE order_id=?
                """,
                (order_id,)
            )
        except Exception:
            pass

        # Delete the order itself.
        c.execute(
            """
            DELETE FROM orders
            WHERE id=?
            """,
            (order_id,)
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def delete_customer(customer_id):

    conn = connect()
    c = conn.cursor()

    # Delete the customer's orders first
    c.execute(
        """
        DELETE FROM orders
        WHERE customer_id=?
        """,
        (customer_id,)
    )

    # Delete the customer's chats
    try:
        c.execute(
            """
            DELETE FROM chats
            WHERE customer_id=?
            """,
            (customer_id,)
        )
    except Exception:
        pass

    # Delete the customer
    c.execute(
        """
        DELETE FROM customers
        WHERE id=?
        """,
        (customer_id,)
    )

    conn.commit()
    conn.close()


def search_orders(keyword):

    conn = connect()
    c = conn.cursor()

    search = f"%{keyword}%"

    c.execute(
        """
        SELECT
            orders.id,
            customers.name,
            customers.phone,
            orders.service,
            orders.invoice,
            orders.amount,
            orders.status,
            orders.created_at
        FROM orders
        JOIN customers
        ON customers.id = orders.customer_id
        WHERE
            customers.name LIKE ?
            OR customers.phone LIKE ?
            OR orders.service LIKE ?
            OR orders.invoice LIKE ?
        ORDER BY orders.id DESC
        """,
        (
            search,
            search,
            search,
            search
        )
    )

    rows = c.fetchall()

    conn.close()

    return rows


def count_orders():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT COUNT(*)
        FROM orders
        """
    )

    total = c.fetchone()[0]

    conn.close()

    return total
    
# ===============================
# PAYMENT FUNCTIONS
# ===============================

def save_payment_proof(order_id, filename):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO payments(
            order_id,
            filename
        )
        VALUES(?,?)
        """,
        (
            order_id,
            filename
        )
    )

    conn.commit()
    conn.close()


def get_payment(order_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT *
        FROM payments
        WHERE order_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (order_id,)
    )

    payment = c.fetchone()

    conn.close()

    return payment


def get_all_payments():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT
            payments.id,
            payments.order_id,
            payments.filename,
            payments.status,
            payments.uploaded_at,
            customers.name,
            customers.phone,
            orders.invoice,
            orders.service,
            orders.amount
        FROM payments
        JOIN orders
            ON payments.order_id = orders.id
        JOIN customers
            ON orders.customer_id = customers.id
        ORDER BY payments.id DESC
        """
    )

    payments = c.fetchall()

    conn.close()

    return payments


def approve_payment(order_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        UPDATE payments
        SET status='Approved'
        WHERE order_id=?
        """,
        (order_id,)
    )

    c.execute(
        """
        UPDATE orders
        SET status='Completed'
        WHERE id=?
        """,
        (order_id,)
    )

    conn.commit()
    conn.close()


def reject_payment(order_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        UPDATE payments
        SET status='Rejected'
        WHERE order_id=?
        """,
        (order_id,)
    )

    conn.commit()
    conn.close()


def payment_exists(order_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT id
        FROM payments
        WHERE order_id=?
        """,
        (order_id,)
    )

    exists = c.fetchone()

    conn.close()

    return exists is not None


def count_payments():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT COUNT(*)
        FROM payments
        """
    )

    total = c.fetchone()[0]

    conn.close()

    return total


def total_revenue():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT COALESCE(SUM(orders.amount),0)
        FROM orders
        JOIN payments
            ON payments.order_id = orders.id
        WHERE payments.status='Approved'
        """
    )

    total = c.fetchone()[0]

    conn.close()

    return total
    
# ===============================
# DASHBOARD & ADMIN FUNCTIONS
# ===============================

def count_customers():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT COUNT(*)
        FROM customers
        """
    )

    total = c.fetchone()[0]

    conn.close()

    return total


def customers_today():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT COUNT(*)
        FROM customers
        WHERE DATE(created_at)=DATE('now')
        """
    )

    total = c.fetchone()[0]

    conn.close()

    return total


def orders_today():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE DATE(created_at)=DATE('now')
        """
    )

    total = c.fetchone()[0]

    conn.close()

    return total


def revenue_today():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT COALESCE(SUM(orders.amount),0)
        FROM orders
        JOIN payments
            ON orders.id = payments.order_id
        WHERE
            payments.status='Approved'
        AND DATE(payments.uploaded_at)=DATE('now')
        """
    )

    total = c.fetchone()[0]

    conn.close()

    return total


def top_service():

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT
            service,
            COUNT(*) as total
        FROM orders
        GROUP BY service
        ORDER BY total DESC
        LIMIT 1
        """
    )

    row = c.fetchone()

    conn.close()

    if row:
        return row["service"]

    return "No orders"


# ===============================
# ADMIN LOGS
# ===============================

def log_action(action):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO admin_logs(action)
        VALUES(?)
        """,
        (action,)
    )

    conn.commit()
    conn.close()


def get_logs(limit=50):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT *
        FROM admin_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    logs = c.fetchall()

    conn.close()

    return logs


# ===============================
# RESET / MAINTENANCE
# ===============================

def delete_all_orders():

    conn = connect()
    c = conn.cursor()

    c.execute("DELETE FROM payments")
    c.execute("DELETE FROM orders")

    conn.commit()
    conn.close()


def delete_all_chats():

    conn = connect()
    c = conn.cursor()

    c.execute("DELETE FROM chats")

    conn.commit()
    conn.close()


def delete_all_customers():

    conn = connect()
    c = conn.cursor()

    c.execute("DELETE FROM payments")
    c.execute("DELETE FROM orders")
    c.execute("DELETE FROM chats")
    c.execute("DELETE FROM customers")

    conn.commit()
    conn.close()
    
def get_recent_activity(limit=15):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT action, created_at
        FROM admin_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = c.fetchall()

    conn.close()

    return rows                                                   
def create_notification(customer_id, message):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO notifications
        (customer_id, message)
        VALUES (?, ?)
        """,
        (customer_id, message)
    )

    conn.commit()
    conn.close() 
    
def get_notifications(customer_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT message, created_at
        FROM notifications
        WHERE customer_id=?
        ORDER BY id DESC
        """,
        (customer_id,)
    )

    rows = c.fetchall()

    conn.close()

    return rows
                                                         
def get_customers():

    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id, name, phone
        FROM customers
        ORDER BY id DESC
    """)

    rows = c.fetchall()

    conn.close()

    return rows


def get_customer_chats(customer_id):

    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT user_message,
               ai_reply,
               created_at
        FROM chats
        WHERE customer_id=?
        ORDER BY id ASC
    """,(customer_id,))

    rows = c.fetchall()

    conn.close()

    return rows    
  
def get_customer_chat(customer_id):

    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT
            id,
            user_message,
            ai_reply,
            admin_reply,
            created_at
        FROM chats
        WHERE customer_id=?
        ORDER BY id ASC
    """, (customer_id,))

    rows = c.fetchall()

    conn.close()

    return rows


def get_customer_orders(customer_id):

    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id,
               invoice,
               service,
               amount,
               status,
               created_at
        FROM orders
        WHERE customer_id=?
        ORDER BY id DESC
    """, (customer_id,))

    rows = c.fetchall()

    conn.close()

    return rows    
  
def save_invoice(customer_id, invoice):

    conn = connect()
    c = conn.cursor()

    c.execute("""
    UPDATE orders
    SET payment_invoice = ?
    WHERE customer_id = ?
    AND status = 'Pending'
    ORDER BY id DESC
    LIMIT 1
    """,
    (
        invoice,
        customer_id
    ))

    conn.commit()
    conn.close()                                                   
def create_delivery(order_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        "SELECT service FROM orders WHERE id=?",
        (order_id,)
    )

    order = c.fetchone()

    if not order:
        return

    service = order["service"]

    if service == "Unlimited Airtel Data Activation":

        message = """
✅ Your Airtel activation is approved.

Your service is now being processed.

Thank you for choosing A.A.M CASH KING1.
"""

    elif service == "Monthly Premium Files":

        message = """
✅ Your Premium Files order has been approved.

Your files are ready.
"""

    else:

        message = """
✅ Your order has been approved.
"""


    c.execute("""
    UPDATE orders
    SET delivery=?
    WHERE id=?
    """,
    (
        message,
        order_id
    ))

    conn.commit()
    conn.close()

    return message                                                                                                                                                                                                               


# ===============================
# ADMIN CHAT REPLY
# ===============================

def save_admin_reply(customer_id, admin_message):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        INSERT INTO chats(
            customer_id,
            user_message,
            ai_reply,
            admin_reply
        )
        VALUES(?, ?, ?, ?)
        """,
        (
            customer_id,
            "",
            "",
            admin_message
        )
    )

    conn.commit()
    conn.close()


def get_customer_conversation(customer_id):

    conn = connect()
    c = conn.cursor()

    c.execute(
        """
        SELECT
            id,
            user_message,
            ai_reply,
            admin_reply,
            created_at
        FROM chats
        WHERE customer_id=?
        ORDER BY id ASC
        """,
        (customer_id,)
    )

    rows = c.fetchall()

    conn.close()

    return rows
