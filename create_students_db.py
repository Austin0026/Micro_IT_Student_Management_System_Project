import sqlite3

def create_database():
    conn = sqlite3.connect('students.db')
    c = conn.cursor()

    # Create students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll TEXT NOT NULL,
            class TEXT NOT NULL
        )
    ''')

    # Create attendance table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
            status TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    ''')

    # Insert sample students (optional)
    sample_students = [
        ('Alice Johnson', '101', '10-A'),
        ('Bob Smith', '102', '10-A'),
        ('Charlie Lee', '103', '10-B')
    ]
    c.executemany('INSERT INTO students (name, roll, class) VALUES (?, ?, ?)', sample_students)

    conn.commit()
    conn.close()
    print("students.db created with tables and sample data.")

if __name__ == "__main__":
    create_database()
