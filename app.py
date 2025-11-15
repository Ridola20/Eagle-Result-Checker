# from flask import Flask, request, jsonify, render_template, g, redirect, url_for, session
# import sqlite3
# import requests
# import random
# import os
# from dotenv import load_dotenv
# from flask import send_from_directory
# from sqlalchemy import create_engine, text
# from sqlalchemy.orm import sessionmaker

# # Load environment variables
# load_dotenv()

# USER = os.getenv("user")
# PASSWORD = os.getenv("password")
# HOST = os.getenv("host")
# PORT = os.getenv("port")
# DBNAME = os.getenv("dbname")

# DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)

# # Helper to get a SQLAlchemy session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()



# def init_db_pg():
#     with engine.connect() as conn:
#         conn.execute(text("""
#             CREATE TABLE IF NOT EXISTS results (
#                 id SERIAL PRIMARY KEY,
#                 student_name TEXT NOT NULL,
#                 exam_number TEXT NOT NULL UNIQUE,
#                 result_blob BYTEA NOT NULL,
#                 access_key TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             );
#         """))

#         conn.execute(text("""
#             CREATE TABLE IF NOT EXISTS staff_passkey (
#                 id INTEGER PRIMARY KEY,
#                 passkey TEXT NOT NULL
#             );
#         """))

#         # Insert default passkey if missing
#         result = conn.execute(text("SELECT * FROM staff_passkey WHERE id = 1")).fetchone()
#         if not result:
#             conn.execute(text("INSERT INTO staff_passkey (id, passkey) VALUES (1, :p)"),
#                         {"p": os.getenv("DEFAULT_PASSKEY", "admin123")})
# init_db_pg()


# def generate_random_number():
#     # Generate a random 6-digit number
#     random_number = random.randint(100000, 999999)
#     return str(random_number)

# # Initialize Flask app
# app = Flask(__name__)
# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key-change-in-production')

# def send_simple_message(to_recipients: list, subject: str, html: str) -> None:
#     """Send email via Brevo API"""
#     api_key = os.getenv('BREVO_API_KEY')
    
#     if not api_key:
#         print("BREVO_API_KEY not found in environment variables")
#         return
    
#     payload = {
#         "sender": {
#             "name": "Eagle Schools Results",
#             "email": "funkesanusi8@gmail.com"
#         },
#         "to": to_recipients,
#         "subject": subject,
#         "htmlContent": html,
#     }
    
#     response = requests.post(
#         "https://api.brevo.com/v3/smtp/email",
#         headers={
#             "accept": "application/json",
#             "api-key": api_key,
#             "content-type": "application/json",
#         },
#         json=payload,
#         timeout=30,
#     )
    
#     # Check if the request was successful
#     if response.status_code == 201:
#         print("Email sent successfully!")
#     else:
#         print(f"Failed to send email. Status: {response.status_code}, Response: {response.text}")

# # Home route
# @app.route("/")
# def index():
#     return render_template("index.html")

# @app.route('/results', methods=['GET', 'POST'])
# def results():
#     db = next(get_db())
#     search_query = request.form.get('search_query', '').strip()

#     try:
#         if search_query:
#             rows = db.execute(text("""
#                 SELECT * FROM results
#                 WHERE student_name ILIKE :q OR exam_number ILIKE :q
#             """), {"q": f"%{search_query}%"}).fetchall()
#         else:
#             rows = db.execute(text("SELECT * FROM results")).fetchall()

#         return render_template('view_users.html', users=rows, search_query=search_query)

#     except Exception as e:
#         return render_template('view_users.html', error=str(e))


# @app.route('/upload', methods=['GET', 'POST'])
# def upload_result():
#     if request.method == 'POST':
#         data = request.form
#         student_name = data.get('student_name')
#         exam_number = data.get('exam_number')
#         passkey = data.get('staff_passkey')
#         result_file = request.files.get('result_blob')
#         email = data.get('email')
#         random_string = generate_random_number()

#         if not student_name or not exam_number or not result_file or not passkey:
#             return jsonify({'error': 'Missing required fields'}), 400

#         try:
#             db = next(get_db())

#             # Check upload limit for today
#             count = db.execute(text("""
#                 SELECT COUNT(*) FROM results
#                 WHERE DATE(created_at) = CURRENT_DATE
#             """)).scalar()

#             if count >= 149:
#                 return jsonify({'error': 'Daily upload limit reached (149 per day).'}), 429

#             # Validate passkey
#             valid_passkey = db.execute(text("SELECT passkey FROM staff_passkey WHERE id=1")).scalar()

#             if str(passkey) != str(valid_passkey):
#                 return jsonify({'error': 'Invalid passkey'}), 403

#             result_blob = result_file.read()

#             # Delete existing record for same exam_number
#             db.execute(text("DELETE FROM results WHERE exam_number = :e"),
#                        {"e": exam_number})

#             # Insert new result
#             db.execute(text("""
#                 INSERT INTO results (student_name, exam_number, result_blob, access_key, created_at)
#                 VALUES (:n, :e, :b, :a, NOW())
#             """), {
#                 "n": student_name,
#                 "e": exam_number,
#                 "b": result_blob,
#                 "a": random_string
#             })

#             db.commit()

#             # Send the email
#             try:
#                 subject = f"📚 Your Result is Ready - Eagle Schools"
#                 recipients = [{"email": "eagleschools@gmail.com"}, {"email": email}]
#                 message_body = f""" 
#                 <!DOCTYPE html> <html> <head> <style> body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }} .email-container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }} .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; padding: 30px 20px; text-align: center; border: none; }} .header h1 {{ margin: 0; font-size: 24px; font-weight: bold; }} .content {{ padding: 30px; line-height: 1.6; color: #374151; }} .content p {{ margin: 0 0 15px; }} .access-key {{ font-size: 20px; color: #2563eb; font-weight: bold; background-color: #dbeafe; padding: 15px; text-align: center; margin: 20px 0; border: 2px dashed #2563eb; font-family: 'Courier New', monospace; }} .cta-button {{ display: block; width: 200px; margin: 25px auto; padding: 12px 24px; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; text-decoration: none; text-align: center; font-weight: bold; border: none; cursor: pointer; }} .cta-button:hover {{ background: linear-gradient(135deg, #1d4ed8, #1e40af); }} .info-box {{ background-color: #f0f9ff; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0; }} .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #6b7280; background-color: #f8fafc; border-top: 1px solid #e5e7eb; }} .login-link {{ color: #2563eb; text-decoration: none; font-weight: bold; }} .login-link:hover {{ text-decoration: underline; }} .steps {{ margin: 20px 0; }} .step {{ margin-bottom: 10px; padding-left: 20px; position: relative; }} .step:before {{ content: "✓"; position: absolute; left: 0; color: #10b981; font-weight: bold; }} </style> </head> <body> <div class="email-container"> <div class="header"> <h1>🎓 Eagle Schools</h1> <p>Student Results Portal</p> </div> <div class="content"> <p>Dear <strong>{student_name}</strong>,</p> <p>We're pleased to inform you that your examination result has been successfully uploaded to our secure portal and is now available for viewing.</p> <div class="info-box"> <p><strong>Exam Number:</strong> {exam_number}</p> <p><strong>Access Key:</strong></p> <div class="access-key">{random_string}</div> </div> <div class="steps"> <p><strong>To access your result:</strong></p> <div class="step">Visit the Eagle Schools Results Portal</div> <div class="step">Enter your Exam Number: <strong>{exam_number}</strong></div> <div class="step">Use the Access Key provided above</div> </div> <a href="https://eagle-result-checker.vercel.app/login" class="cta-button"> View Your Result Now </a> <p>For security reasons, please keep your access key confidential and do not share it with others.</p> <p>If you encounter any issues accessing your result, please contact the school administration.</p> </div> <div class="footer"> <p>&copy; 2024 Eagle Schools. All rights reserved.</p> <p>This is an automated message. Please do not reply to this email.</p> <p>Access your result at: <a href="https://eagle-result-checker.vercel.app/login" class="login-link"> https://eagle-result-checker.vercel.app/login </a> </p> </div> </div> </body> </html> """

#                 # (Your email HTML remains unchanged)
#                 send_simple_message(recipients, subject, message_body)

#             except Exception as e:
#                 print("Email sending error:", e)

#             return redirect(url_for('results'))

#         except Exception as e:
#             return jsonify({'error': str(e)}), 500

#     return render_template('upload.html')

# @app.route('/download_result/<int:result_id>')
# def download_result(result_id):
#     if 'exam_number' not in session:
#         return redirect(url_for('login'))

#     db = next(get_db())

#     try:
#         row = db.execute(text("""
#             SELECT result_blob, exam_number, student_name
#             FROM results
#             WHERE id = :id
#         """), {"id": result_id}).fetchone()

#         if not row:
#             return jsonify({'error': 'Result not found'}), 404

#         if row.exam_number != session['exam_number']:
#             return jsonify({'error': 'Unauthorized'}), 403

#         return app.response_class(
#             response=row.result_blob,
#             status=200,
#             mimetype='application/pdf',
#             headers={'Content-Disposition': f'attachment;filename={row.student_name}_result.pdf'}
#         )

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         exam_number = request.form.get('exam_number')
#         password = request.form.get('password')

#         db = next(get_db())

#         row = db.execute(text("""
#             SELECT * FROM results WHERE exam_number = :e
#         """), {"e": exam_number}).fetchone()

#         if row and row.access_key == password:
#             session['user_id'] = row.id
#             session['exam_number'] = row.exam_number
#             return redirect(url_for('results'))

#         return render_template('login.html', error="Invalid credentials")

#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     session.pop('user_id', None)  # Remove user session data
#     session.pop('exam_number', None)
#     return redirect(url_for('login'))  # Redirect to the login page

# @app.route('/dashboard')
# def dashboard():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))

#     db = next(get_db())

#     try:
#         total = db.execute(text("SELECT COUNT(*) FROM results")).scalar()
#         last_id = db.execute(text("SELECT MAX(id) FROM results")).scalar()

#         return render_template('dashboard.html',
#                                total_students=total,
#                                total_results=total,
#                                last_upload=f"Result ID: {last_id}" if last_id else "No uploads yet")

#     except Exception as e:
#         return render_template('dashboard.html', error=str(e))

# @app.route('/student/result', methods=['GET', 'POST'])
# def student_check_result():
#     if request.method == 'POST':
#         exam_number = request.form.get('exam_number')
#         access_key = request.form.get('access_key')

#         db = next(get_db())

#         row = db.execute(text("""
#             SELECT * FROM results
#             WHERE exam_number = :e AND access_key = :a
#         """), {"e": exam_number, "a": access_key}).fetchone()

#         if row:
#             return render_template("student_result.html",
#                                    student_name=row.student_name,
#                                    exam_number=row.exam_number,
#                                    result_id=row.id,
#                                    access_key=access_key)

#         return render_template("check_result.html", error="Invalid exam number or access key")

#     return render_template("check_result.html")

# @app.route('/bulk_upload', methods=['GET', 'POST'])
# def bulk_upload():
#     if request.method == 'POST':
#         if 'csv_file' not in request.files:
#             return render_template('bulk_upload.html', error="No file selected")

#         csv_file = request.files['csv_file']

#         if csv_file.filename == '':
#             return render_template('bulk_upload.html', error="No file selected")

#         if csv_file and csv_file.filename.endswith('.csv'):
#             try:
#                 import csv, io

#                 db = next(get_db())

#                 stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
#                 reader = csv.DictReader(stream)

#                 success = 0
#                 errors = 0

#                 for row in reader:
#                     try:
#                         db.execute(text("""
#                             INSERT INTO results (student_name, exam_number, result_blob, access_key)
#                             VALUES (:n, :e, '', :a)
#                             ON CONFLICT (exam_number)
#                             DO UPDATE SET student_name = :n, access_key = :a
#                         """), {
#                             "n": row['student_name'],
#                             "e": row['exam_number'],
#                             "a": generate_random_number()
#                         })
#                         success += 1
#                     except:
#                         errors += 1

#                 db.commit()

#                 return render_template('bulk_upload.html',
#                                        success=f"Processed {success}. Errors: {errors}")

#             except Exception as e:
#                 return render_template('bulk_upload.html', error=str(e))

#     return render_template('bulk_upload.html')

# @app.route('/manifest.json')
# def manifest():
#     return send_from_directory('static', 'manifest.json')

# @app.route('/sw.js')
# def service_worker():
#     return send_from_directory('static', 'sw.js'), 200, {'Content-Type': 'application/javascript'}

# @app.route('/offline')
# def offline():
#     return render_template('offline.html')

# # Initialize the database and start the app
# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
import os
import random
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

# ------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------------------------------
load_dotenv()

USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# ------------------------------------------------
# SQLAlchemy ENGINE + SESSION
# ------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2
)

SessionLocal = scoped_session(sessionmaker(bind=engine))


# Clean DB session after each request
def get_db():
    db = SessionLocal()
    try:
        return db
    except:
        db.close()


# ------------------------------------------------
# INITIALIZE DATABASE TABLES ONCE
# ------------------------------------------------
def init_db_pg():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS results (
                id SERIAL PRIMARY KEY,
                student_name TEXT NOT NULL,
                exam_number TEXT NOT NULL UNIQUE,
                result_blob BYTEA,
                access_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS staff_passkey (
                id INTEGER PRIMARY KEY,
                passkey TEXT NOT NULL
            );
        """))

        conn.execute(text("""
            INSERT INTO staff_passkey (id, passkey)
            VALUES (1, 'E4GL35')
            ON CONFLICT (id) DO NOTHING;
        """))


# Run once at startup
init_db_pg()


# ------------------------------------------------
# HELPERS
# ------------------------------------------------
def generate_random_number():
    return str(random.randint(100000, 999999))

def send_simple_message(to_recipients: list, subject: str, html: str) -> None:
    api_key = os.getenv('BREVO_API_KEY')

    if not api_key:
        print("BREVO_API_KEY missing")
        return

    payload = {
        "sender": {"name": "Eagle Schools Results", "email": "funkesanusi8@gmail.com"},
        "to": to_recipients,
        "subject": subject,
        "htmlContent": html,
    }

    requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"accept": "application/json", "api-key": api_key, "content-type": "application/json"},
        json=payload,
        timeout=30,
    )


# ------------------------------------------------
# FLASK APP
# ------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

# ---------------------- HOME --------------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------------- VIEW RESULTS --------------------
@app.route("/results", methods=["GET", "POST"])
def results():
    db = get_db()
    search_query = request.form.get('search_query', '').strip()

    try:
        if search_query:
            rows = db.execute(text("""
                SELECT * FROM results
                WHERE student_name ILIKE :q OR exam_number ILIKE :q
            """), {"q": f"%{search_query}%"}).fetchall()
        else:
            rows = db.execute(text("SELECT * FROM results")).fetchall()

        return render_template("view_users.html", users=rows, search_query=search_query)

    except Exception as e:
        return render_template("view_users.html", error=str(e))

    finally:
        db.close()

# ---------------------- UPLOAD RESULT --------------------
@app.route("/upload", methods=["GET", "POST"])
def upload_result():
    if request.method == "POST":
        db = get_db()

        try:
            data = request.form
            student_name = data.get('student_name')
            exam_number = data.get('exam_number')
            passkey = data.get('staff_passkey')
            result_file = request.files.get('result_blob')
            email = data.get('email')
            access_key = generate_random_number()
            random_string = access_key

            # Validate
            if not all([student_name, exam_number, passkey, result_file]):
                return jsonify({"error": "Missing required fields"}), 400

            # Validate passkey
            valid_passkey = db.execute(text("SELECT passkey FROM staff_passkey WHERE id = 1")).scalar()
            print(valid_passkey)
            if str(passkey) != str(valid_passkey):
                return jsonify({"error": "Invalid passkey"}), 403

            # Delete old
            db.execute(text("DELETE FROM results WHERE exam_number = :e"), {"e": exam_number})

            # Insert new
            db.execute(text("""
                INSERT INTO results (student_name, exam_number, result_blob, access_key)
                VALUES (:n, :e, :b, :a)
            """), {
                "n": student_name,
                "e": exam_number,
                "b": result_file.read(),
                "a": access_key
            })

            db.commit()

            # Email (optional)
            message_body = f""" 
                 <!DOCTYPE html> <html> <head> <style> body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }} .email-container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }} .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; padding: 30px 20px; text-align: center; border: none; }} .header h1 {{ margin: 0; font-size: 24px; font-weight: bold; }} .content {{ padding: 30px; line-height: 1.6; color: #374151; }} .content p {{ margin: 0 0 15px; }} .access-key {{ font-size: 20px; color: #2563eb; font-weight: bold; background-color: #dbeafe; padding: 15px; text-align: center; margin: 20px 0; border: 2px dashed #2563eb; font-family: 'Courier New', monospace; }} .cta-button {{ display: block; width: 200px; margin: 25px auto; padding: 12px 24px; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; text-decoration: none; text-align: center; font-weight: bold; border: none; cursor: pointer; }} .cta-button:hover {{ background: linear-gradient(135deg, #1d4ed8, #1e40af); }} .info-box {{ background-color: #f0f9ff; border-left: 4px solid #2563eb; padding: 15px; margin: 20px 0; }} .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #6b7280; background-color: #f8fafc; border-top: 1px solid #e5e7eb; }} .login-link {{ color: #2563eb; text-decoration: none; font-weight: bold; }} .login-link:hover {{ text-decoration: underline; }} .steps {{ margin: 20px 0; }} .step {{ margin-bottom: 10px; padding-left: 20px; position: relative; }} .step:before {{ content: "✓"; position: absolute; left: 0; color: #10b981; font-weight: bold; }} </style> </head> <body> <div class="email-container"> <div class="header"> <h1>🎓 Eagle Schools</h1> <p>Student Results Portal</p> </div> <div class="content"> <p>Dear <strong>{student_name}</strong>,</p> <p>We're pleased to inform you that your examination result has been successfully uploaded to our secure portal and is now available for viewing.</p> <div class="info-box"> <p><strong>Exam Number:</strong> {exam_number}</p> <p><strong>Access Key:</strong></p> <div class="access-key">{random_string}</div> </div> <div class="steps"> <p><strong>To access your result:</strong></p> <div class="step">Visit the Eagle Schools Results Portal</div> <div class="step">Enter your Exam Number: <strong>{exam_number}</strong></div> <div class="step">Use the Access Key provided above</div> </div> <a href="https://eagle-result-checker.vercel.app/login" class="cta-button"> View Your Result Now </a> <p>For security reasons, please keep your access key confidential and do not share it with others.</p> <p>If you encounter any issues accessing your result, please contact the school administration.</p> </div> <div class="footer"> <p>&copy; 2024 Eagle Schools. All rights reserved.</p> <p>This is an automated message. Please do not reply to this email.</p> <p>Access your result at: <a href="https://eagle-result-checker.vercel.app/login" class="login-link"> https://eagle-result-checker.vercel.app/login </a> </p> </div> </div> </body> </html> """
            send_simple_message(
                [{"email": "eagleschools@gmail.com"}, {"email": email}],
                f"📚 Your Result is Ready - Eagle Schools",
                message_body,
            )

            return redirect(url_for("results"))

        except Exception as e:
            return jsonify({"error": str(e)}), 500

        finally:
            db.close()

    return render_template("upload.html")


# ---------------------- DOWNLOAD RESULT --------------------
@app.route("/download_result/<int:result_id>")
def download_result(result_id):
    if 'exam_number' not in session:
        return redirect(url_for('login'))

    db = get_db()

    try:
        row = db.execute(text("""
            SELECT result_blob, exam_number, student_name
            FROM results WHERE id = :id
        """), {"id": result_id}).fetchone()

        if not row:
            return "Not found", 404

        if row.exam_number != session['exam_number']:
            return "Unauthorized", 403

        return app.response_class(
            response=row.result_blob,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment;filename={row.student_name}.pdf'}
        )

    finally:
        db.close()


# ---------------------- LOGIN --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        exam_number = request.form.get("exam_number")
        password = request.form.get("password")

        db = get_db()

        try:
            row = db.execute(
                text("SELECT * FROM results WHERE exam_number = :e"),
                {"e": exam_number}
            ).fetchone()

            if row and row.access_key == password:
                session['user_id'] = row.id
                session['exam_number'] = row.exam_number
                return redirect(url_for("results"))

            return render_template("login.html", error="Invalid credentials")

        finally:
            db.close()

    return render_template("login.html")


# ---------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------- STUDENT CHECK RESULT --------------------
@app.route("/student/result", methods=["GET", "POST"])
def student_check_result():
    if request.method == "POST":
        exam_number = request.form.get("exam_number")
        access_key = request.form.get("access_key")

        db = get_db()

        try:
            row = db.execute(text("""
                SELECT * FROM results
                WHERE exam_number = :e AND access_key = :a
            """), {"e": exam_number, "a": access_key}).fetchone()

            if row:
                return render_template("student_result.html",
                                       student_name=row.student_name,
                                       exam_number=row.exam_number,
                                       result_id=row.id,
                                       access_key=access_key)

            return render_template("check_result.html", error="Invalid credentials")

        finally:
            db.close()

    return render_template("check_result.html")


# ------------------------------------------------
# STATIC FILES
# ------------------------------------------------
@app.route("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")


@app.route("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js"), 200, {"Content-Type": "application/javascript"}


@app.route("/offline")
def offline():
    return render_template("offline.html")


# ------------------------------------------------
# RUN FLASK
# ------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
