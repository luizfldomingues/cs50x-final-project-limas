from flask import redirect, render_template, session
from functools import wraps

def apology(message, code="400"):
    return render_template("apology.html", message=message, code=code)

def brl(value):
    """Format value from BRL cents to BRL"""
    try:
        value = int(value)
    except (ValueError, TypeError):
        value = 0
    return f"R${value/100:,.2f}".replace(".", ",")

# TODO: Understand how this works
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
