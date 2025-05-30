from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, brl, login_required
import preferences
# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["brl"] = brl

# Configure session to use filesystem (instead of signed cookies)
# TODO: Understand what this means
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure the cs50 lib to use the database
db = SQL("sqlite:///database/limas.db")

# TODO: understand what this means
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Create a order increment and add the products in the order_products table
def add_order_products(order_id, increment_products):
    if len(increment_products) == 0:
        return
    order_increment_id = db.execute("INSERT INTO order_increments "
    "(order_id, user_id) VALUES (?, ?)", order_id, session["user_id"])
    for product in increment_products:
        price = db.execute("SELECT price FROM products WHERE id = ?",
                           product["id"])[0]["price"]
        db.execute("INSERT INTO order_products "
                   "(order_id, product_id, order_increment_id, "
                   "quantity, current_price)"
                   "VALUES (?, ?, ?, ?, ?)",
                   order_id, product["id"], order_increment_id,
                   product["quantity"], price)
    return
# When receiving a list of orders, returns the products of those orders
def list_products(orders):
    # Create a dictionary of lists of products with each key being the order id
    order_products = {}
    for order in orders:
        order_products[order["id"]] = db.execute(
            "SELECT * FROM "
            "(SELECT order_products.product_id AS id, "
            "SUM(quantity) AS quantity, current_price, "
            "products.product_name FROM order_products JOIN products "
            "ON order_products.product_id = products.id WHERE order_id = ? "
            "GROUP BY order_products.product_id "
            "ORDER BY products.product_type_id, price) WHERE quantity > 0",
            order["id"])
        total = 0
        for product in order_products[order["id"]]:
            total += product.get("quantity") * product.get("current_price")
        order["total"] = total
    return order_products


@app.route("/")
@login_required
def index():
    # Request the list of pending orders and the list of products
    pending_orders = db.execute("SELECT * FROM orders "
                                "WHERE order_status = 'pending' "
                                "ORDER BY id DESC")
    order_products = list_products(pending_orders)
    return render_template("index.html",
                            orders=pending_orders, 
                            order_products=order_products)


@app.route("/edit-order", methods=["GET", "POST"])
@login_required
def edit_order():
    # User reached route via POST
    if request.method == "POST":
        order_id = request.form.get("order-id")
        customer = request.form.get("customer")
        table = request.form.get("table-number")
        # Check if the table number is valid
        if table:
            if not table.isnumeric():
                return apology("Número de mesa inválido")
        increment_products = []
        intended_products = {}
        # Request the order from the database
        order = db.execute("SELECT * FROM orders WHERE id = ?", order_id)
        if len(order) != 1:
            return apology("Não foi possível encontrar o pedido")
        # Request the list of the actual products
        actual_products = list_products(order)[int(order_id)]
        # Populates the intended products list
        for actual_product in actual_products:
            if request.form.get(str(actual_product["id"])):
                if request.form.get(str(actual_product["id"])).isnumeric():
                    intended_products[actual_product["id"]] = (
                    int(request.form.get(str((actual_product["id"])))))
                else:
                    intended_products[actual_product["id"]] = 0
        # Populates the increment_products list
        for actual_product in actual_products:
            if type(intended_products.get(actual_product["id"])) != None:
                quantity = (intended_products[actual_product["id"]] -
                            int(actual_product["quantity"]))
                if quantity != 0:
                    increment_products.append({"id": actual_product["id"],
                                               "quantity": quantity})
        db.execute("UPDATE orders SET customer_name = ?, table_number = ? "
                   "WHERE id = ?", customer, table, order_id)
        add_order_products(order_id, increment_products)
        flash(f"Pedido Nº.{order_id} editado com sucesso")
        return redirect("/")
    # User reached route via GET
    else:
        order_id = request.args.get("order-id")
        order = db.execute("SELECT * FROM orders WHERE id = ?", order_id)
        if len(order) != 1:
            return apology("Pedido não encontrado")
        order_products = list_products(order)
        return render_template("edit-order.html", order=order[0],
                               order_products=order_products[int(order_id)])

@app.route("/modify-order-status", methods=["POST"])
@login_required
def delete_order():
    order_id = request.form.get("order-id")
    order = db.execute("SELECT order_status FROM orders WHERE id = ?",
                       order_id)
    if len(order) != 1:
        return apology("Não foi possível encontrar o pedido")
    order = order[0]
    action = request.form.get("action")
    if action == "delete":
        db.execute("DELETE FROM order_products WHERE order_id = ?", order_id)
        db.execute("DELETE FROM order_increments WHERE order_id = ?", order_id)
        db.execute("DELETE FROM orders WHERE id = ?", order_id)
        flash(f"Pedido Nº.{order_id} apagado com sucesso")
        return redirect("/")
    if action == "complete":
        try:
            db.execute("UPDATE orders "
                       "SET order_status = 'completed' WHERE id = ?", 
                       order_id)
            flash(f"Pedido N.º {order_id} "
                    "completado com sucesso")
        except:
            return apology("Algo deu errado com a mudança do status do pedido")
        return redirect("/")
    if action == "reopen":
        try:
            db.execute("UPDATE orders SET order_status = 'pending' WHERE id = ?", order_id)
        except:
            return apology("Não foi possível reabrir o pedido")
        flash(f"Pedido Nº.{order_id} reaberto com sucesso")
        return redirect("/")

@app.route("/history")
@login_required
def history():
    if request.args:
        total_sold = 0
        date_range = request.args.get("date-range")
        if date_range.isdigit():
            since_date = db.execute("SELECT DATE("
                                    "DATETIME(current_timestamp, '-3 hours'), "
                                    "'-' || ? || ' days') "
                                    "AS date",
                                    date_range)[0]["date"]
            orders = db.execute("SELECT *, DATETIME(order_time, '-3 hours') "
                                "AS order_timef "
                                "FROM orders "
                                "WHERE order_timef >= ? "
                                "AND order_status = 'completed' "
                                "ORDER BY order_time DESC", since_date)
        else:
            orders = db.execute("SELECT *, DATETIME(order_time, '-3 hours') "
                                "AS order_timef FROM orders "
                                "WHERE order_status = 'completed' "
                                "ORDER BY order_time DESC")
            since_date = "Sempre"
        order_products = list_products(orders)
        total_sold = 0
        for order in orders:
            total_sold += order["total"]

        return render_template("history.html", orders=orders,
                               order_products=order_products,
                               total=total_sold, since=since_date)
    else:
        return render_template("query-history.html")

@app.route("/increment-order", methods=["GET", "POST"])
@login_required
def increment_order():
    # User reached route via POST
    if request.method == "POST":
        order_id = request.form.get("order-id")
        if not order_id or not order_id.isnumeric():
            print(f"O id do pedido não foi reconhecido id: {order_id}")
            return apology("Não foi possível receber o id do pedido")

        # Append each ordered product to the order_products list
        increment_products = []
        try:
            for product in request.form:
                if product.isnumeric() and request.form.get(product).isnumeric():
                    if int(request.form.get(product)) > 0:
                        increment_products.append({"id": int(product), 
                                                   "quantity": int(request.form
                                                                   .get(product))})
        except:
            return apology("Não foi possível registrar o produto")

        add_order_products(order_id, increment_products)
        flash(f"Pedido Nº.{order_id} incrementado com sucesso")
        return redirect("/")

    # User reached route via GET
    else:
        order_id = request.args.get("order-id")
        order = db.execute("SELECT * FROM orders WHERE id = ?", order_id)
        if len(order) != 1:
            return apology("Pedido não encontrado")
        product_types = db.execute("SELECT * FROM product_types")
        products = []
        for type in product_types:
            products.append({"type": type["type_name"],
                             "products": db.execute("SELECT id, product_name, "
                                                    "price FROM products "
                                                    "WHERE product_type_id = ?",
                                                    type["id"])})
        order=order[0]
        return render_template("increment-order.html", products=products,
                               order=order, order_id=order_id)



@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("user_id"):
        # Clear the user session
        session.clear()

    # User reached route via POST:
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Verify if the username, password and confirmation were submited
        if not username:
            flash("Digite um nome de usuário")
            return redirect("/login")
        if not password:
            flash("Digite uma senha")
            return redirect("/login")

        # Verifies if the user exist and password matches
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(user) != 1 or not check_password_hash(
            user[0]["hash"], request.form.get("password")
        ):
            flash("Usuário ou senha incorretos")
            return redirect("/login")

        # If password hash matches, logs the user
        session["user_id"] = user[0]["id"]
        flash("Logado com sucesso!")
        return redirect("/")
    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/manage/<status>")
@app.route("/manage", defaults={"status": "active"})
@login_required
def manage(status):
    # TODO: User can edit active products of inactive product types
    # WORKING on
    if status == "active": 
        product_types = db.execute("SELECT * FROM product_types "
                                "WHERE type_status = 'active'")
        for c in range(len(product_types)):
            product_types[c]["products"] = db.execute("SELECT * "
                                                    "FROM products "
                                                    "WHERE product_type_id = ? "
                                                    "AND product_status "
                                                    "= 'active' "
                                                    "ORDER BY price",
                                                    product_types[c]["id"])
        return render_template("manage.html", product_types=product_types, status=status)
    elif status == "inactive":
        product_types = db.execute("SELECT * FROM product_types")
        for c in range(len(product_types)):
            if product_types[c]["type_status"] == "active":
                product_types[c]["products"] = db.execute("SELECT * "
                                                        "FROM products "
                                                        "WHERE product_type_id = ? "
                                                        "AND product_status "
                                                        "= 'inactive' "
                                                        "ORDER BY price",
                                                        product_types[c]["id"])
            elif product_types[c]["type_status"] == "inactive":
                product_types[c]["products"] = db.execute("SELECT * "
                                                        "FROM products "
                                                        "WHERE product_type_id = ? "
                                                        "ORDER BY price",
                                                        product_types[c]["id"])
        return render_template("manage.html", product_types=product_types, status=status)


@app.route("/manage/edit", methods=["GET", "POST"])
@login_required
def manage_edit():
    """Edit a product or product type"""
    if request.method == "POST":
        # A product id is given
        if request.form.get("product-id"):
            # Check if the product with given id exists
            product = db.execute("SELECT * FROM products "
                                 "WHERE id=?",
                                 request.form.get("product-id"))
            if len(product) != 1:
                return apology("Product was not found")
            product = product[0]
            new_values = {
                "name": request.form.get("product-name"),
                "price": request.form.get("product-price"),
                "type": request.form.get("product-type"),
                "status": request.form.get("product-status")
            }
            # Validate the new_values data
            if (not new_values["name"]
            or not new_values["price"].isnumeric() 
            or len(db.execute("SELECT id FROM product_types "
                              "WHERE id = ?",
                              new_values["type"])) != 1
            or not new_values["status"] in ["active", "inactive"]):
                return apology("Algum dos valores enviados são incompatíveis")
            try:
                db.execute("UPDATE products "
                        "SET product_name = ?, "
                        "price = ?, "
                        "product_type_id = ?, "
                        "product_status = ? "
                        "WHERE id = ?",
                        new_values["name"],
                        new_values["price"],
                        new_values["type"],
                        new_values["status"],
                        product["id"])   
            except Exception as exception:
                return apology(f"Não foi possível editar o produto\n{exception}")
            flash(f"Produto N.º{product["id"]} editado com sucesso")
            return redirect("/manage")
        # A product_type_id is given

        elif request.form.get("product-type-id"):
            # Check if the product_type with given id exists
            product_type = db.execute("SELECT * FROM product_types "
                                 "WHERE id = ?",
                                 request.form.get("product-type-id"))
            if len(product_type) != 1:
                return apology("Tipo de produto não encontrado")
            product_type = product_type[0]
            new_values = {
                "name": request.form.get("type-name"),
                "status": request.form.get("type-status")
            }
            # Validate the new_values data
            if (not new_values["name"]
            or not new_values["status"] in ["active", "inactive"]):
                return apology("Algum dos valores enviados são incompatíveis")
            try:
                db.execute("UPDATE product_types "
                        "SET type_name = ?, "
                        "type_status = ? "
                        "WHERE id = ?",
                        new_values["name"],
                        new_values["status"],
                        product_type["id"])   
            except Exception as exception:
                return apology(f"Não foi possível editar o tipo de produto\n{exception}")
            flash(f"Tipo de produto N.º{product_type["id"]} editado com sucesso")
            return redirect("/manage")

    # User reached route via GET
    else:
        # Serve page for editing a product
        if request.args.get("product-id"):
            product = db.execute("SELECT * FROM products "
                                 "WHERE id = ?",
                                 request.args.get("product-id"))
            if len(product) != 1:
                return apology("Produto não encontrado")
            product = product[0]
            product_types = db.execute("SELECT * FROM product_types "
                                       "WHERE type_status = 'active'")
            return render_template("edit-product.html",
                                   product=product,
                                   product_types=product_types)
        # Serve page for editing a product type
        elif request.args.get("product-type-id"):
            product_type = db.execute("SELECT * FROM product_types "
                                      "WHERE id = ?",
                                      request.args.get("product-type-id"))
            if len(product_type) != 1:
                return apology("Tipo de produto não encontrado")
            product_type = product_type[0]
            product_type["active_products"] = db.execute("SELECT COUNT(id) "
                                                         "FROM products "
                                                         "WHERE product_type_id = ? "
                                                         "AND product_status "
                                                         "= 'active'",
                                                         product_type["id"])
            return render_template("edit-product-type.html", product_type=product_type)


@app.route("/manage/new/product", methods=["GET", "POST"])
@login_required
def manage_new_product():
    if request.method == "POST":
        # User wants to create a new product
        new_values = {
            "name": request.form.get("product-name"),
            "price": request.form.get("product-price"),
            "type": request.form.get("product-type"),
        }
        # Validate the new_values data
        if (not new_values["name"]
        or not new_values["price"].isnumeric() 
        or len(db.execute("SELECT id FROM product_types "
                            "WHERE id = ?",
                            new_values["type"])) != 1):
            return apology("Algum dos valores enviados são incompatíveis")
        try:
            db.execute("INSERT INTO products "
                       "(product_name, price, product_type_id) "
                       "VALUES (?, ?, ?)",
                       new_values["name"],
                       new_values["price"],
                       new_values["type"])
        except Exception as exception:
            return apology(f"Não foi possível registar o produto: \n{exception}")
        flash(f"Produto registrado com sucesso")
        return redirect("/manage")
    # User reached route via get
    else:
        product_types = db.execute("SELECT * FROM product_types "
                                   "WHERE type_status = 'active'")
        return render_template("new-product.html", product_types=product_types)


@app.route("/manage/new/product-type", methods=["GET", "POST"])
@login_required
def manage_new_product_type():
    if request.method == "POST":
        # User wants to create a new product type
        type_name = request.form.get("type-name")

        # Validate the new_values data
        if not type_name:
            return apology("Insira um nome para o tipo de produto")
        try:
            db.execute("INSERT INTO product_types "
                       "(type_name) "
                       "VALUES (?)",
                       type_name)
        except Exception as exception:
            return apology(f"Não foi possível registar o tipo de produto: \n{exception}")
        flash(f"Tipo de produto registrado com sucesso")
        return redirect("/manage")
        # User reached route via get
    else:
        return render_template("new-product-type.html")

@app.route("/new-order", methods=["GET", "POST"])
@login_required
def new_order():
    """Register new orders"""
    if request.method == "POST":
        order_products = []
        # Append each ordered product to the order_products list
        try:
            for product in request.form:
                if product.isnumeric() and request.form.get(product).isnumeric():
                    if int(request.form.get(product)) > 0:
                        order_products.append({"id": int(product),
                                               "quantity": int(request.form
                                                               .get(product))})
        except:
            return apology("Não foi possível registrar o produto")
        customer = request.form.get("customer")
        table_number = request.form.get("table-number")

        # Register the order into the orders table
        order_id = db.execute("INSERT INTO orders "
                              "(user_id, customer_name, table_number) "
                              "VALUES (?, ?, ?)",
                              session["user_id"], customer, table_number)
        add_order_products(order_id, order_products)
        flash(f"Pedido N.º{order_id} registrado")
        return redirect("/")
    # User reached route via GET
    else:
        product_types = db.execute("SELECT * FROM product_types")
        products = []
        for type in product_types:
            products.append({"type": type["type_name"],
                             "products": db.execute("SELECT id, product_name, "
                             "price FROM products "
                             "WHERE product_type_id = ?", type["id"])})
        return render_template("new-order.html", products=products)

@app.route("/order-details")
@login_required
def order_details():
    order_id = request.args.get("order-id")
    order = db.execute("SELECT * FROM orders WHERE id = ?", order_id)
    if len(order) != 1:
        return apology("Pedido não encontrado")
    # list_products(order_id, order)
    order = order[0]
    details = {}
    details["total"] = db.execute("SELECT SUM(current_price * quantity) "
                                  "AS total FROM order_products WHERE "
                                  "order_id = ?", order_id)[0].get("total")
    details["username"] = db.execute("SELECT username FROM users WHERE id "
                                     "IN (SELECT user_id FROM orders "
                                     "WHERE id = ?)", 
                                     order_id)[0].get("username")
    details["time"] = db.execute("SELECT "
                                 "DATETIME(order_time, '-3 hours') "
                                 "as order_time FROM orders "
                                 "WHERE id = ?", 
                                 order_id)[0].get("order_time")
    details["status"] = db.execute("SELECT order_status "
                                   "FROM orders "
                                   "WHERE id = ?",
                                   order_id)[0].get("order_status")


    increments = db.execute("SELECT order_increments.id AS id, username, "
                            "DATETIME(increment_time, '-3 hours') "
                            "AS increment_time FROM order_increments "
                            "JOIN users "
                            "ON order_increments.user_id = "
                            "users.id WHERE order_id = ? "
                            "ORDER BY increment_time DESC", 
                            order_id)
    for i in range(len(increments)):
        increments[i]["products"] = db.execute("SELECT product_id, quantity, "
                                               "current_price, product_name "
                                               "FROM order_products "
                                               "JOIN products "
                                               "ON order_products.product_id = " 
                                               "products.id "
                                               "WHERE order_increment_id = ? " 
                                               "AND order_id = ? "
                                               "ORDER BY product_type_id, "
                                               "current_price", 
                                               increments[i]["id"], order_id)
        increments[i]["total"] = db.execute("SELECT "
                                            "SUM(quantity * current_price) "
                                            "AS total FROM order_products "
                                            "WHERE order_increment_id = ?",
                                            increments[i]["id"])[0].get("total")
    return render_template("order-details.html", order=order,
                           increments=increments, details=details)

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register new users"""
    if session.get("user_id"):
        # Clear the user session
        session.clear()
    # User reached route via POST:
    if request.method == "POST":
        if preferences.allow_new_users:
            username = request.form.get("username")
            password = request.form.get("password")
            confirmation = request.form.get("confirmation")
            # Verify if the username, password and confirmation were submited
            if not username:
                flash("Digite um nome de usuário")
                return redirect("/register")
            if not password:
                flash("Digite uma senha")
                return redirect("/register")
            if not confirmation:
                flash("Digite uma confirmação de senha")
                return redirect("/register")

            # Verify if the password and confirmation match
            if not password == confirmation:
                flash("As senhas não são iguais")
                return redirect("/register")
            # Verify if the username already exist
            try:
                db.execute("INSERT INTO users (username, hash) VALUES (?, ?)",
                           username, generate_password_hash(password))
            except:
                flash("Nome de usuário ja registrado")
                return redirect("/register")

            # Logs the user
            uid = db.execute("SELECT id FROM users WHERE username = ?", 
                             username)[0]["id"]
            session["user_id"] = uid
            flash("Registrado com sucesso!")
            return redirect("/")
        else:
            flash("Sistema não aberto para novos usuários")
            return redirect("/")

    else:
        return render_template("register.html")

