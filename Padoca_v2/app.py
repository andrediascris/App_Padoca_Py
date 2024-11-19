from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  address TEXT NOT NULL)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  price REAL NOT NULL,
                  description TEXT)''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  date TEXT NOT NULL,
                  status TEXT NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
                  
    c.execute('''CREATE TABLE IF NOT EXISTS order_items
                 (order_id INTEGER,
                  product_id INTEGER,
                  quantity INTEGER,
                  FOREIGN KEY (order_id) REFERENCES orders (id),
                  FOREIGN KEY (product_id) REFERENCES products (id))''')
    
    conn.commit()
    conn.close()

# User routes
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (name, email, address) VALUES (?, ?, ?)',
                 (data['name'], data['email'], data['address']))
        conn.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already exists'}), 400
    finally:
        conn.close()

@app.route('/users/<int:user_id>', methods=['PUT'])
def edit_user(user_id):
    data = request.get_json()
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('UPDATE users SET name=?, email=?, address=? WHERE id=?',
             (data['name'], data['email'], data['address'], user_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User updated successfully'})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def remove_user(user_id):
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'User deleted successfully'})

@app.route('/users', methods=['GET'])
def list_users():
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = [{'id': row[0], 'name': row[1], 'email': row[2], 'address': row[3]} 
             for row in c.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/users/addresses', methods=['GET'])
def list_user_addresses():
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('SELECT id, name, address FROM users')
    addresses = [{'id': row[0], 'name': row[1], 'address': row[2]} 
                for row in c.fetchall()]
    conn.close()
    return jsonify(addresses)

# Product routes
@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('INSERT INTO products (name, price, description) VALUES (?, ?, ?)',
             (data['name'], data['price'], data['description']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product created successfully'}), 201

@app.route('/products/<int:product_id>', methods=['PUT'])
def edit_product(product_id):
    data = request.get_json()
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('UPDATE products SET name=?, price=?, description=? WHERE id=?',
             (data['name'], data['price'], data['description'], product_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product updated successfully'})

@app.route('/products/<int:product_id>', methods=['DELETE'])
def remove_product(product_id):
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('DELETE FROM products WHERE id=?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted successfully'})

@app.route('/products', methods=['GET'])
def list_products():
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('SELECT * FROM products')
    products = [{'id': row[0], 'name': row[1], 'price': row[2], 'description': row[3]} 
               for row in c.fetchall()]
    conn.close()
    return jsonify(products)

# Order routes
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('INSERT INTO orders (user_id, date, status) VALUES (?, ?, ?)',
             (data['user_id'], datetime.now().isoformat(), 'pending'))
    order_id = c.lastrowid
    
    for item in data['items']:
        c.execute('INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)',
                 (order_id, item['product_id'], item['quantity']))
    
    conn.commit()
    conn.close()
    return jsonify({'message': 'Order created successfully', 'order_id': order_id}), 201

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def remove_order(order_id):
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('DELETE FROM order_items WHERE order_id=?', (order_id,))
    c.execute('DELETE FROM orders WHERE id=?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Order deleted successfully'})

@app.route('/orders/<int:order_id>/items', methods=['POST'])
def add_order_item(order_id):
    data = request.get_json()
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)',
             (order_id, data['product_id'], data['quantity']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Item added to order successfully'})

@app.route('/users/<int:user_id>/orders', methods=['GET'])
def list_user_orders(user_id):
    conn = sqlite3.connect('bakery.db')
    c = conn.cursor()
    c.execute('''
        SELECT o.id, o.date, o.status, 
               oi.product_id, p.name, oi.quantity, p.price
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = ?
    ''', (user_id,))
    
    orders = {}
    for row in c.fetchall():
        order_id = row[0]
        if order_id not in orders:
            orders[order_id] = {
                'id': order_id,
                'date': row[1],
                'status': row[2],
                'items': []
            }
        orders[order_id]['items'].append({
            'product_id': row[3],
            'product_name': row[4],
            'quantity': row[5],
            'price': row[6]
        })
    
    conn.close()
    return jsonify(list(orders.values()))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)