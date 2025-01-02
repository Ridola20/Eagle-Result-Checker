from flask import Flask, request, jsonify, render_template, g, redirect, url_for, session
import sqlite3
import requests
import random

def generate_random_number():
    # Generate a random 6-digit number
    random_number = random.randint(100000, 999999)
    
    # Return as a string
    return str(random_number)

# Database file path
DATABASE = './Results.db'

# Initialize Flask app
app = Flask(__name__)

app.config['SECRET_KEY'] = '1234567890'

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
        # Create the table if it does not exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                exam_number TEXT NOT NULL UNIQUE,
                result_blob BLOB NOT NULL,
                access_key TEXT NOT NULL
            )
        """)
        conn.commit()
        cursor.close()

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
        
        results = cursor.fetchall()
        return render_template('view_users.html', users=results, search_query=search_query)
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
        random_string = generate_random_number()

        if not student_name or not exam_number or not result_file or not passkey:
            return jsonify({'error': 'Missing required fields'}), 400

        try:
            cursor = get_db().cursor()
            
            cursor.execute("SELECT * FROM staff_passkey")
            valid_passkey = cursor.fetchone()[1]
            print(valid_passkey)

            if not valid_passkey:
                return jsonify({'error': 'Invalid passkey'}), 403
            elif str(passkey) != str(valid_passkey):
                return jsonify({'error': 'Invalid passkey'}), 403
            else:
                pass
            
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
                recipients = ["ridwansanusiessential@gmail.com"] 
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
                            Student Results Portal
                        </div>
                        <div class="content">
                            <p>Dear {student_name},</p>
                            <p>Your result has been successfully uploaded to the portal.</p>
                            <p>Your result access key is:</p>
                            <p class="access-key">{random_string}</p>
                            <p>Please use this access key to view or download your result securely from the portal.</p>
                            <p>Thank you for using our service!</p>
                        </div>
                        <div class="footer">
                            &copy; {2024} Student Results Portal. All rights reserved.
                        </div>
                    </div>
                </body>
                </html>
                """
                
                def send_simple_message():
                    response = requests.post(
                        "https://api.mailgun.net/v3/sandboxae7349da4b674887beddb068e4b9f714.mailgun.org/messages",
                        auth=("api", "33f678ed4aa713e446d0af703e615dd0-2e68d0fb-c5597279"),
                        data={"from": "Excited User <mailgun@sandboxae7349da4b674887beddb068e4b9f714.mailgun.org>",
                            "to": recipients, #"YOU@sandboxae7349da4b674887beddb068e4b9f714.mailgun.org"
                            "subject": subject,
                            "text": "Testing some Mailgun awesomeness!"})
                    print(f"Status Code: {response.status_code}")
                    print(f"Response: {response.text}")
                    return response

                send_simple_message()
                
                print("Emails sent successfully!")

            except Exception as e:
                print(f"Failed to send email: {str(e)}")

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

# Initialize the database and start the app
if __name__ == "__main__":
    # Check if database exists, initialize if not
    # if not os.path.exists(DATABASE):
    print("Initializing the database...")
    init_db()
    app.run(debug=True)
