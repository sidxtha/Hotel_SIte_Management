import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")

# Database Configuration (Reads TiDB Cloud / Vercel Environment Variables)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "sid"),
    "database": os.getenv("DB_NAME", "friendship_hotel"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

# Configure Gemini AI API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Email Settings
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")


def get_db_connection():
    """Establish and return a database connection."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection failed: {e}")
        return None


def send_email_notification(subject, body_text):
    """Send email notifications for new bookings and orders."""
    if not (EMAIL_ADDRESS and EMAIL_PASSWORD and NOTIFY_EMAIL):
        print("Email credentials missing, skipping notification.")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = NOTIFY_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("Email notification sent successfully.")
    except Exception as e:
        print(f"Failed to send email notification: {e}")


@app.route("/")
def index():
    return render_template("home.html")


@app.route("/menu")
def menu():
    return render_template("menu.html")


@app.route("/book", methods=["GET", "POST"])
def book():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        check_in = request.form.get("check_in")
        check_out = request.form.get("check_out")
        room_type = request.form.get("room_type")
        guests = request.form.get("guests")

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                query = """
                    INSERT INTO bookings (name, email, check_in, check_out, room_type, guests)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (name, email, check_in, check_out, room_type, guests))
                conn.commit()
                cursor.close()
                conn.close()

                # Send Notification Email
                subject = f"New Booking Request: {name}"
                body = (
                    f"New Room Booking Received:\n\n"
                    f"Name: {name}\nEmail: {email}\n"
                    f"Check-In: {check_in}\nCheck-Out: {check_out}\n"
                    f"Room Type: {room_type}\nGuests: {guests}"
                )
                send_email_notification(subject, body)

                flash("Booking submitted successfully!", "success")
                return redirect(url_for("book"))
            except Error as e:
                print(f"Database error saving booking: {e}")
                flash("Database error saving booking. Please try again.", "danger")
        else:
            flash("Database connection error. Please try again later.", "danger")

    return render_template("book.html")


@app.route("/order", methods=["POST"])
def order():
    data = request.get_json() or {}
    customer_name = data.get("customer_name")
    contact = data.get("contact")
    items_summary = data.get("items_summary")
    total = data.get("total")
    notes = data.get("notes", "")

    if not (customer_name and contact and items_summary and total):
        return jsonify({"success": False, "message": "Missing required order details"}), 400

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO orders (customer_name, contact, items_summary, total, notes)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (customer_name, contact, items_summary, total, notes))
            conn.commit()
            cursor.close()
            conn.close()

            # Send Notification Email
            subject = f"New Food Order: {customer_name}"
            body = (
                f"New Order Placed:\n\n"
                f"Customer: {customer_name}\nContact: {contact}\n"
                f"Items: {items_summary}\nTotal: Rs. {total}\n"
                f"Notes: {notes}"
            )
            send_email_notification(subject, body)

            return jsonify({"success": True, "message": "Order placed successfully!"})
        except Error as e:
            print(f"Database error saving order: {e}")
            return jsonify({"success": False, "message": f"Database error: {e}"}), 500
    else:
        return jsonify({"success": False, "message": "Database connection error"}), 500


@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    conn = get_db_connection()
    if request.method == "POST":
        name = request.form.get("name")
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        if conn:
            try:
                cursor = conn.cursor()
                query = "INSERT INTO reviews (name, rating, comment) VALUES (%s, %s, %s)"
                cursor.execute(query, (name, rating, comment))
                conn.commit()
                cursor.close()
                flash("Thank you for your review!", "success")
            except Error as e:
                print(f"Error saving review: {e}")
                flash("Error submitting review.", "danger")

    reviews_list = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name, rating, comment, created_at FROM reviews ORDER BY created_at DESC")
            reviews_list = cursor.fetchall()
            cursor.close()
            conn.close()
        except Error as e:
            print(f"Error fetching reviews: {e}")

    return render_template("reviews.html", reviews=reviews_list)


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"reply": "Please enter a message."})

    if not GEMINI_API_KEY:
        return jsonify({"reply": "AI Assistant service is currently unavailable."})

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        system_prompt = (
            "You are the virtual receptionist for Friendship Hotel. "
            "Answer guest queries politely regarding room bookings, food menu items, and hotel amenities."
        )
        response = model.generate_content(f"{system_prompt}\nUser query: {user_message}")
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Gemini API error: {e}")
        return jsonify({"reply": "Sorry, I am having trouble answering right now."})


if __name__ == "__main__":
    app.run(debug=True)