from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_DIR = '/app/db'
DB_PATH = os.path.join(DB_DIR, 'dodge_tracker.db')

# Define a password for edit and delete actions
VALID_PASSWORD = 'test'  # Replace with your desired password

def init_db():
    """Initialize the database with required tables."""
    try:
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)

        if not os.path.exists(DB_PATH):
            print(f"Creating database file: {DB_PATH}")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                dodge_count INTEGER DEFAULT 0
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dodges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                reason TEXT NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (name) REFERENCES friends (name)
            )
            """)
            conn.commit()
            print(f"Database initialized at {DB_PATH}")
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")

@app.route('/')
def index():
    """Display the main page with the list of friends and their dodge counts."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.name, COALESCE(f.dodge_count, 0) AS dodge_count, 
                   (SELECT reason FROM dodges WHERE name = f.name ORDER BY date DESC LIMIT 1) AS last_dodge_reason
            FROM friends f
        """)
        friends = cursor.fetchall()
        conn.close()
    except sqlite3.Error as e:
        return f"Database error: {e}", 500

    return render_template('index.html', friends=friends)


@app.route('/add_friend', methods=['POST'])
def add_friend():
    """Add a new friend."""
    name = request.form['name']
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO friends (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error adding friend.", 500
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete_friend', methods=['POST'])
def delete_friend():
    """Delete a friend."""
    name = request.form['name']
    password = request.form['password']

    # Validate the password
    if password != VALID_PASSWORD:
        return "Invalid password.", 403

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM friends WHERE name = ?", (name,))
        cursor.execute("DELETE FROM dodges WHERE name = ?", (name,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error deleting friend.", 500
    finally:
        conn.close()
    
    return redirect(url_for('index'))


@app.route('/edit_dodge', methods=['POST'])
def edit_dodge():
    """Edit a dodge record."""
    dodge_id = request.form.get('dodge_id')
    new_reason = request.form.get('new_reason')
    friend_name = request.form.get('name')  # Ensure this is included
    password = request.form.get('password')

    # Validate the password
    if password != VALID_PASSWORD:
        return "Invalid password.", 403

    # Validate the form data
    if not dodge_id or not new_reason or not friend_name:
        return "Missing dodge_id, new_reason, or name.", 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE dodges SET reason = ? WHERE id = ?", (new_reason, dodge_id))
        conn.commit()
    except sqlite3.Error as e:
        return "Error editing dodge.", 500
    finally:
        conn.close()
    
    return redirect(url_for('friend', name=friend_name))

@app.route('/delete_dodge', methods=['POST'])
def delete_dodge():
    """Delete a dodge record."""
    dodge_id = request.form.get('dodge_id')
    friend_name = request.form.get('name')  # Ensure this is included
    password = request.form.get('password')

    # Validate the password
    if password != VALID_PASSWORD:
        return "Invalid password.", 403

    # Validate the form data
    if not dodge_id or not friend_name:
        return "Missing dodge_id or name.", 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dodges WHERE id = ?", (dodge_id,))
        
        # Decrement the dodge count for the friend
        cursor.execute("UPDATE friends SET dodge_count = dodge_count - 1 WHERE name = ?", (friend_name,))
        conn.commit()
    except sqlite3.Error as e:
        return "Error deleting dodge.", 500
    finally:
        conn.close()
    

    return redirect(url_for('friend', name=friend_name))


@app.route('/friend/<name>')
def friend(name):
    """Display the list of dodges for a specific friend."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dodges WHERE name = ?", (name,))
        dodges = cursor.fetchall()
        conn.close()
    except sqlite3.Error as e:
        return "Error retrieving dodges.", 500
    
    return render_template('user.html', name=name, dodges=dodges)

@app.route('/add_dodge', methods=['POST'])
def add_dodge():
    """Add a new dodge entry and update the friend's dodge count."""
    name = request.form['name']
    reason = request.form['reason']
    date = request.form['date']
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO dodges (name, reason, date) VALUES (?, ?, ?)", (name, reason, date))
        cursor.execute("INSERT INTO friends (name) VALUES (?) ON CONFLICT(name) DO UPDATE SET dodge_count = dodge_count + 1", (name,))
        conn.commit()
    except sqlite3.Error as e:
        return "Error adding dodge.", 500
    finally:
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/edit_friend', methods=['POST'])
def edit_friend():
    """Edit a friend's name."""
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')
    password = request.form.get('password')

    # Validate the password
    if password != VALID_PASSWORD:
        return "Invalid password.", 403

    # Validate the form data
    if not old_name or not new_name:
        return "Missing old_name or new_name.", 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the old friend's name exists
        cursor.execute("SELECT * FROM friends WHERE name = ?", (old_name,))
        if cursor.fetchone() is None:
            return "Friend not found.", 404

        # Update the friend's name
        cursor.execute("UPDATE friends SET name = ? WHERE name = ?", (new_name, old_name))
        conn.commit()
    except sqlite3.Error as e:
        return "Error updating friend.", 500
    finally:
        conn.close()

    return redirect(url_for('index'))




if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5008)
