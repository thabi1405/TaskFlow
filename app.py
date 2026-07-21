from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re

app = Flask(__name__)
app.secret_key = "taskflow_secret_key_2026"


# -------------------------
# Validation Functions
# -------------------------

def is_valid_email(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email)


def is_strong_password(password):
    if len(password) < 8:
        return False

    if not re.search(r"[A-Z]", password):
        return False

    if not re.search(r"[a-z]", password):
        return False

    if not re.search(r"[0-9]", password):
        return False

    return True


# -------------------------
# Home
# -------------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------------
# Register
# -------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        # Validate email
        if not is_valid_email(email):
            flash("Please enter a valid email address.", "error")
            return redirect("/register")

        # Validate password
        if not is_strong_password(password):
            flash("Password must be at least 8 characters and contain an uppercase letter, lowercase letter and a number.", "error")
            return redirect("/register")

        conn = sqlite3.connect("database/taskflow.db")
        cursor = conn.cursor()

        # Check duplicate email
        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash("An account with this email already exists.", "error")
            return redirect("/register")

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (full_name, email, password)
            VALUES (?, ?, ?)
            """,
            (full_name, email, hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# -------------------------
# Login
# -------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        conn = sqlite3.connect("database/taskflow.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Invalid email or password."
)

    return render_template("login.html")

# -------------------------
# Add Task
# -------------------------

@app.route("/add-task", methods=["GET", "POST"])
def add_task():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]

        conn = sqlite3.connect("database/taskflow.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tasks
            (user_id, title, description, due_date, priority)

            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            title,
            description,
            due_date,
            priority
        ))

        conn.commit()
        conn.close()

        flash("Task created successfully!", "success")

        return redirect("/dashboard")

    return render_template("add_task.html")
# -------------------------
# Dashboard
# -------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database/taskflow.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE user_id = ?
        AND completed = 0
        ORDER BY due_date
    """, (session["user_id"],))

    tasks = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=0",
        (session["user_id"],)
    )
    pending = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=1",
        (session["user_id"],)
    )
    completed = cursor.fetchone()[0]

    total = pending + completed

    conn.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        tasks=tasks,
        pending=pending,
        completed=completed,
        total=total
    )


# -------------------------
# Pending Tasks
# -------------------------

@app.route("/pending")
def pending_tasks():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "")

    conn = sqlite3.connect("database/taskflow.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE user_id = ?
        AND completed = 0
        AND title LIKE ?
        ORDER BY due_date
    """, (session["user_id"], f"%{search}%"))

    tasks = cursor.fetchall()

    conn.close()

    return render_template(
        "pending_tasks.html",
        tasks=tasks,
        search=search
    )
# -------------------------
# Edit Task
# -------------------------

@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database/taskflow.db")
    cursor = conn.cursor()

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]

        cursor.execute("""
            UPDATE tasks
            SET
                title = ?,
                description = ?,
                due_date = ?,
                priority = ?
            WHERE id = ?
            AND user_id = ?
        """, (
            title,
            description,
            due_date,
            priority,
            task_id,
            session["user_id"]
        ))

        conn.commit()
        conn.close()

        flash("Task updated successfully!", "success")

        return redirect("/dashboard")

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE id = ?
        AND user_id = ?
    """, (
        task_id,
        session["user_id"]
    ))

    task = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_task.html",
        task=task
    )

# -------------------------
# Complete Task
# -------------------------

@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database/taskflow.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET completed = 1
        WHERE id = ? AND user_id = ?
        """,
        (task_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------------------------
# Delete Task
# -------------------------

@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database/taskflow.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------------------------
# Complete Task
# -------------------------

@app.route("/completed")
def completed_tasks():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database/taskflow.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM tasks
        WHERE user_id = ?
        AND completed = 1
        ORDER BY due_date
    """, (session["user_id"],))

    tasks = cursor.fetchall()

    conn.close()

    return render_template(
        "completed_tasks.html",
        tasks=tasks,
        name=session["user_name"]
    )    

# -------------------------
# Logout
# -------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -------------------------
# Run App
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)