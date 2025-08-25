import sqlite3
import os
from flask import session, g

class Database:
    """Handles all database interactions for the Flask application."""

    def __init__(self, db_path):
        """Initializes the Database class and creates the database if it doesn't exist."""
        self.db_path = db_path
        if not os.path.isfile(self.db_path):
            self._init_database()

    def _init_database(self):
        """Initializes the database schema from an SQL script."""
        with open('database/limas.sql', 'r') as sql_file:
            sql_script = sql_file.read()
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(sql_script)
            conn.commit()
            print("Novo banco de dados criado com sucesso")

    def _get_db_connection(self):
        """Returns the connection of the context"""
        if 'db_conn' not in g:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            g.db_conn = conn
            return conn
        return g.db_conn

    def close_db_connection(self, exception=None):
        """Closes the connection of the context"""
        conn = g.pop('db_conn', None)
        if conn is not None:
            if exception is None:
                conn.commit()
            conn.close()

    def _fetchall_query(self, query, params=(), fetch_limit=0):
        """Execute a query and return a list of dicts with all the results
        if fetch_limit is not zero, return at maximum fetch_limit"""
        cur = self._get_db_connection().execute(query, params)
        if fetch_limit:
            rows = cur.fetchmany(fetch_limit)
        else:
            rows = cur.fetchall()
        return [dict(row) for row in rows]

    def _fetchone_query(self, query, params=()):
        """Execute a query and return a dict with the gotten row.
        if no row is found, return None"""
        row = self._get_db_connection().execute(query, params).fetchone()
        if row:
            return dict(row)
        else:
            return {}

    def _execute_query(self, query, params=()):
        """Execute a query, return cursor.lastrowid"""
        return self._get_db_connection().execute(query, params).lastrowid

    def _executemany_query(self, query, l_params):
        return self._get_db_connection().executemany(query, l_params)

    def add_order_products(self, order_id, increment_products):
        """Adds new products to an existing order, creating an order increment."""
        if not increment_products:
            return
        order_increment_id = self._execute_query(
            "INSERT INTO order_increments (order_id, user_id) VALUES (?, ?)",
            (order_id, session["user_id"])
        )
        for product in increment_products:
            price_row = self._fetchone_query(
                "SELECT price FROM products WHERE id = ?",
                (product["id"],)
            )
            if price_row:
                price = price_row["price"]
                self._execute_query(
                    "INSERT INTO order_products (order_id, product_id, order_increment_id, quantity, current_price) VALUES (?, ?, ?, ?, ?)",
                    (order_id, product["id"], order_increment_id, product["quantity"], price)
                )

    def list_products(self, orders):
        """Retrieves all products for a given list of orders and calculates the total for each."""
        order_products = {}
        for order in orders:
            products = self._fetchall_query(
                "SELECT * FROM (SELECT op.product_id AS id, SUM(op.quantity) AS quantity, op.current_price, p.product_name "
                "FROM order_products op JOIN products p ON op.product_id = p.id WHERE op.order_id = ? "
                "GROUP BY op.product_id ORDER BY p.product_type_id, p.price) WHERE quantity > 0",
                (order["id"],)
            )
            order_products[order["id"]] = products
            total = sum(p["quantity"] * p["current_price"] for p in order_products[order["id"]])
            order["total"] = total
        return order_products

    def get_pending_orders(self):
        """Retrieves all orders with a 'pending' status."""
        return self._fetchall_query("SELECT * FROM orders WHERE order_status = 'pending' ORDER BY id DESC")

    def get_order(self, order_id):
        """Retrieves a single order by its ID."""
        return self._fetchall_query("SELECT * FROM orders WHERE id = ?", (order_id,))

    def update_order(self, order_id, customer, table):
        """Updates the customer name and table number for a specific order."""
        self._execute_query("UPDATE orders SET customer_name = ?, table_number = ? WHERE id = ?", (customer, table, order_id))

    def get_order_status(self, order_id):
        """Retrieves the status of a single order by its ID."""
        return self._fetchall_query("SELECT order_status FROM orders WHERE id = ?", (order_id,))

    def delete_order_products(self, order_id):
        """Deletes all products associated with a specific order."""
        self._execute_query("DELETE FROM order_products WHERE order_id = ?", (order_id,))

    def delete_order_increments(self, order_id):
        """Deletes all increments associated with a specific order."""
        self._execute_query("DELETE FROM order_increments WHERE order_id = ?", (order_id,))

    def delete_order(self, order_id):
        """Deletes a single order by its ID."""
        self._execute_query("DELETE FROM orders WHERE id = ?", (order_id,))

    def update_order_status(self, order_id, status):
        """Updates the status of a specific order (e.g., 'pending', 'completed')."""
        self._execute_query("UPDATE orders SET order_status = ? WHERE id = ?", (status, order_id))

    def get_date_since(self, date_range):
        """Calculates a date based on a given range of days from the current timestamp."""
        row = self._fetchone_query("SELECT DATE(DATETIME(current_timestamp, '-3 hours'), '-' || ? || ' days') AS date", (date_range,))
        return row['date'] if row else None

    def get_completed_orders_since(self, since_date):
        """Retrieves all completed orders from a specific date forward."""
        return self._fetchall_query(
            "SELECT *, DATETIME(order_time, '-3 hours') AS order_timef FROM orders "
            "WHERE order_timef >= ? AND order_status = 'completed' ORDER BY order_time DESC",
            (since_date,)
        )

    def get_all_completed_orders(self):
        """Retrieves all orders with a 'completed' status."""
        return self._fetchall_query(
            "SELECT *, DATETIME(order_time, '-3 hours') AS order_timef FROM orders "
            "WHERE order_status = 'completed' ORDER BY order_time DESC"
        )

    def get_product_types(self):
        """Retrieves all active product types with at least one active product."""
        return self._fetchall_query("SELECT * FROM product_types pt "
                                   "WHERE EXISTS (SELECT 1 FROM products p WHERE p.product_type_id = pt.id AND p.product_status = 'active') "
                                   "AND type_status = 'active'")

    def get_products_by_type(self, type_id):
        """Retrieves all (active) products belonging to a specific product type."""
        return self._fetchall_query("SELECT * FROM products WHERE product_type_id = ? AND product_status = 'active'", (type_id,))

    def get_user_by_username(self, username):
        """Retrieves a single user by their username."""
        return self._fetchall_query("SELECT * FROM users WHERE username = ?", (username,))

    def get_active_product_types(self):
        """Retrieves all product types with an 'active' status."""
        return self._fetchall_query("SELECT * FROM product_types WHERE type_status = 'active'")

    def get_inactive_product_types(self):
        """Retrieves all product types with an 'inactive' status or with inactive products"""
        return self._fetchall_query("SELECT * FROM product_types pt WHERE type_status = 'inactive' "
                                   "OR EXISTS (SELECT 1 FROM products p WHERE p.product_type_id = pt.id AND p.product_status = 'inactive')")

    def get_inactive_products_by_type(self, type_id):
        """Retrieves all products that are inative or from an inactive type by a type"""
        return self._fetchall_query("SELECT * FROM products p WHERE product_status = 'inactive' "
                                   "OR EXISTS (SELECT 1 FROM product_types pt "
                                   "WHERE p.product_type_id = ? AND pt.type_status = 'inactive')",
                                   (type_id,))

    def get_inactive_products_by_active_type(self, type_id):
        """Retrieves all inactive products of a specific active product type."""
        return self._fetchall_query(
            "SELECT * FROM products WHERE product_type_id = ? AND product_status = 'inactive' ORDER BY price",
            (type_id,)
        )

    def get_all_products_by_inactive_type(self, type_id):
        """Retrieves all products of a specific inactive product type."""
        return self._fetchall_query("SELECT * FROM products WHERE product_type_id = ? ORDER BY price", (type_id,))

    def get_product_by_id(self, product_id):
        """Retrieves a single product by its ID."""
        return self._fetchall_query("SELECT * FROM products WHERE id=?", (product_id,))

    def get_product_type_by_id(self, product_type_id):
        """Retrieves a single product type by its ID."""
        return self._fetchall_query("SELECT id FROM product_types WHERE id = ?", (product_type_id,))

    def update_product(self, name, price, type_id, status, product_id):
        """Updates the details of a specific product."""
        self._execute_query(
            "UPDATE products SET product_name = ?, price = ?, product_type_id = ?, product_status = ? WHERE id = ?",
            (name, price, type_id, status, product_id)
        )

    def get_full_product_type_by_id(self, product_type_id):
        """Retrieves a single product type with all its details by its ID."""
        return self._fetchall_query("SELECT * FROM product_types WHERE id = ?", (product_type_id,))

    def update_product_type(self, name, status, type_id):
        """Updates the name and status of a specific product type."""
        self._fetchall_query("UPDATE product_types SET type_name = ?, type_status = ? WHERE id = ?", (name, status, type_id))

    def create_product(self, name, price, type_id):
        """Creates a new product in the database."""
        self._execute_query("INSERT INTO products (product_name, price, product_type_id) VALUES (?, ?, ?)", (name, price, type_id))

    def create_product_type(self, type_name):
        """Creates a new product type in the database."""
        self._execute_query("INSERT INTO product_types (type_name) VALUES (?)", (type_name,))

    def create_order(self, user_id, customer_name, table_number):
        """Creates a new order and returns the new order's ID."""
        return self._execute_query(
            "INSERT INTO orders (user_id, customer_name, table_number) VALUES (?, ?, ?)",
            (user_id, customer_name, table_number)
        )

    def get_order_total(self, order_id):
        """Calculates and returns the total cost of a specific order."""
        row = self._fetchone_query("SELECT SUM(current_price * quantity) AS total FROM order_products WHERE order_id = ?", (order_id,))
        return row['total'] if row else 0

    def get_order_username(self, order_id):
        """Retrieves the username of the user who created a specific order."""
        row = self._fetchone_query("SELECT username FROM users WHERE id IN (SELECT user_id FROM orders WHERE id = ?)", (order_id,))
        return row['username'] if row else None

    def get_order_time(self, order_id):
        """Retrieves the creation time of a specific order."""
        row = self._fetchone_query("SELECT DATETIME(order_time, '-3 hours') as order_time FROM orders WHERE id = ?", (order_id,))
        return row['order_time'] if row else None

    def get_order_increments(self, order_id):
        """Retrieves all increments for a specific order."""
        return self._fetchall_query(
            "SELECT oi.id AS id, u.username, DATETIME(oi.increment_time, '-3 hours') AS increment_time "
            "FROM order_increments oi JOIN users u ON oi.user_id = u.id WHERE oi.order_id = ? "
            "ORDER BY oi.increment_time DESC",
            (order_id,)
        )

    def get_increment_products(self, increment_id, order_id):
        """Retrieves all products associated with a specific order increment."""
        return self._fetchall_query(
            "SELECT op.product_id, op.quantity, op.current_price, p.product_name "
            "FROM order_products op JOIN products p ON op.product_id = p.id "
            "WHERE op.order_increment_id = ? AND op.order_id = ? "
            "ORDER BY p.product_type_id, op.current_price",
            (increment_id, order_id)
        )

    def get_increment_total(self, increment_id):
        """Calculates and returns the total cost of a specific order increment."""
        row = self._fetchone_query("SELECT SUM(quantity * current_price) AS total FROM order_products WHERE order_increment_id = ?", (increment_id,))
        return row['total'] if row else 0

    def create_user(self, username, password_hash):
        """Creates a new user with a username and hashed password."""
        self._execute_query("INSERT INTO users (username, hash) VALUES (?, ?)", (username, password_hash))

    def get_user_id_by_username(self, username):
        """Retrieves the ID of a user by their username."""
        row = self._fetchone_query("SELECT id FROM users WHERE username = ?", (username,))
        return row['id'] if row else None

    def get_today(self):
        return self._fetchone_query("SELECT DATE(DATETIME(current_timestamp, '-3 hours')) 'today'")["today"]

    def get_sales_report(self, start_date, end_date):
        """Returns the total sales in the period and the sold products"""
        sales = self._fetchone_query("SELECT SUM(op.current_price * op.quantity) total "
                                     "FROM order_products op "
                                     "WHERE op.order_id "
                                     "IN (SELECT orders.id FROM orders "
                                     "WHERE orders.order_status = 'completed' "
                                     "AND order_time "
                                     "BETWEEN DATETIME(?, '-3 hours') "
                                     "AND DATETIME(?, '-3 hours'))",
                                     (start_date, end_date))
        return sales

db = Database("./database/limas.db")
