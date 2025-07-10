from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Configure upload folder

#disable this line while "CLOUDINARY" is enabled

app.config['UPLOAD_FOLDER'] = 'static/uploads'  


#myssql database connection for local development
# db = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="KBABU0307",
#     database="marriage_proposal",
#     port=3306  # Default MySQL port, change if necessary
# )



# MySQL database connection

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
    photo_path TEXT
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

        # Save photo locally if uploaded
        # photo_path = None
        # if photo and photo.filename:
        #     photo_path = os.path.join('static', 'uploads', photo.filename)
        #     os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        #     photo.save(photo_path)
        #     photo_path = '/' + photo_path.replace('\\', '/')
        # else:
        #     photo_path = None

        # photo_filename = ''
        # if photo and photo.filename != '':
        #     photo_filename = secure_filename(photo.filename)
        #     photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
        #     photo.save(photo_path)
        # else:
        #     photo_path = None

        photo_filename = ''
        if photo and photo.filename != '':
            photo_filename = secure_filename(photo.filename)
            file_save_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            os.makedirs(os.path.dirname(file_save_path), exist_ok=True)
            photo.save(file_save_path)
            # photo_path = f"/static/uploads/{photo_filename}"  # Save this to DB
            photo_path = f"https://forever-begins.vercel.app/static/uploads/{photo_filename}"

        else:
            photo_path = None


        # Insert into MySQL
        query = "INSERT INTO proposals (proposer_name, proposee_name, message, photo_path) VALUES (%s, %s, %s, %s)"
        values = (proposer_name, proposee_name, message, photo_path if photo_path else None)
        cursor.execute(query, values)
        db.commit()

        return render_template("thankyou.html", proposer_name=proposer_name, photo_path=photo_path)

    except Exception as e:
        print("Error in /submit:", e)
        return f"Internal Server Error: {str(e)}", 500

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
                                   proposee=proposee_name, message=message, photo_path=photo_path)
        else:
            return f"No proposal found with ID {proposal_id}", 404
    return render_template('view_form.html')

@app.route('/submissions')
def all_submissions():
    cursor.execute("SELECT * FROM proposals")
    proposals = cursor.fetchall()
    return render_template('all_submissions.html', proposals=proposals)

if __name__ == '__main__':
    app.run(debug=True)
