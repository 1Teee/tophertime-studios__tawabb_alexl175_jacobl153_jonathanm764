'''
TopherTime Studios - Tawab Berri, Alex Luo, Jacob Lukose, Jonathan Metzler
SoftDev
Spring 2025
p05 - DevoGuessr
'''
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import os
import random
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "game.db")

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# creates db for users and locations
def create_db():
    """Create database tables for users, scores, rounds, and locations"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.executescript("""
        DROP TABLE IF EXISTS rounds;
        DROP TABLE IF EXISTS scores;
        DROP TABLE IF EXISTS address;
        DROP TABLE IF EXISTS loc;  
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scores (
            score_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            region TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'untimed',
            move_mode TEXT NOT NULL DEFAULT 'move',
            points INTEGER NOT NULL,
            distance REAL NOT NULL,
            game_time REAL DEFAULT 0,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
	);

        CREATE TABLE IF NOT EXISTS rounds (
            round_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            region TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'untimed',
            move_mode TEXT NOT NULL DEFAULT 'move',
            round_number INTEGER NOT NULL,
            points INTEGER NOT NULL,
            distance REAL NOT NULL,
            round_time REAL DEFAULT 0,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime'))
        );

	CREATE TABLE IF NOT EXISTS loc (
        loc_id INTEGER PRIMARY KEY AUTOINCREMENT,
	    lat REAL NOT NULL,
	    long REAL NOT NULL,
        region TEXT NOT NULL DEFAULT 'nyc'
        );
    """)
    conn.commit()
    conn.close()

# add users to users database
def add_user(username, password):
    """Add a new user to the database with hashed password"""
    conn = get_db_connection()
    cur = conn.cursor()
    pw_hash = generate_password_hash(password)
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw_hash)
        )
        conn.commit()
        ok = True
    except sqlite3.IntegrityError:
        ok = False
    finally:
        conn.close()
    return ok

# check users password and username
def check_user(username, password):
    """Verify user credentials against database"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT password_hash FROM users WHERE username = ?", 
        (username,)
    )
    row = cur.fetchone()
    conn.close()
    return row and check_password_hash(row["password_hash"], password)

# adds users scores
def add_score(
    username, 
    points, 
    distance, 
    mode="untimed", 
    region="nyc", 
    move_mode="move", 
    game_time=0
):
    """Add a game score to the database for a user"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    id = cur.fetchone()
    if not id:
        conn.close()
        return False
    user_id = id["user_id"]
    
    cur.execute(
        """INSERT INTO scores (user_id, region, mode, move_mode, points, 
        distance, game_time, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, 
        datetime('now', 'localtime'))""",
        (user_id, region, mode, move_mode, points, distance, game_time)
    )
    
    conn.commit()
    conn.close()
    return True

def import_csv_to_loc(region, csv_path, sample: int=500):
    """Import location coordinates from CSV file to database"""
    conn = get_db_connection()
    cur  = conn.cursor()

    with open(csv_path, newline='', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        next(reader, None)
        rows = list(reader)                
        for row in random.sample(rows, min(sample, len(rows))):
            lon = float(row[0])            
            lat = float(row[1])            
            cur.execute(
                "INSERT INTO loc (lat, long, region) VALUES (?, ?, ?)",
                (lat, lon, region)
            )
    conn.commit()
    conn.close()

def import_folder_to_loc(region, folder_path, sample: int=500):
    """Import all CSV files from a folder to location database"""
    for file in os.listdir(folder_path):       
        if file.lower().endswith(".csv"):     
            csv_path = os.path.join(folder_path, file)
            import_csv_to_loc(region, csv_path, sample)

# gets random location, this is also subject to change with the use of
# Google Geocoding API in order to avoid unintelligible coords
def getRandLoc(region="nyc"):
    """Get a random location from the database for the specified region"""
    conn = get_db_connection()
    cur = conn.cursor()
    if region == "world":
        cur.execute("SELECT lat, long FROM loc ORDER BY RANDOM() LIMIT 1")
    else:
        cur.execute(
            """SELECT lat, long FROM loc WHERE region = ? 
            ORDER BY RANDOM() LIMIT 1""",
            (region,)
        )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise ValueError("No coordinates found for region " + region + ".")
    return [row["lat"], row["long"]]

#gets top scores to serve to leaderboard
def top_scores(region="nyc", move_mode=None):
    """Get top 25 scores for leaderboard from database"""
    conn = get_db_connection()
    cur  = conn.cursor()

    if move_mode:
        cur.execute("""
            SELECT u.username, s.points, s.distance, s.game_time, s.timestamp
            FROM scores AS s
            JOIN users AS u ON u.user_id = s.user_id
            WHERE s.region = ? AND s.move_mode = ?
            ORDER BY s.points DESC, s.distance ASC
            LIMIT 25;
        """, (region, move_mode))
    else:
        cur.execute("""
            SELECT u.username, s.points, s.distance, s.game_time, s.timestamp
            FROM scores AS s
            JOIN users AS u ON u.user_id = s.user_id
            WHERE s.region = ?
            ORDER BY s.points DESC, s.distance ASC
            LIMIT 25;
        """, (region,))

    rows = cur.fetchall()
    conn.close()
    
    formatted_rows = []
    for row in rows:
        formatted_row = dict(row)
        formatted_row['timestamp'] = datetime.strptime(
            row['timestamp'], '%Y-%m-%d %H:%M:%S'
        )
        formatted_rows.append(formatted_row)
    
    return formatted_rows

def get_user_stats(username):
    """Get user statistics including completed games and scores"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return None
        
    user_id = user["user_id"]
    
    cur.execute("""
        SELECT 
            COUNT(*) as completed_games,
            AVG(points) as avg_score,
            MAX(points) as max_score
        FROM scores
        WHERE user_id = ?
    """, (user_id,))
    
    stats = cur.fetchone()
    conn.close()
    
    return {
        'completed_games': stats['completed_games'] or 0,
        'avg_score': round(stats['avg_score'] or 0),
        'max_score': stats['max_score'] or 0
    }

def get_user_games(username):
    """Get user's game history separated by move and nomove modes"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return None
        
    user_id = user["user_id"]
    
    # Get games for move mode
    cur.execute("""
        SELECT region, points, distance, game_time, timestamp
        FROM scores
        WHERE user_id = ? AND move_mode = 'move'
        ORDER BY timestamp DESC;
    """, (user_id,))
    move_games = cur.fetchall()
    
    # Get games for no move mode
    cur.execute("""
        SELECT region, points, distance, game_time, timestamp
        FROM scores
        WHERE user_id = ? AND move_mode = 'nomove'
        ORDER BY timestamp DESC;
    """, (user_id,))
    nomove_games = cur.fetchall()
    
    conn.close()
    
    formatted_move = []
    for row in move_games:
        formatted_row = dict(row)
        formatted_row['timestamp'] = datetime.strptime(
            row['timestamp'], '%Y-%m-%d %H:%M:%S'
        )
        formatted_move.append(formatted_row)
    
    formatted_nomove = []
    for row in nomove_games:
        formatted_row = dict(row)
        formatted_row['timestamp'] = datetime.strptime(
            row['timestamp'], '%Y-%m-%d %H:%M:%S'
        )
        formatted_nomove.append(formatted_row)
    
    return {
        'move_games': formatted_move,
        'nomove_games': formatted_nomove
    }

    