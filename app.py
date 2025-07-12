from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
import sqlite3
from models import init_db, create_user, validate_user, get_user_profile
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'static/images'
Session(app)

if not os.path.exists('swap_skills.db'):
    init_db()

@app.before_request
def show_session():
    print("SESSION DATA:", session)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        try:
            create_user(name, email, password)
            flash("Registered successfully! You can now log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "danger")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = validate_user(email, password)
        if user:
            session['user_id'] = user[0]
            session['email'] = user[2]
            session['role'] = user[4]
            if user[4] == 'admin' or email == 'abcd@gmail.com':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out!", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in first", "warning")
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        skill_offered = request.form['skill_offered']
        skill_wanted = request.form['skill_wanted']
        availability = request.form['availability']
        location = request.form['location']
        is_public = 1 if request.form.get('is_public') == 'Public' else 0

        with sqlite3.connect('swap_skills.db', check_same_thread=False) as conn:
            c = conn.cursor()

            # Check if user already has a skill entry
            c.execute('SELECT id FROM skills WHERE user_id = ?', (user_id,))
            exists = c.fetchone()
            if exists:
                c.execute('''
                    UPDATE skills SET skill_offered = ?, skill_wanted = ?, availability = ?, is_public = ?, location = ?
                    WHERE user_id = ?
                ''', (skill_offered, skill_wanted, availability, is_public, location, user_id))
            else:
                c.execute('''
                    INSERT INTO skills (user_id, skill_offered, skill_wanted, availability, is_public, location)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, skill_offered, skill_wanted, availability, is_public, location))

        flash("Profile updated!", "success")
        return redirect(url_for('profile'))

    skills = get_user_profile(user_id)
    return render_template('profile.html', skills=skills)

@app.route('/send_request')
def send_request():
    return render_template('send_request.html')

@app.route('/browse')
def browse():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '')
    with sqlite3.connect('swap_skills.db', check_same_thread=False) as conn:
        c = conn.cursor()
        if query:
            c.execute('''
                SELECT skills.*, users.name FROM skills 
                JOIN users ON skills.user_id = users.id 
                WHERE skills.is_public = 1 AND skills.skill_offered LIKE ?
            ''', ('%' + query + '%',))
        else:
            c.execute('''
                SELECT skills.*, users.name FROM skills 
                JOIN users ON skills.user_id = users.id 
                WHERE skills.is_public = 1
            ''')
        results = c.fetchall()
    return render_template('browse.html', results=results, query=query)

@app.route('/send_swap/<int:receiver_id>/<skill>')
def send_swap_request(receiver_id, skill):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    sender_id = session['user_id']
    with sqlite3.connect('swap_skills.db', check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO swap_requests (sender_id, receiver_id, skill)
            VALUES (?, ?, ?)
        ''', (sender_id, receiver_id, skill))

    flash("Swap request sent!", "success")
    return redirect(url_for('browse'))

@app.route('/swap_requests')
def swap_requests():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with sqlite3.connect('swap_skills.db', check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT swap_requests.id, users.name, swap_requests.skill, swap_requests.status
            FROM swap_requests
            JOIN users ON swap_requests.sender_id = users.id
            WHERE receiver_id = ?
        ''', (user_id,))
        requests = c.fetchall()
    return render_template('swap_requests.html', requests=requests)

@app.route('/swap_action/<int:req_id>/<action>')
def swap_action(req_id, action):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if action in ['accept', 'reject', 'delete']:
        new_status = 'accepted' if action == 'accept' else 'rejected' if action == 'reject' else 'deleted'
        with sqlite3.connect('swap_skills.db', check_same_thread=False) as conn:
            c = conn.cursor()
            if new_status == 'deleted':
                c.execute('DELETE FROM swap_requests WHERE id = ?', (req_id,))
            else:
                c.execute('UPDATE swap_requests SET status = ? WHERE id = ?', (new_status, req_id))
        flash(f"Request {new_status}.", "info")

    return redirect(url_for('swap_requests'))

@app.route('/feedback/<int:swap_id>', methods=['GET', 'POST'])
def feedback(swap_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        rating = int(request.form['rating'])
        comment = request.form['comment']
        with sqlite3.connect('swap_skills.db', check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO feedback (swap_id, rating, comment) VALUES (?, ?, ?)',
                      (swap_id, rating, comment))
        flash("Feedback submitted!", "success")
        return redirect(url_for('dashboard'))

    return render_template('feedback.html', swap_id=swap_id)
@app.route('/admin')
def admin():
    if 'role' not in session or session['role'] != 'admin':
        flash("Unauthorized access. Admins only.", "danger")
        return redirect(url_for('login'))

    conn = sqlite3.connect('swap_skills.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    c.execute('SELECT * FROM feedback')
    feedbacks = c.fetchall()
    conn.close()

    return render_template('admin.html', users=users, feedbacks=feedbacks)

@app.route('/ban_user/<int:user_id>')
def ban_user(user_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    with sqlite3.connect('swap_skills.db', check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (user_id,))
    flash("User banned.", "danger")
    return redirect(url_for('admin'))

@app.route('/upload_pic', methods=['POST'])
def upload_pic():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    file = request.files['profile_pic']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    with sqlite3.connect('swap_skills.db', check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (filename, session['user_id']))

    flash("Profile picture updated!", "success")
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
