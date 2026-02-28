from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "fitzone_secret_key"

# ----------------------------
# Database Initialize
# ----------------------------
def init_db():
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()

    # contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            message TEXT
        )
    """)

    # members table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            plan TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ----------------------------
# Home & About
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

# ----------------------------
# Membership Registration
@app.route("/membership", methods=["GET", "POST"])
def membership():
    success = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        plan = request.form["plan"]

        hashed_password = generate_password_hash(password)
        try:
            conn = sqlite3.connect("gym.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO members (name, email, password, plan) VALUES (?, ?, ?, ?)",
                (name, email, hashed_password, plan)
            )
            conn.commit()
            conn.close()
            success = "Registration Successful!"
        except sqlite3.IntegrityError:
            success = "Email already registered!"
    return render_template("membership.html", success=success)

# ----------------------------
# BMI Calculator
@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    result = None
    if request.method == "POST":
        weight = float(request.form["weight"])
        height = float(request.form["height"])
        bmi_value = weight / ((height / 100) ** 2)
        result = round(bmi_value, 2)
    return render_template("bmi.html", result=result)

# ----------------------------
# Contact Form
@app.route("/contact", methods=["GET", "POST"])
def contact():
    success = None
    if request.method == "POST":
        name = request.form["name"]
        message = request.form["message"]
        conn = sqlite3.connect("gym.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO contacts (name, message) VALUES (?, ?)", (name, message))
        conn.commit()
        conn.close()
        success = "Message Sent Successfully!"
    return render_template("contact.html", success=success)

# ----------------------------
# User Login
@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = sqlite3.connect("gym.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, password FROM members WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect("/profile")
        else:
            error = "Invalid email or password!"
    return render_template("user_login.html", error=error)

# ----------------------------
# User Profile
@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect("/user_login")
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, plan FROM members WHERE id = ?", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()
    return render_template("profile.html", user=user)

# ----------------------------
# Admin Login
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "1234":
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Invalid Credentials!"
    return render_template("login.html", error=error)

# ----------------------------
# Admin Dashboard
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contacts")
    contacts = cursor.fetchall()
    cursor.execute("SELECT id, name, email, plan FROM members")
    members = cursor.fetchall()
    conn.close()
    return render_template("admin.html", contacts=contacts, members=members)

# ----------------------------
# Delete Contact
@app.route("/delete_contact/<int:id>")
def delete_contact(id):
    if not session.get("admin"):
        return redirect("/login")
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM contacts WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ----------------------------
# Delete Member
@app.route("/delete_member/<int:id>")
def delete_member(id):
    if not session.get("admin"):
        return redirect("/login")
    conn = sqlite3.connect("gym.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM members WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ----------------------------
# Logout
@app.route("/logout")
def logout():
    session.pop("admin", None)
    session.pop("user_id", None)
    session.pop("user_name", None)
    return redirect("/")

# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)