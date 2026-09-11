import os
import smtplib
from email.mime.text import MIMEText
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

# ---------------------------------------------------------------
# Email Notification Configuration (for new orders)
# ---------------------------------------------------------------
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")        # the account that SENDS the email
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")      # Gmail App Password (not your normal password)
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", EMAIL_ADDRESS)  # where order alerts are RECEIVED

# ---------------------------------------------------------------
# Menu Catalog (single source of truth for prices/items)
# ---------------------------------------------------------------
MENU_ITEMS = [
    {"id": "soup", "name": "Soup of the Day", "price": 6, "category": "Starters"},
    {"id": "spring_rolls", "name": "Spring Rolls", "price": 7, "category": "Starters"},
    {"id": "grilled_chicken", "name": "Grilled Chicken", "price": 14, "category": "Main Course"},
    {"id": "veg_curry", "name": "Vegetable Curry", "price": 11, "category": "Main Course"},
    {"id": "pasta_alfredo", "name": "Pasta Alfredo", "price": 13, "category": "Main Course"},
    {"id": "choc_cake", "name": "Chocolate Cake", "price": 5, "category": "Desserts"},
    {"id": "ice_cream", "name": "Ice Cream", "price": 4, "category": "Desserts"},
]


def send_order_email(customer_name, contact, order_lines, total, notes):
    """Email the hotel staff the moment a new order comes in."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD or not NOTIFY_EMAIL:
        raise RuntimeError(
            "Email is not configured. Set EMAIL_ADDRESS, EMAIL_PASSWORD and NOTIFY_EMAIL in .env"
        )

    items_text = "\n".join(f"- {line}" for line in order_lines)
    body = (
        f"New order from: {customer_name}\n"
        f"Contact: {contact}\n\n"
        f"Items:\n{items_text}\n\n"
        f"Total: ${total:.2f}\n"
    )
    if notes:
        body += f"\nNotes: {notes}\n"

    msg = MIMEText(body)
    msg["Subject"] = f"New Food Order - {customer_name} (${total:.2f})"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = NOTIFY_EMAIL

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, [NOTIFY_EMAIL], msg.as_string())


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
    categories = []
    for item in MENU_ITEMS:
        cat = next((c for c in categories if c["name"] == item["category"]), None)
        if cat is None:
            cat = {"name": item["category"], "dishes": []}
            categories.append(cat)
        cat["dishes"].append(item)
    return render_template("menu.html", categories=categories)


# ---------------------------------------------------------------
# Order Form (from the Menu page)
# ---------------------------------------------------------------
@app.route("/order", methods=["POST"])
def order():
    customer_name = (request.form.get("customer_name") or "").strip()
    contact = (request.form.get("contact") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    if not customer_name or not contact:
        flash("Please enter your name and a phone/email so we can reach you.")
        return redirect(url_for("menu"))

    order_lines = []
    total = 0.0
    for item in MENU_ITEMS:
        try:
            qty = int(request.form.get(f"qty_{item['id']}", 0) or 0)
        except ValueError:
            qty = 0
        if qty > 0:
            line_total = qty * item["price"]
            total += line_total
            order_lines.append(f"{item['name']} x{qty} = ${line_total:.2f}")

    if not order_lines:
        flash("Please select at least one item to order.")
        return redirect(url_for("menu"))

    items_summary = "; ".join(order_lines)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO orders (customer_name, contact, items_summary, total, notes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (customer_name, contact, items_summary, total, notes),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        flash(f"Something went wrong saving your order: {e}")
        return redirect(url_for("menu"))

    try:
        send_order_email(customer_name, contact, order_lines, total, notes)
    except Exception as e:
        # Order is already saved in the database even if the email fails.
        flash(f"Order placed, but the notification email failed to send: {e}")
        return redirect(url_for("menu"))

    flash("Thanks! Your order has been placed. We'll be in touch shortly.")
    return redirect(url_for("menu"))


# ---------------------------------------------------------------
# Place Order Route (Saves to Database & Sends Email)
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
            order_items.append((key, qty, subtotal))

    if not order_items:
        flash("Please select at least one item to order.")
        return redirect(url_for("menu"))

    # 1. Save order to database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO orders (name, phone, total_price) VALUES (%s, %s, %s)",
            (name, phone, total_price)
        )
        order_id = cursor.lastrowid
        
        for item_name, qty, subtotal in order_items:
            cursor.execute(
                "INSERT INTO order_items (order_id, item_name, quantity, subtotal) VALUES (%s, %s, %s, %s)",
                (order_id, item_name, qty, subtotal)
            )
            
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        flash(f"Database error saving order: {e}")
        return redirect(url_for("menu"))

    # 2. Format and send email
    email_lines = [f"{item[0]} x {item[1]} = ${item[2]}" for item in order_items]
    email_content = f"""
    New Order Received! (Order ID: #{order_id})
    
    Customer Name: {name}
    Phone/Table: {phone}
    
    Items Ordered:
    """ + "\n".join(email_lines) + f"\n\nTotal: ${total_price}"

    try:
        msg = EmailMessage()
        msg.set_content(email_content)
        msg['Subject'] = f"New Order from {name} (# {order_id})"
        msg['From'] = os.getenv("MAIL_USERNAME")
        msg['To'] = os.getenv("HOTEL_OWNER_EMAIL")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv("MAIL_USERNAME"), os.getenv("MAIL_PASSWORD"))
            smtp.send_message(msg)
            
        flash("Your order has been successfully placed and saved!")
    except Exception as e:
        flash(f"Order saved to database, but email failed to send: {e}")

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