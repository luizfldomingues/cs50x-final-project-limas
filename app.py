from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from database.database import db

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


# TODO: understand what this means
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    # Request the list of pending orders and the list of products
    pending_orders = db.get_pending_orders()
    order_products = db.list_products(pending_orders)
    return render_template(
        "index.html", orders=pending_orders, order_products=order_products
    )


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
        order = db.get_order(order_id)
        if len(order) != 1:
            return apology("Não foi possível encontrar o pedido")
        # Request the list of the actual products
        actual_products = db.list_products(order)[int(order_id)]
        # Populates the intended products list
        for actual_product in actual_products:
            if request.form.get(str(actual_product["id"])):
                if request.form.get(str(actual_product["id"])).isnumeric():
                    intended_products[actual_product["id"]] = int(
                        request.form.get(str((actual_product["id"])))
                    )
                else:
                    intended_products[actual_product["id"]] = 0
        # Populates the increment_products list
        for actual_product in actual_products:
            if type(intended_products.get(actual_product["id"])) != None:
                quantity = intended_products[actual_product["id"]] - int(
                    actual_product["quantity"]
                )
                if quantity != 0:
                    increment_products.append(
                        {"id": actual_product["id"], "quantity": quantity}
                    )
        db.update_order(order_id, customer, table)
        db.add_order_products(order_id, increment_products)
        flash(f"Pedido Nº.{order_id} editado com sucesso")
        return redirect("/")
    # User reached route via GET
    else:
        order_id = request.args.get("order-id")
        order = db.get_order(order_id)
        if len(order) != 1:
            return apology("Pedido não encontrado")
        order_products = db.list_products(order)
        return render_template(
            "edit-order.html",
            order=order[0],
            order_products=order_products[int(order_id)],
        )


@app.route("/modify-order-status", methods=["POST"])
@login_required
def delete_order():
    order_id = request.form.get("order-id")
    order = db.get_order_status(order_id)
    if len(order) != 1:
        return apology("Não foi possível encontrar o pedido")
    order = order[0]
    action = request.form.get("action")
    if action == "delete":
        db.delete_order_products(order_id)
        db.delete_order_increments(order_id)
        db.delete_order(order_id)
        flash(f"Pedido Nº.{order_id} apagado com sucesso")
        return redirect("/")
    if action == "complete":
        try:
            db.update_order_status(order_id, "completed")
            flash(f"Pedido N.º {order_id} completado com sucesso")
        except:
            return apology("Algo deu errado com a mudança do status do pedido")
        return redirect("/")
    if action == "reopen":
        try:
            db.update_order_status(order_id, "pending")
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
            since_date = db.get_date_since(date_range)
            orders = db.get_completed_orders_since(since_date)
        else:
            orders = db.get_all_completed_orders()
            since_date = "Sempre"
        order_products = db.list_products(orders)
        total_sold = 0
        for order in orders:
            total_sold += order["total"]

        return render_template(
            "history.html",
            orders=orders,
            order_products=order_products,
            total=total_sold,
            since=since_date,
        )
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
                        increment_products.append(
                            {
                                "id": int(product),
                                "quantity": int(request.form.get(product)),
                            }
                        )
        except:
            return apology("Não foi possível registrar o produto")

        db.add_order_products(order_id, increment_products)
        flash(f"Pedido Nº.{order_id} incrementado com sucesso")
        return redirect("/")

    # User reached route via GET
    else:
        order_id = request.args.get("order-id")
        order = db.get_order(order_id)
        if len(order) != 1:
            return apology("Pedido não encontrado")
        product_types = db.get_product_types()
        products = []
        for type in product_types:
            products.append(
                {
                    "type": type["type_name"],
                    "products": db.get_products_by_type(type["id"]),
                }
            )
        order = order[0]
        return render_template(
            "increment-order.html", products=products, order=order, order_id=order_id
        )


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
        user = db.get_user_by_username(username)
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


@app.route("/products/<status>")
@app.route("/products", defaults={"status": "active"})
@login_required
def products(status):
    if status == "active":
        product_types = db.get_product_types()
        for c in range(len(product_types)):
            product_types[c]["products"] = db.get_products_by_type(
                product_types[c]["id"]
            )
        return render_template(
            "products.html", product_types=product_types, status=status
        )
    elif status == "inactive":
        product_types = db.get_inactive_product_types()
        for c in range(len(product_types)):
            product_types[c]["products"] = db.get_inactive_products_by_type(
                product_types[c]["id"]
            )
        return render_template(
            "products.html", product_types=product_types, status=status
        )


@app.route("/products/edit", methods=["GET", "POST"])
@login_required
def products_edit():
    """Edit a product or product type"""
    if request.method == "POST":
        # A product id is given
        if request.form.get("product-id"):
            # Check if the product with given id exists
            product = db.get_product_by_id(request.form.get("product-id"))
            if len(product) != 1:
                return apology("Product was not found")
            product = product[0]
            new_values = {
                "name": request.form.get("product-name"),
                "price": request.form.get("product-price"),
                "type": request.form.get("product-type"),
                "status": request.form.get("product-status"),
            }
            # Validate the new_values data
            if (
                not new_values["name"]
                or not new_values["price"].isnumeric()
                or len(db.get_product_type_by_id(new_values["type"])) != 1
                or not new_values["status"] in ["active", "inactive"]
            ):
                return apology("Algum dos valores enviados são incompatíveis")
            try:
                db.update_product(
                    new_values["name"],
                    new_values["price"],
                    new_values["type"],
                    new_values["status"],
                    product["id"],
                )
            except Exception as exception:
                return apology(f"Não foi possível editar o produto\n{exception}")
            flash(f"Produto N.º{product['id']} editado com sucesso")
            return redirect("/products")
        # A product_type_id is given

        elif request.form.get("product-type-id"):
            # Check if the product_type with given id exists
            product_type = db.get_full_product_type_by_id(
                request.form.get("product-type-id")
            )
            if len(product_type) != 1:
                return apology("Tipo de produto não encontrado")
            product_type = product_type[0]
            new_values = {
                "name": request.form.get("type-name"),
                "status": request.form.get("type-status"),
            }
            # Validate the new_values data
            if not new_values["name"] or not new_values["status"] in [
                "active",
                "inactive",
            ]:
                return apology("Algum dos valores enviados são incompatíveis")
            try:
                db.update_product_type(
                    new_values["name"], new_values["status"], product_type["id"]
                )
            except Exception as exception:
                return apology(
                    f"Não foi possível editar o tipo de produto\n{exception}"
                )
            flash(f"Tipo de produto N.º{product_type['id']} editado com sucesso")
            return redirect("/products")

    # User reached route via GET
    else:
        # Serve page for editing a product
        if request.args.get("product-id"):
            product = db.get_product_by_id(request.args.get("product-id"))
            if len(product) != 1:
                return apology("Produto não encontrado")
            product = product[0]
            product_types = db.get_active_product_types()
            return render_template(
                "edit-product.html", product=product, product_types=product_types
            )
        # Serve page for editing a product type
        elif request.args.get("product-type-id"):
            product_type = db.get_full_product_type_by_id(
                request.args.get("product-type-id")
            )
            if len(product_type) != 1:
                return apology("Tipo de produto não encontrado")
            product_type = product_type[0]
            return render_template("edit-product-type.html", product_type=product_type)


@app.route("/products/new/product", methods=["GET", "POST"])
@login_required
def products_new_product():
    if request.method == "POST":
        # User wants to create a new product
        new_values = {
            "name": request.form.get("product-name"),
            "price": request.form.get("product-price"),
            "type": request.form.get("product-type"),
        }
        # Validate the new_values data
        if (
            not new_values["name"]
            or not new_values["price"].isnumeric()
            or len(db.get_product_type_by_id(new_values["type"])) != 1
        ):
            return apology("Algum dos valores enviados são incompatíveis")
        try:
            db.create_product(
                new_values["name"], new_values["price"], new_values["type"]
            )
        except Exception as exception:
            return apology(f"Não foi possível registar o produto: \n{exception}")
        flash(f"Produto registrado com sucesso")
        return redirect("/products")
    # User reached route via get
    else:
        product_types = db.get_active_product_types()
        return render_template("new-product.html", product_types=product_types)


@app.route("/products/new/product-type", methods=["GET", "POST"])
@login_required
def products_new_product_type():
    if request.method == "POST":
        # User wants to create a new product type
        type_name = request.form.get("type-name")

        # Validate the new_values data
        if not type_name:
            return apology("Insira um nome para o tipo de produto")
        try:
            db.create_product_type(type_name)
        except Exception as exception:
            return apology(
                f"Não foi possível registar o tipo de produto: \n{exception}"
            )
        flash(f"Tipo de produto registrado com sucesso")
        return redirect("/products")
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
                        order_products.append(
                            {
                                "id": int(product),
                                "quantity": int(request.form.get(product)),
                            }
                        )
        except:
            return apology("Não foi possível registrar o produto")
        customer = request.form.get("customer")
        table_number = request.form.get("table-number")

        # Register the order into the orders table
        order_id = db.create_order(session["user_id"], customer, table_number)
        db.add_order_products(order_id, order_products)
        flash(f"Pedido N.º{order_id} registrado")
        return redirect("/")
    # User reached route via GET
    else:
        product_types = db.get_product_types()
        products = []
        for type in product_types:
            products.append(
                {
                    "type": type["type_name"],
                    "products": db.get_products_by_type(type["id"]),
                }
            )
        return render_template("new-order.html", products=products)


@app.route("/order-details")
@login_required
def order_details():
    order_id = request.args.get("order-id")
    order = db.get_order(order_id)
    if len(order) != 1:
        return apology("Pedido não encontrado")
    # list_products(order_id, order)
    order = order[0]
    details = {}
    details["total"] = db.get_order_total(order_id)
    details["username"] = db.get_order_username(order_id)
    details["time"] = db.get_order_time(order_id)
    details["status"] = db.get_order_status(order_id)[0].get("order_status")

    increments = db.get_order_increments(order_id)
    for i in range(len(increments)):
        increments[i]["products"] = db.get_increment_products(
            increments[i]["id"], order_id
        )
        increments[i]["total"] = db.get_increment_total(increments[i]["id"])
    return render_template(
        "order-details.html", order=order, increments=increments, details=details
    )


@app.route("/reports")
@login_required
def reports():
    """Page for querying for sales reports"""
    flash("TODO")
    return render_template("blank.html")


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
                db.create_user(username, generate_password_hash(password))
            except:
                flash("Nome de usuário ja registrado")
                return redirect("/register")

            # Logs the user
            uid = db.get_user_id_by_username(username)
            session["user_id"] = uid
            flash("Registrado com sucesso!")
            return redirect("/")
        else:
            flash("Sistema não aberto para novos usuários")
            return redirect("/")

    else:
        return render_template("register.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000")
