from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import psycopg2
from io import BytesIO
from functools import wraps
import matplotlib.pyplot as plt
import pandas as pd
from CarSales import app

DB_CONFIG = {
    "database": "cars",
    "user": "postgres",
    "password": "aRiana01",
    "host": "127.0.0.1",
    "port": "5432"
}

# Authentication check decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

# Function to get a database connection
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route("/home")
def home():
    return render_template("home.html", title="Home")

@app.route("/sales", methods=["GET", "POST"])
def sales():
    filters = ["sold = TRUE"]
    values = []

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    year = make = model = None
    if request.method == "POST":
        year = request.form.get('year')
        make = request.form.get('make')
        model = request.form.get('model')

        if year:
            filters.append("year = %s")
            values.append(year)
        if make:
            filters.append("make = %s")
            values.append(make)
        if model:
            filters.append("model = %s")
            values.append(model)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = f"SELECT * FROM inventory WHERE {' AND '.join(filters)}"
        cursor.execute(query, tuple(values))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        sold_df = pd.DataFrame(rows, columns=columns)
        sold_list = sold_df.to_dict(orient='records')

        chart_query = "SELECT date_sold, price FROM inventory WHERE sold = TRUE AND date_sold IS NOT NULL"
        chart_params = []

        if start_date:
            chart_query += " AND date_sold >= %s"
            chart_params.append(start_date)
        if end_date:
            chart_query += " AND date_sold <= %s"
            chart_params.append(end_date)

        cursor.execute(chart_query, tuple(chart_params))
        chart_rows = cursor.fetchall()
        chart_cols = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()

        chart_df = pd.DataFrame(chart_rows, columns=chart_cols)
        chart_df['date_sold'] = pd.to_datetime(chart_df['date_sold']).dt.date

        img = BytesIO()
        if chart_df.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, "No data for selected date range", ha='center', va='center')
            ax.axis('off')
            plt.savefig(img, format='png')
        else:
            grouped = chart_df.groupby('date_sold')['price'].sum().reset_index()
            plt.figure(figsize=(8, 5))
            plt.plot(grouped['date_sold'], grouped['price'], marker='o', linestyle='-', color='orange')
            plt.title("Total Sales Over Time")
            plt.xlabel("Date Sold")
            plt.ylabel("Total Sales ($)")
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        import base64
        chart_base64 = base64.b64encode(img.read()).decode('utf-8')

        return render_template(
            "sales.html",
            sold=sold_list,
            title="Sales Report",
            start_date=start_date or "",
            end_date=end_date or "",
            chart_data=chart_base64
        )

    except Exception as e:
        print(f"Error: {e}")
        return render_template("sales.html", sold=[], error=str(e), title="Sales Report")


@app.route("/inventory_table", methods=["GET", "POST"])
def inventory():
    filters = []
    values = []

    if request.method == "POST":
        year = request.form.get('year')
        make = request.form.get('make')
        model = request.form.get('model')

        if year:
            filters.append("year = %s")
            values.append(year)
        if make:
            filters.append("make = %s")
            values.append(make)
        if model:
            filters.append("model = %s")
            values.append(model)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = "SELECT * FROM inventory"
        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, tuple(values))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()

        inv_df = pd.DataFrame(rows, columns=columns)
        inventory_list = inv_df.to_dict(orient='records')

        return render_template("inventory.html", inventory=inventory_list, title="Inventory")

    except Exception as e:
        print(f"Database error: {e}")
        return render_template("inventory.html", inventory=[], error=str(e), title="Inventory")



@app.route("/add_new", methods=["GET", "POST"])
def save_to_database():
    if request.method == "POST":
        type_name = request.form.get("type")
        make_name = request.form.get("make")
        model_name = request.form.get("model")
        year = request.form.get("year")
        vin = request.form.get("vin")
        color = request.form.get("color")
        miles = request.form.get("miles")
        price = request.form.get("price")
        condition = request.form.get("condition")
        description = request.form.get("description")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("INSERT INTO type (type) VALUES (%s) RETURNING id", (type_name,))  
            type_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO make (make) VALUES (%s) RETURNING id", (make_name,))
            make_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO model (model) VALUES (%s) RETURNING id", (model_name,))
            model_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO trim (color, year) VALUES (%s, %s) RETURNING id", (color, year))
            trim_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO vehicle (description, vin, price, condition, miles, type_id, make_id, model_id, trim_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                description, vin, price, condition, miles,
                type_id, make_id, model_id, trim_id
            ))

            cursor.execute("""INSERT INTO inventory (type, make, model, color, year, vin, price, miles) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", (type_name, make_name, model_name, color, year, vin, price, miles,))  

            conn.commit()
            cursor.close()
            conn.close()

            print("Data saved to database successfully.")
            return "Vehicle added successfully."

        except Exception as e:
            print(f"Database error: {e}")
            return f"Database error: {e}", 500

    return render_template("add_vehicle.html", title="Add New Vehicle")





