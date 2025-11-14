from flask import Flask, request, jsonify, render_template, g, redirect, url_for, session
import sqlite3
import requests
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_random_number():
    # Generate a random 6-digit number
    random_number = random.randint(100000, 999999)
    return str(random_number)

# Use /tmp directory for Vercel, local for development
DATABASE = '/tmp/Results.db' if 'VERCEL' in os.environ else './Results.db'

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key-change-in-production')

def send_simple_message(to_recipients: list, subject: str, html: str) -> None:
    """Send email via Brevo API"""
    api_key = os.getenv('BREVO_API_KEY')
    
    if not api_key:
        print("BREVO_API_KEY not found in environment variables")
        return
    
    payload = {
        "sender": {
            "name": "Eagle Schools Results",
            "email": "funkesanusi8@gmail.com"
        },
        "to": to_recipients,
        "subject": subject,
        "htmlContent": html,
    }
    
    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    
    # Check if the request was successful
    if response.status_code == 201:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email. Status: {response.status_code}, Response: {response.text}")

# Function to get database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.execute("PRAGMA journal_mode=WAL;")
    return db

# Close database connection on app teardown
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Function to initialize the database and create the table if it doesn't exist
def init_db():
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        # Create the results table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                exam_number TEXT NOT NULL UNIQUE,
                result_blob BLOB NOT NULL,
                access_key TEXT NOT NULL
            )
        """)
        
        # Create staff passkey table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_passkey (
                id INTEGER PRIMARY KEY,
                passkey TEXT NOT NULL
            )
        """)
        
        # Insert default passkey if not exists
        cursor.execute("SELECT * FROM staff_passkey WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO staff_passkey (id, passkey) VALUES (1, ?)", 
                          (os.getenv('DEFAULT_PASSKEY', 'admin123'),))
        
        conn.commit()
        cursor.close()

# Initialize database before first request
@app.before_request
def initialize_database():
    init_db()

# Home route
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/results', methods=['GET', 'POST'])
def results():
    cursor = get_db().cursor()
    search_query = request.form.get('search_query', '').strip()  # Get search input
    try:
        if search_query:
            # Search query to filter results
            cursor.execute("""
                SELECT * FROM results
                WHERE student_name LIKE ? OR exam_number LIKE ?
            """, (f'%{search_query}%', f'%{search_query}%'))
        else:
            # Display all results if no search query
            cursor.execute("SELECT * FROM results")
        
        results_data = cursor.fetchall()
        return render_template('view_users.html', users=results_data, search_query=search_query)
    except Exception as e:
        return render_template('view_users.html', error=str(e))
    finally:
        cursor.close()

@app.route('/upload', methods=['GET', 'POST'])
def upload_result():
    if request.method == 'POST':
        data = request.form
        student_name = data.get('student_name')
        exam_number = data.get('exam_number')
        passkey = data.get('staff_passkey')  # Get the passkey from the form
        result_file = request.files.get('result_blob')
        email = data.get('email')
        random_string = generate_random_number()

        if not student_name or not exam_number or not result_file or not passkey:
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            cursor = get_db().cursor()
            
            cursor.execute("SELECT * FROM staff_passkey")
            valid_passkey = cursor.fetchone()[1]

            if not valid_passkey:
                return jsonify({'error': 'Invalid passkey'}), 403
            elif str(passkey) != str(valid_passkey):
                return jsonify({'error': 'Invalid passkey'}), 403
            
            # Convert file to binary
            result_blob = result_file.read()

            # Check if the exam number already exists
            cursor.execute("SELECT * FROM results WHERE exam_number = ?", (exam_number,))
            existing_result = cursor.fetchone()

            if existing_result:
                # Delete the existing result
                cursor.execute("DELETE FROM results WHERE exam_number = ?", (exam_number,))

            cursor.execute("""
                INSERT INTO results (student_name, exam_number, result_blob, access_key)
                VALUES (?, ?, ?, ?)
            """, (student_name, exam_number, result_blob, random_string))
            get_db().commit()
            cursor.close()

            try:
                # Email content
                subject = f"Dear {student_name}, your result has been uploaded"
                
                # Format recipients properly for Brevo API
                recipients = [{"email": "eagleschools@gmail.com"}, {"email": email}]
                
                message_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 0;
                            background-color: #f4f4f4;
                        }}
                        .email-container {{
                            max-width: 600px;
                            margin: 20px auto;
                            background: #ffffff;
                            padding: 20px;
                            border-radius: 8px;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        }}
                        .header {{
                            background-color: #4CAF50;
                            color: white;
                            padding: 10px 20px;
                            text-align: center;
                            font-size: 20px;
                            font-weight: bold;
                            border-radius: 8px 8px 0 0;
                        }}
                        .content {{
                            padding: 20px;
                            line-height: 1.6;
                            color: #333333;
                        }}
                        .content p {{
                            margin: 0 0 10px;
                        }}
                        .access-key {{
                            font-size: 18px;
                            color: #4CAF50;
                            font-weight: bold;
                            background-color: #f8f9fa;
                            padding: 10px;
                            border-radius: 5px;
                            text-align: center;
                            margin: 15px 0;
                        }}
                        .footer {{
                            text-align: center;
                            padding: 10px;
                            font-size: 12px;
                            color: #888888;
                            border-top: 1px solid #eeeeee;
                        }}
                    </style>
                </head>
                <body>
                    <div class="email-container">
                        <div class="header">
                            Eagle Schools - Student Results Portal
                        </div>
                        <div class="content">
                            <p>Dear {student_name},</p>
                            <p>Your result has been successfully uploaded to the portal.</p>
                            <p>Your result access key is:</p>
                            <p class="access-key">{random_string}</p>
                            <p>Please use this access key to view or download your result securely from the portal.</p>
                            <p><strong>Exam Number:</strong> {exam_number}</p>
                            <p>Thank you for using our service!</p>
                        </div>
                        <div class="footer">
                            &copy; 2024 Eagle Schools. All rights reserved.
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Send the email using the function defined above
                send_simple_message(recipients, subject, message_body)
                print("Result uploaded and email sent successfully!")

            except Exception as e:
                print(f"Email sending failed: {str(e)}")
                # Don't return error here, just log it since the result was uploaded successfully

            # Redirect to the results page
            return redirect(url_for('results'))
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()

    return render_template('upload.html')

@app.route('/download_result/<int:result_id>')
def download_result(result_id):
    # Check if user is logged in
    if 'exam_number' not in session:
        return redirect(url_for('login'))  # If not logged in, redirect to login

    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT result_blob, exam_number, student_name FROM results WHERE id=?", (result_id,))
        result = cursor.fetchone()

        if result:
            # Check if the result belongs to the logged-in user
            if result[1] != session['exam_number']:
                return jsonify({'error': 'You are not authorized to download this result'}), 403  # Unauthorized

            return app.response_class(
                response=result[0],
                status=200,
                mimetype='application/pdf',  # Adjust MIME type if needed
                headers={'Content-Disposition': f'attachment;filename={result[2]} result.pdf'}
            )
        else:
            return jsonify({'error': 'Result not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        exam_number = request.form.get('exam_number')
        password = request.form.get('password')
        
        # Validate credentials (this is a simplified version, in production, use hashed passwords)
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM results WHERE exam_number=?", (exam_number,))
        student = cursor.fetchone()

        if student and student[4] == password:  # Assuming password is at index 4
            session['user_id'] = student[0]  # Store the student's ID in the session
            session['exam_number'] = student[2]  # Assuming exam number is at index 1
            return redirect(url_for('results'))  # Redirect to results or dashboard page
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user session data
    session.pop('exam_number', None)
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cursor = get_db().cursor()
    try:
        # Get total students count
        cursor.execute("SELECT COUNT(*) FROM results")
        total_results = cursor.fetchone()[0]
        
        # Get recent activity
        cursor.execute("SELECT MAX(id) FROM results")
        last_upload_id = cursor.fetchone()[0]
        
        return render_template('dashboard.html', 
                             total_students=total_results,
                             total_results=total_results,
                             last_upload=f"Result ID: {last_upload_id}" if last_upload_id else "No uploads yet")
    except Exception as e:
        return render_template('dashboard.html', error=str(e))
    finally:
        cursor.close()

@app.route('/student/result', methods=['GET', 'POST'])
def student_check_result():
    if request.method == 'POST':
        exam_number = request.form.get('exam_number')
        access_key = request.form.get('access_key')
        
        cursor = get_db().cursor()
        try:
            cursor.execute("SELECT * FROM results WHERE exam_number=? AND access_key=?", (exam_number, access_key))
            result = cursor.fetchone()
            
            if result:
                return render_template('student_result.html', 
                                     student_name=result[1],
                                     exam_number=result[2],
                                     result_id=result[0],
                                     access_key=access_key)
            else:
                return render_template('check_result.html', 
                                     error="Invalid exam number or access key")
        except Exception as e:
            return render_template('check_result.html', error=str(e))
        finally:
            cursor.close()
    
    return render_template('check_result.html')

@app.route('/bulk_upload', methods=['GET', 'POST'])
def bulk_upload():
    if request.method == 'POST':
        # Handle bulk CSV upload
        if 'csv_file' not in request.files:
            return render_template('bulk_upload.html', error="No file selected")
        
        csv_file = request.files['csv_file']
        if csv_file.filename == '':
            return render_template('bulk_upload.html', error="No file selected")
        
        if csv_file and csv_file.filename.endswith('.csv'):
            # Process CSV file
            try:
                import csv
                import io
                
                stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                
                success_count = 0
                error_count = 0
                
                for row in csv_reader:
                    try:
                        # Process each row
                        cursor = get_db().cursor()
                        random_string = generate_random_number()
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO results 
                            (student_name, exam_number, result_blob, access_key) 
                            VALUES (?, ?, ?, ?)
                        """, (row['student_name'], row['exam_number'], b'', random_string))
                        
                        get_db().commit()
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error processing row: {e}")
                    finally:
                        cursor.close()
                
                return render_template('bulk_upload.html', 
                                     success=f"Successfully processed {success_count} records. Errors: {error_count}")
                
            except Exception as e:
                return render_template('bulk_upload.html', error=f"Error processing CSV: {str(e)}")
    
    return render_template('bulk_upload.html')

# Initialize the database and start the app
if __name__ == "__main__":
    init_db()
    app.run(debug=True)