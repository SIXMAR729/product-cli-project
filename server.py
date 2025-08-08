import grpc
import sqlite3
import uuid
import json
from concurrent import futures
from contextlib import contextmanager

import order_api_pb2
import order_api_pb2_grpc
from google.protobuf import empty_pb2

DATABASE_NAME = "orders.db"

class Database:
    """Manages all database operations for the API."""
    def __init__(self, db_name):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                description TEXT, price REAL NOT NULL
            )""")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
                status INTEGER NOT NULL, total_amount REAL NOT NULL
            )""")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL,
                product_id TEXT NOT NULL, quantity INTEGER NOT NULL, price_per_item REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            )""")

    @contextmanager
    def _get_connection(self):
        """A context manager to handle database connections safely."""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # --- Product Methods ---
    def create_product(self, name, description, price):
        product_id = "prod-" + str(uuid.uuid4())[:8]
        with self._get_connection() as conn:
            conn.execute("INSERT INTO products (product_id, name, description, price) VALUES (?, ?, ?, ?)",
                         (product_id, name, description, price))
        return self.get_product(product_id)

    def get_product(self, product_id):
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()

    def update_product(self, product_id, name, description, price):
        with self._get_connection() as conn:
            cursor = conn.execute("UPDATE products SET name=?, description=?, price=? WHERE product_id=?",
                                  (name, description, price, product_id))
            if cursor.rowcount == 0:
                return None
        return self.get_product(product_id)

    def delete_product(self, product_id):
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
            conn.commit()  
        return cursor.rowcount > 0

    def list_products(self):
        with self._get_connection() as conn:
            return conn.execute("SELECT * FROM products").fetchall()

    def count_products(self):
        with self._get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    def export_products(self):
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM products").fetchall()
            return json.dumps([dict(row) for row in rows], indent=2)

    # --- Order Methods ---
    def create_order(self, user_id, items):
        order_id = "order-" + str(uuid.uuid4())[:8]
        total_amount = sum(item.quantity * item.price_per_item for item in items)
        with self._get_connection() as conn:
            conn.execute("INSERT INTO orders (order_id, user_id, status, total_amount) VALUES (?, ?, ?, ?)",
                           (order_id, user_id, order_api_pb2.Order.PENDING, total_amount))
            for item in items:
                conn.execute("INSERT INTO order_items (order_id, product_id, quantity, price_per_item) VALUES (?, ?, ?, ?)",
                               (order_id, item.product_id, item.quantity, item.price_per_item))
        return self.get_order(order_id)

    def get_order(self, order_id):
        with self._get_connection() as conn:
            order_data = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
            if not order_data:
                return None, []
            items_data = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
            return order_data, items_data
    
    def update_order_status(self, order_id, new_status):
        with self._get_connection() as conn:
            cursor = conn.execute("UPDATE orders SET status=? WHERE order_id=?", (new_status, order_id))
            if cursor.rowcount == 0:
                return None, []
        return self.get_order(order_id)
        
    def count_orders(self):
        with self._get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    def export_orders(self):
        with self._get_connection() as conn:
            orders_rows = conn.execute("SELECT * FROM orders").fetchall()
            items_rows = conn.execute("SELECT * FROM order_items").fetchall()
        
        orders_list = []
        for order_row in orders_rows:
            order_dict = dict(order_row)
            order_dict['items'] = [dict(item_row) for item_row in items_rows if item_row['order_id'] == order_dict['order_id']]
            orders_list.append(order_dict)
        return json.dumps(orders_list, indent=2)

class ProductServiceServicer(order_api_pb2_grpc.ProductServiceServicer):
    def __init__(self, db):
        self.db = db

    def CreateProduct(self, request, context):
        row = self.db.create_product(request.name, request.description, request.price)
        return order_api_pb2.Product(**row)

    def GetProduct(self, request, context):
        row = self.db.get_product(request.product_id)
        if not row:
            context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details("Product not found.")
            return order_api_pb2.Product()
        return order_api_pb2.Product(**row)

    def UpdateProduct(self, request, context):
        row = self.db.update_product(request.product_id, request.name, request.description, request.price)
        if not row:
            context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details("Product not found to update.")
            return order_api_pb2.Product()
        return order_api_pb2.Product(**row)

    def DeleteProduct(self, request, context):
        success = self.db.delete_product(request.product_id)
        return order_api_pb2.DeleteProductResponse(success=success)

    def ListProducts(self, request, context):
        for row in self.db.list_products():
            yield order_api_pb2.Product(**row)

    def CountProducts(self, request, context):
        count = self.db.count_products()
        return order_api_pb2.CountResponse(count=count)
    
    def ExportProducts(self, request, context):
        json_data = self.db.export_products()
        return order_api_pb2.ExportResponse(json_data=json_data)

class OrderServiceServicer(order_api_pb2_grpc.OrderServiceServicer):
    def __init__(self, db):
        self.db = db

    def CreateOrder(self, request, context):
        order_row, item_rows = self.db.create_order(request.user_id, request.items)
        items = [order_api_pb2.Order.Item(**item) for item in item_rows]
        return order_api_pb2.Order(**order_row, items=items)

    def GetOrder(self, request, context):
        order_row, item_rows = self.db.get_order(request.order_id)
        if not order_row:
            context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details("Order not found.")
            return order_api_pb2.Order()
        items = [order_api_pb2.Order.Item(**item) for item in item_rows]
        return order_api_pb2.Order(**order_row, items=items)

    def UpdateOrderStatus(self, request, context):
        order_row, item_rows = self.db.update_order_status(request.order_id, request.new_status)
        if not order_row:
            context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details("Order not found to update.")
            return order_api_pb2.Order()
        items = [order_api_pb2.Order.Item(**item) for item in item_rows]
        return order_api_pb2.Order(**order_row, items=items)
        
    def CountOrders(self, request, context):
        count = self.db.count_orders()
        return order_api_pb2.CountResponse(count=count)

    def ExportOrders(self, request, context):
        json_data = self.db.export_orders()
        return order_api_pb2.ExportResponse(json_data=json_data)

def serve():
    db = Database(DATABASE_NAME)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    order_api_pb2_grpc.add_ProductServiceServicer_to_server(ProductServiceServicer(db), server)
    order_api_pb2_grpc.add_OrderServiceServicer_to_server(OrderServiceServicer(db), server)
    
    server.add_insecure_port('[::]:50051')
    server.start()
    print("✅ Server started. Listening on port 50051.")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()