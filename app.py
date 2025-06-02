from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set a secure secret key

# --------------------- Database Initialization ---------------------
def init_db():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # Students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll TEXT NOT NULL,
            class TEXT NOT NULL
        )
    ''')

    # Attendance table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')

    # Grades table
    c.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject TEXT,
            grade TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')

    # Announcement
    c.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        date TEXT NOT NULL
        )
    ''')
    # Create messages table
    c.execute('''
     CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        content TEXT NOT NULL,
        timestamp TEXT,
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(receiver_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

# --------------------- Create Admin User ---------------------
def create_user(username, password, role='admin'):
    password_hash = generate_password_hash(password)
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', 
                  (username, password_hash, role))
    except sqlite3.IntegrityError:
        pass  # Skip if user already exists
    conn.commit()
    conn.close()

# --------------------- Login Required Decorator ---------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --------------------- Authentication Routes ---------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        c.execute('SELECT id, password_hash, role FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session['role'] = user[2]
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --------------------- Dashboard ---------------------
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# --------------------- Student Management ---------------------
@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll']
        class_name = request.form['class']
        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        c.execute("INSERT INTO students (name, roll, class) VALUES (?, ?, ?)", (name, roll, class_name))
        conn.commit()
        conn.close()
        return redirect('/view_students')
    return render_template('add_student.html')

@app.route('/view_students')
@login_required
def view_students():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()
    conn.close()
    return render_template('view_students.html', students=students)

# --------------------- Attendance ---------------------
@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    students = c.fetchall()

    if request.method == 'POST':
        date = request.form['date']
        for student in students:
            status = request.form.get(f'status_{student[0]}')
            c.execute("INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?)",
                      (student[0], date, status))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    conn.close()
    return render_template('mark_attendance.html', students=students)

@app.route('/view_attendance')
@login_required
def view_attendance():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT student_id, date, status FROM attendance")
    records = c.fetchall()
    conn.close()
    return render_template('view_attendance.html', records=records)

# --------------------- Grade Management ---------------------
@app.route('/add_grade', methods=['GET', 'POST'])
@login_required
def add_grade():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM students")
    students = c.fetchall()

    if request.method == 'POST':
        student_id = request.form['student_id']
        subject = request.form['subject']
        grade = request.form['grade']
        c.execute("INSERT INTO grades (student_id, subject, grade) VALUES (?, ?, ?)",
                  (student_id, subject, grade))
        conn.commit()
        conn.close()
        return redirect('/view_grades')

    conn.close()
    return render_template('add_grade.html', students=students)

@app.route('/view_grades')
@login_required
def view_grades():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute('''
        SELECT grades.id, students.name, grades.subject, grades.grade
        FROM grades
        JOIN students ON grades.student_id = students.id
    ''')
    grades = c.fetchall()
    conn.close()
    return render_template('view_grades.html', grades=grades)

from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        password_hash = generate_password_hash(password)

        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', 
                      (username, password_hash, role))
            conn.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')


# --------------------- Announcement Management ---------------------
from datetime import datetime

@app.route('/add_announcement', methods=['GET', 'POST'])
@login_required
def add_announcement():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect('students.db')
        c = conn.cursor()
        c.execute("INSERT INTO announcements (title, content, date) VALUES (?, ?, ?)",
                  (title, content, date))
        conn.commit()
        conn.close()
        return redirect('/view_announcements')
    return render_template('add_announcement.html')

@app.route('/view_announcements')
@login_required
def view_announcements():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("SELECT title, content, date, id FROM announcements ORDER BY date DESC")

    announcements = c.fetchall()
    conn.close()
    return render_template('view_announcements.html', announcements=announcements)

@app.route('/edit_announcement/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_announcement(id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        c.execute("UPDATE announcements SET title = ?, content = ? WHERE id = ?", (title, content, id))
        conn.commit()
        conn.close()
        return redirect(url_for('view_announcements'))

    c.execute("SELECT title, content FROM announcements WHERE id = ?", (id,))
    announcement = c.fetchone()
    conn.close()
    return render_template('edit_announcement.html', announcement=announcement, id=id)

@app.route('/delete_announcement/<int:id>')
@login_required
def delete_announcement(id):
    conn = sqlite3.connect('students.db')
    c = conn.cursor()
    c.execute("DELETE FROM announcements WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('view_announcements'))

from flask import session, jsonify
from datetime import datetime

@app.route('/messages')
@login_required
def messages():
    user_id = session['user_id']
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # Get all users except current user
    c.execute('SELECT id, username FROM users WHERE id != ?', (user_id,))
    contacts = c.fetchall()

    conn.close()
    return render_template('messages.html', contacts=contacts)

@app.route('/messages/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def message_thread(contact_id):
    user_id = session['user_id']
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    if request.method == 'POST':
        message_text = request.form['message']
        timestamp = datetime.now()
        c.execute('''
            INSERT INTO messages (sender_id, receiver_id, message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, contact_id, message_text, timestamp))
        conn.commit()

    # Fetch message history between current user and contact
    c.execute('''
        SELECT m.sender_id, u.username, m.message, m.timestamp
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?)
        OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.timestamp ASC
    ''', (user_id, contact_id, contact_id, user_id))
    messages = c.fetchall()
    conn.close()
    return render_template('message_thread.html', messages=messages, contact_id=contact_id)



# --------------------- Run App ---------------------
if __name__ == '__main__':
    init_db()
    create_user('admin', 'admin123')  # Only creates if not exists
    app.run(debug=True)
