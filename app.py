from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder='.')

DATABASE_PATH = os.environ.get('DATABASE_PATH', '/data/leaderboard.db')


def get_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    try:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                display_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                pct INTEGER NOT NULL,
                correct INTEGER NOT NULL,
                streak INTEGER NOT NULL,
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        db.close()
        print(f"[DB] Initialized at {DATABASE_PATH}", flush=True)
    except Exception as e:
        print(f"[DB] Init error: {e}", flush=True)


# Called at import time so gunicorn initializes the DB
init_db()


@app.route('/api/leaderboard')
def get_leaderboard():
    try:
        db = get_db()
        rows = db.execute('''
            SELECT display_name, score, pct, correct, streak, date
            FROM leaderboard
            ORDER BY score DESC, pct DESC
            LIMIT 15
        ''').fetchall()
        db.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        print(f"[DB] GET error: {e}", flush=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/leaderboard/save', methods=['POST'])
def save_score():
    try:
        data = request.get_json()
        print(f"[DB] Save request: {data}", flush=True)
        name = str(data.get('display_name', '')).upper().strip()
        name = ''.join(c for c in name if c.isalnum() or c in ' _-')[:20]
        if not name:
            return jsonify({'error': 'Name required'}), 400

        db = get_db()
        db.execute('''
            INSERT INTO leaderboard (display_name, score, pct, correct, streak, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            name,
            int(data.get('score', 0)),
            int(data.get('pct', 0)),
            int(data.get('correct', 0)),
            int(data.get('streak', 0)),
            data.get('date', datetime.now().strftime('%Y-%m-%d'))
        ))
        db.commit()
        db.close()
        print(f"[DB] Saved: {name}", flush=True)
        return jsonify({'success': True})
    except Exception as e:
        print(f"[DB] Save error: {e}", flush=True)
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
