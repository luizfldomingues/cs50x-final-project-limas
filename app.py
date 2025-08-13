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

        if table and not table.isnumeric():
            return apology("Número de mesa inválido")

        order = db.get_order(order_id)
        if not order:
            return apology("Não foi possível encontrar o pedido")

        actual_products = db.list_products([order])[int(order_id)]
        increment_products = []

        for product in actual_products:
            product_id = str(product["id"])
            intended_quantity_str = request.form.get(product_id)

            if intended_quantity_str and intended_quantity_str.isnumeric():
                intended_quantity = int(intended_quantity_str)
                current_quantity = int(product["quantity"])
                quantity_diff = intended_quantity - current_quantity

                if quantity_diff != 0:
                    increment_products.append(
                        {"id": product["id"], "quantity": quantity_diff}
                    )

        db.update_order(order_id, customer, table)
        db.add_order_products(order_id, increment_products)

        flash(f"Pedido Nº.{order_id} editado com sucesso")
        return redirect("/")
    # User reached route via GET
    else:
        order_id = request.args.get("order-id")
        order = db.get_order(order_id)
        if not order:
            return apology("Pedido não encontrado")
        order_products = db.list_products([order])
        return render_template(
            "edit-order.html",
            order=order,
            order_products=order_products[int(order_id)],
        )


@app.route("/modify-order-status", methods=["POST"])
@login_required
def modify_order_status():
    order_id = request.form.get("order-id")
    order = db.get_order_status(order_id)
    if not order:
        return apology("Não foi possível encontrar o pedido")
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
            orders = db.get_completed_orders(since_date)
        else:
            orders = db.get_completed_orders()
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
            return apology("ID de pedido inválido")

        increment_products = []
        for key, value in request.form.items():
            if key.isnumeric() and value.isnumeric():
                quantity = int(value)
                if quantity > 0:
                    increment_products.append({"id": int(key), "quantity": quantity})

        if not increment_products:
            flash("Nenhum produto foi adicionado")
            return redirect(f"/increment-order?order-id={order_id}")

        db.add_order_products(order_id, increment_products)
        flash(f"Pedido Nº.{order_id} incrementado com sucesso")
        return redirect("/")

    # User reached route via GET
    else:
        order_id = request.args.get("order-id")
        order = db.get_order(order_id)
        if not order:
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
        if not user or not check_password_hash(
            user["hash"], request.form.get("password")
        ):
            flash("Usuário ou senha incorretos")
            return redirect("/login")

        # If password hash matches, logs the user
        session["user_id"] = user["id"]
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
        product_types = db.get_active_product_types()
        for pt in product_types:
            pt["products"] = db.get_products_by_type(pt["id"])
    elif status == "inactive":
        product_types = db.get_inactive_product_types()
        for pt in product_types:
            pt["products"] = db.get_inactive_products_by_type(pt["id"])
    else:
        return apology("Status de produto inválido")

    return render_template("products.html", product_types=product_types, status=status)


@app.route("/products/edit-product", methods=["GET", "POST"])
@login_required
def edit_product():
    if request.method == "POST":
        product_id = request.form.get("product-id")
        product = db.get_product_by_id(product_id)
        if not product:
            return apology("Product was not found")

        new_values = {
            "name": request.form.get("product-name"),
            "price": request.form.get("product-price"),
            "type": request.form.get("product-type"),
            "status": request.form.get("product-status"),
        }

        if (
            not new_values["name"]
            or not new_values["price"].isnumeric()
            or not db.get_product_type_by_id(new_values["type"])
            or new_values["status"] not in ["active", "inactive"]
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

    else:  # GET
        product_id = request.args.get("product-id")
        product = db.get_product_by_id(product_id)
        if not product:
            return apology("Produto não encontrado")

        product_types = db.get_active_product_types()
        return render_template(
            "edit-product.html", product=product, product_types=product_types
        )


@app.route("/products/edit-product-type", methods=["GET", "POST"])
@login_required
def edit_product_type():
    if request.method == "POST":
        product_type_id = request.form.get("product-type-id")
        product_type = db.get_product_type_by_id(product_type_id)
        if not product_type:
            return apology("Tipo de produto não encontrado")

        new_values = {
            "name": request.form.get("type-name"),
            "status": request.form.get("type-status"),
        }

        if not new_values["name"] or new_values["status"] not in ["active", "inactive"]:
            return apology("Algum dos valores enviados são incompatíveis")

        try:
            db.update_product_type(
                new_values["name"], new_values["status"], product_type["id"]
            )
        except Exception as exception:
            return apology(f"Não foi possível editar o tipo de produto\n{exception}")

        flash(f"Tipo de produto N.º{product_type['id']} editado com sucesso")
        return redirect("/products")

    else:  # GET
        product_type_id = request.args.get("product-type-id")
        product_type = db.get_product_type_by_id(product_type_id)
        if not product_type:
            return apology("Tipo de produto não encontrado")

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
            or not db.get_product_type_by_id(new_values["type"])
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
        for key, value in request.form.items():
            if key.isnumeric() and value.isnumeric():
                quantity = int(value)
                if quantity > 0:
                    order_products.append({"id": int(key), "quantity": quantity})

        if not order_products:
            flash("Nenhum produto foi adicionado")
            return redirect("/new-order")

        customer = request.form.get("customer")
        table_number = request.form.get("table-number")

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
    if not order:
        return apology("Pedido não encontrado")
    details = {}
    details["total"] = db.get_order_total(order_id)
    details["username"] = db.get_order_username(order_id)
    details["time"] = db.get_order_time(order_id)
    details["status"] = db.get_order_status(order_id).get("order_status")

    increments = db.get_order_increments(order_id)
    for i in range(len(increments)):
        increments[i]["products"] = db.get_increment_products(
            increments[i]["id"], order_id
        )
        increments[i]["total"] = db.get_increment_total(increments[i]["id"])
    return render_template(
        "order-details.html", order=order, increments=increments, details=details
    )

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
