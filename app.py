from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"  # needed for flash messages

# ---------------------------------------------------------------
# MySQL connection settings
# Update these to match your local MySQL setup.
# ---------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "friendship_hotel",
}


def get_db_connection():
    """Open a new connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


# ---------------------------------------------------------------
# Static pages
# ---------------------------------------------------------------
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/menu")
def menu():
    return render_template("menu.html")


# ---------------------------------------------------------------
# Booking form -> inserts into `bookings` table
# ---------------------------------------------------------------
@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        room_type = request.form.get("room_type")
        guests = request.form.get("guests")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO bookings (name, email, check_in, check_out, room_type, guests)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (name, email, check_in, check_out, room_type, guests),
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Your booking has been submitted! We'll be in touch by email.")
        except Error as e:
            flash(f"Something went wrong saving your booking: {e}")

        return redirect(url_for("book"))

    return render_template("book.html")


# ---------------------------------------------------------------
# Reviews page -> lists reviews from DB, form inserts a new one
# ---------------------------------------------------------------
@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    if request.method == "POST":
        name = request.form.get("name")
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reviews (name, rating, comment) VALUES (%s, %s, %s)",
                (name, rating, comment),
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash("Thanks for your review!")
        except Error as e:
            flash(f"Something went wrong saving your review: {e}")

        return redirect(url_for("reviews"))

    # GET: fetch existing reviews to display
    review_rows = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name, rating, comment FROM reviews ORDER BY id DESC")
        review_rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Error as e:
        flash(f"Could not load reviews: {e}")

    return render_template("reviews.html", reviews=review_rows)


if __name__ == "__main__":
    app.run(debug=True)