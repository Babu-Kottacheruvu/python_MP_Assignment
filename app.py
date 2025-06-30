from flask import Flask, render_template, request, redirect, url_for
import cloudinary
import cloudinary.uploader
import mysql.connector
import os

app = Flask(__name__)

cloudinary.config(
    cloud_name="dne1bro85",
    api_key="517532446814286",
    api_secret="clFK95-4gNTjThGMKUYhM4DF6n4"
)


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
    photo_url TEXT
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

        # Upload to Cloudinary
        photo_url = None
        if photo:
            upload_result = cloudinary.uploader.upload(photo)
            photo_url = upload_result.get('secure_url')

        # Insert into MySQL
        query = "INSERT INTO proposals (proposer_name, proposee_name, message, photo_url) VALUES (%s, %s, %s, %s)"
        values = (proposer_name, proposee_name, message, photo_url)
        cursor.execute(query, values)
        db.commit()

        return render_template("thankyou.html", proposer_name=proposer_name, photo_url=photo_url)

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

        cursor.execute("SELECT proposer_name, proposee_name, message, photo_url FROM proposals WHERE id = %s", (proposal_id,))
        result = cursor.fetchone()

        if result:
            proposer_name, proposee_name, message, photo_url = result
            return render_template('view.html', id=proposal_id, proposer=proposer_name,
                                   proposee=proposee_name, message=message, photo_url=photo_url)
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
