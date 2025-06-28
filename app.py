from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# MySQL connection
db = mysql.connector.connect(
    host=os.environ['DB_HOST'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME'],
    port=int(os.environ.get('DB_PORT', 3306))
)
cursor = db.cursor()

# Create proposals table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS proposals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proposer_name VARCHAR(100),
    proposee_name VARCHAR(100),
    message TEXT,
    photo_path VARCHAR(255)
)
""")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        proposer_name = request.form.get('proposerName')
        proposee_name = request.form.get('proposeeName')
        message = request.form.get('message')
        photo = request.files.get('photo')

        if not proposer_name or not proposee_name or not message:
            return "Please fill in all required fields!", 400

        photo_path = None
        if photo and photo.filename != '':
            photo_filename = secure_filename(photo.filename)
            full_path = os.path.join("/tmp", photo_filename)  # Use /tmp for Vercel
            photo.save(full_path)
            photo_path = f"uploads/{photo_filename}"  # Just logical, won't work on Vercel

        query = "INSERT INTO proposals (proposer_name, proposee_name, message, photo_path) VALUES (%s, %s, %s, %s)"
        values = (proposer_name, proposee_name, message, photo_path)
        cursor.execute(query, values)
        db.commit()

        return redirect(url_for('thank_you', proposer_name=proposer_name))

    except Exception as e:
        print("🔥 ERROR in /submit:", e)
        return f"Internal Server Error: {str(e)}", 500

    # proposer_name = request.form.get('proposerName')
    # proposee_name = request.form.get('proposeeName')
    # message = request.form.get('message')
    # photo = request.files.get('photo')

    # if not proposer_name or not proposee_name or not message:
    #     return "Please fill in all required fields!", 400

    # # Handle photo upload - FIXED VERSION
    # photo_path = None
    # if photo and photo.filename != '':
    #     photo_filename = secure_filename(photo.filename)
    #     # Save file to disk
    #     full_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
    #     photo.save(full_path)
    #     # Store only the relative path for the database (uploads/filename.jpg)
    #     photo_path = f"uploads/{photo_filename}"

    # # Insert into database
    # query = "INSERT INTO proposals (proposer_name, proposee_name, message, photo_path) VALUES (%s, %s, %s, %s)"
    # values = (proposer_name, proposee_name, message, photo_path)
    # cursor.execute(query, values)
    # db.commit()

    # return redirect(url_for('thank_you', proposer_name=proposer_name))

@app.route('/thank-you')
def thank_you():
    proposer_name = request.args.get('proposer_name', 'Someone Special')
    return render_template('thankyou.html', proposer_name=proposer_name)

@app.route('/view', methods=['GET', 'POST'])
def view_proposal():
    if request.method == 'POST':
        proposal_id = request.form.get('proposal_id')
        if not proposal_id.isdigit():
            return "Invalid ID", 400

        cursor.execute("SELECT proposer_name, proposee_name, message, photo_path FROM proposals WHERE id = %s", (proposal_id,))
        result = cursor.fetchone()

        if result:
            proposer_name, proposee_name, message, photo_path = result
            return render_template('view.html', id=proposal_id, proposer=proposer_name,
                                   proposee=proposee_name, message=message, photo=photo_path)
        else:
            return f"No proposal found with ID {proposal_id}", 404
    return render_template('view_form.html')


@app.route('/submissions')
def all_submissions():
    cursor.execute("SELECT * FROM proposals")
    proposals = cursor.fetchall()
    return render_template('all_submissions.html', proposals=proposals)


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)