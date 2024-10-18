import requests
import sqlitecloud
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_cors import CORS

app = Flask(__name__)
DATABASE = 'product_inventory.db'  # SQLite database file

# Connect to SQLite Database
def connect_to_db():
    conn = sqlitecloud.connect('sqlitecloud://criv3i7ihz.sqlite.cloud:8860/product_inventory.db?apikey=DRXXstsAS0AmGvWIOYvjZCCE5wJDBPyxjdPe4rQRayk')
    # db_name = DATABASE
    return conn


# Home route
@app.route('/')
def home():
    return render_template('index.html')




# Product Route
@app.route('/products', methods=['GET'])
def products():
    # Delete products with 0 total quantity and marked as open quantity
    delete_zero_quantity_products()

    # Fetch updated product list
    products = fetch_all_products()
    return render_template('products.html', products=products)


#Refresh Route
@app.route('/refresh', methods=['POST'])
def refresh():
    # Redirect to the products page to refresh the data
    return redirect(url_for('products'))




def delete_zero_quantity_products():
    # Your database logic to delete products with total quantity and marked open quantity equal to 0
    # Example (pseudocode):
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE total_quantity = 0 AND mark_open_count = 0")
    conn.commit()
    conn.close()




# Create the Products Table
def create_table():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        total_quantity INTEGER NOT NULL,
        unit TEXT CHECK(unit IN ('kg', 'packs', 'litres')) NOT NULL,
        expiry_date DATE NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

# Function to Insert Product Data Route
@app.route('/add_product', methods=['POST'])
def insert_product():

    data = request.form
    name = data['name']
    total_quantity = data['total_quantity']
    unit = data['unit']
    expiry_date = data['expiry_date']

    conn = connect_to_db()
    cursor = conn.cursor()
    sql = "INSERT INTO products (name, total_quantity, unit, expiry_date) VALUES (?, ?, ?, ?)"
    values = (name, total_quantity, unit, expiry_date)

    cursor.execute(sql, values)
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


# Function to Fetch All Products
def fetch_all_products():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    return products


# Creating Shopping Cart List Table
def create_shopping_table():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shopping_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        total_quantity INTEGER NOT NULL,
        unit TEXT CHECK(unit IN ('kg', 'packs', 'litres')) NOT NULL,
        status TEXT NOT NULL DEFAULT 'not_done'
    )
    ''')
    conn.commit()
    conn.close()


# Function to fetch shopping list items
def fetch_shopping_list():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM shopping_list')
    items = cursor.fetchall()
    conn.close()
    return items


# Shopping List Route
@app.route('/shopping_list', methods=['GET'])
def shopping_list():
    items = fetch_shopping_list()
    return render_template('shopping_list.html', items=items)


# Add Item to Shopping List Route
@app.route('/add_item', methods=['POST'])
def add_item():
    name = request.form['item_name']
    total_quantity = request.form['quantity']
    unit = request.form['unit']
    
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO shopping_list (name, total_quantity, unit, status) VALUES (?, ?, ?, ?)', (name, total_quantity, unit, 'not_done'))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Item added successfully!'})



# Mark as Done Route
@app.route('/update_item_status', methods=['POST'])
def update_item_status():
    item_index = request.form['index']
    status = request.form['status']

    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE shopping_list SET status = ? WHERE id = ?', (status, item_index))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Item status updated successfully!'})



# Delete Item Route
@app.route('/delete_item', methods=['POST'])
def delete_item():
    item_name = request.form['item_name']
    
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM shopping_list WHERE name = ?', (item_name,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Item deleted successfully!'})

# Add Item to Stock Route
@app.route('/add_item_to_stock', methods=['POST'])
def add_item_to_stock():
    item_name = request.form['item_name']
    quantity = request.form['quantity']
    unit = request.form['unit']
    expiry_date = request.form['expiry_date']

    conn = connect_to_db()
    cursor = conn.cursor()

    # Move the item to the products table
    cursor.execute('INSERT INTO products (name, total_quantity, unit, expiry_date) VALUES (?, ?, ?, ?)', 
                   (item_name, quantity, unit, expiry_date))
    cursor.execute('DELETE FROM shopping_list WHERE name = ?', (item_name,))

    conn.commit()
    conn.close()
    return jsonify(message=f'Added {item_name} to stock.')


# Expired Products Route
@app.route('/expired_products', methods=['GET'])
def expired_products():
    products_list = fetch_expired_products()
    return render_template('expired_products.html', products=products_list)



# Function to Fetch Expired Products
def fetch_expired_products():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE expiry_date < DATE('now') ORDER BY expiry_date ASC")
    products = cursor.fetchall()
    conn.close()
    return products


# Near to Expiry Products Route
@app.route('/near_expiry', methods=['GET'])
def near_expiry():
    products_list = fetch_near_expiry_products()
    return render_template('near_expiry.html', products=products_list)


# Function to Fetch Products Near Expiry
def fetch_near_expiry_products():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM products 
        WHERE expiry_date BETWEEN DATE('now') AND DATE('now', '+3 days')
        ORDER BY expiry_date ASC
    """)
    products = cursor.fetchall()
    conn.close()
    return products


# Create the products table
create_table()



# For Consume 1 Pack Button Route
@app.route('/consume/<int:product_id>', methods=['POST'])
def consume_product(product_id):
    conn = connect_to_db()
    cursor = conn.cursor()

    # Decrease the total_quantity by 1
    cursor.execute("UPDATE products SET total_quantity = total_quantity - 1 WHERE id = ? AND total_quantity > 0", (product_id,))
    conn.commit()

    # Fetch updated product details
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    return jsonify({'status': 'success', 'product': product})




# For Consume All Button Route
@app.route('/consume_all/<int:product_id>', methods=['POST'])
def consume_all_product(product_id):
    conn = connect_to_db()
    cursor = conn.cursor()

    # Update total_quantity to 0 and mark_open_count to 0
    cursor.execute("UPDATE products SET total_quantity = 0, mark_open_count = 0 WHERE id = ?", (product_id,))
    conn.commit()

    # Fetch updated product details
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    return jsonify({'status': 'success', 'product': product})




# For Mark as Open Button Route
@app.route('/mark_open/<int:product_id>', methods=['POST'])
def mark_open_product(product_id):
    conn = connect_to_db()
    cursor = conn.cursor()

    # Update total_quantity and mark_open_count
    cursor.execute("UPDATE products SET total_quantity = total_quantity - 1, mark_open_count = mark_open_count + 1 WHERE id = ? AND total_quantity > 0", (product_id,))
    conn.commit()

    # Fetch updated product details
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    return jsonify({'status': 'success', 'product': product})



# Recipe Route
@app.route('/recipe/<int:product_id>', methods=['GET'])
def recipe(product_id):
    # Fetch product details using the product_id
    product = get_product_details(product_id)
    print(f"Fetching recipes for ingredient: {product}")
    
    if not product:
        return "Product not found", 404

    ingredient = product[1]  # Assuming product name is used as the ingredient
    recipes = fetch_indian_recipes(ingredient)

    return render_template('recipe.html', product=product, recipes=recipes)


# Recipe Fetching Function
def fetch_indian_recipes(ingredient):
    EDAMAM_APP_ID = 'e9dbea10'
    EDAMAM_APP_KEY = '4ea0174c8d96f2b1d0e15683d4374ca4'
    
    url = f'https://api.edamam.com/search?q={ingredient}&cuisineType=Indian&app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}'
    response = requests.get(url)
    data = response.json()
    print(data)  # Log the API response
    
    if response.status_code == 200:
        return response.json()['hits']
    else:
        return []



# Overview Route
@app.route('/overview/<int:product_id>', methods=['GET'])
def overview(product_id):
    # Fetch product details using the product_id
    product = get_product_details(product_id)  # You need to implement this function

    if not product:
        return "Product not found", 404

    return render_template('overview.html', product=product)


# Overview Function
def get_product_details(product_id):
    conn = connect_to_db()  # Adjust your database connection
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()

    conn.close()
    return product




    





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)  # Make sure to bind to 0.0.0.0
