import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
from google import genai
import smtplib
from email.message import EmailMessage

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-to-a-random-secret-key")

# ---------------------------------------------------------------
# MySQL Connection Configuration
# ---------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "sid",  # Your MySQL root password
    "database": "friendship_hotel",
}

# Initialize Gemini Client (automatically pulls GEMINI_API_KEY from .env)
ai_client = genai.Client()


def get_db_connection():
    """Open a new connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


# ---------------------------------------------------------------
# Static Pages
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
# Place Order Route (Sends email to hotel management)
# ---------------------------------------------------------------
@app.route("/place-order", methods=["POST"])
def place_order():
    name = request.form.get("customer_name")
    phone = request.form.get("customer_phone")
    
    prices = {
        'Soup of the Day': 6,
        'Spring Rolls': 7,
        'Grilled Chicken': 14,
        'Vegetable Curry': 11,
        'Pasta Alfredo': 13,
        'Chocolate Cake': 5,
        'Ice Cream': 4
    }
    
    order_items = []
    total_price = 0
    
    for key, price in prices.items():
        form_field_name = 'item_' + key.lower().replace(' ', '_')
        qty = int(request.form.get(form_field_name, 0))
        if qty > 0:
            subtotal = qty * price
            total_price += subtotal
            order_items.append(f"{key} x {qty} = ${subtotal}")

    if not order_items:
        flash("Please select at least one item to order.")
        return redirect(url_for("menu"))

    email_content = f"""
    New Order Received!
    
    Customer Name: {name}
    Phone/Table: {phone}
    
    Items Ordered:
    """ + "\n".join(order_items) + f"\n\nTotal: ${total_price}"

    try:
        msg = EmailMessage()
        msg.set_content(email_content)
        msg['Subject'] = f"New Order from {name}"
        msg['From'] = os.getenv("MAIL_USERNAME")
        msg['To'] = os.getenv("HOTEL_OWNER_EMAIL")

        # Using Gmail SMTP server (Port 465)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
            smtp.send_message(msg)
            
        flash("Your order has been successfully placed and sent to the kitchen!")
    except Exception as e:
        flash(f"There was an error sending your order: {e}")

    return redirect(url_for("menu"))


# ---------------------------------------------------------------
# Chatbot Route (Grounded Gemini AI)
# ---------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please enter a valid message."}), 400

    try:
        system_instruction = """
        You are the official AI Concierge for Friendship Hotel in Kathmandu, Nepal.
        Your job is to answer guest questions politely, accurately, and concisely (1 to 3 sentences max).

        Use ONLY the following hotel information to answer questions:
        - Location: 123 Main Street, Kathmandu, Nepal
        - Contact: Phone: +977-1-1234567 | Email: info@friendshiphotel.example.com
        - History: Welcoming guests since 1998.
        - Room Types: Standard, Deluxe, Suite.
        - Dining / Menu:
          * Starters: Soup of the Day ($6), Spring Rolls ($7)
          * Main Course: Grilled Chicken ($14), Vegetable Curry ($11), Pasta Alfredo ($13)
          * Desserts: Chocolate Cake ($5), Ice Cream ($4)
        - Booking & Reviews: Guests can submit booking requests and leave reviews directly on our website tabs.

        Rules:
        1. Keep responses short, direct, and under 3 sentences.
        2. Do NOT invent information not listed above.
        3. If asked about something outside this hotel's services, politely state you only assist with Friendship Hotel inquiries.
        """

        prompt = f"{system_instruction}\n\nGuest Question: {user_message}"

        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"Sorry, I couldn't process that right now. ({str(e)})"}), 500


# ---------------------------------------------------------------
# Booking Form
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
# Reviews Page
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