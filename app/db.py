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

DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "users.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# creates db for users and locations
def create_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.executescript("""
        DROP TABLE IF EXISTS scores;
        DROP TABLE IF EXISTS address;
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
            points INTEGER NOT NULL,
            distance REAL NOT NULL
	);

	CREATE TABLE IF NOT EXISTS loc (
            loc_id INTEGER PRIMARY KEY AUTOINCREMENT,
	    lat REAL NOT NULL,
	    long REAL NOT NULL
        );
    """)
    """CREATE TABLE IF NOT EXISTS address (
            add_id INTEGER PRIMARY KEY AUTOINCREMENT,
            num INTEGER NOT NULL,
            street TEXT NOT NULL,
            city TEXT NOT NULL,
            region TEXT NOT NULL,
            post INTEGER NOT NULL
        );"""
    conn.commit()
    conn.close()

# add users to users database
def add_user(username, password):
    create_db()
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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row and check_password_hash(row["password_hash"], password)

# adds users scores
def add_score(username, points, distance, mode="untimed",  region="nyc"):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    id = cur.fetchone()
    if not id:
        conn.close()
        return False
    user_id = id["user_id"]
    cur.execute(
        "INSERT INTO scores (user_id, region, mode, points, distance) VALUES (?, ?, ?, ?, ?)",
        (user_id, region, mode, points, distance,)
    )
    conn.commit()
    conn.close()
    return True

# creates db for locations (only works for new york right now, so subject to change)
'''
def loc_db():
    count = 0
    conn = get_db_connection()
    cur = conn.cursor()
    with open('../../city_of_new_york.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            #print(row[0], row[1])
            if(count > 5000):
                break
            cur.execute("INSERT INTO loc (lat, long) VALUES (?, ?)", (row[1], row[0]))
            cur.execute("SELECT MAX(loc_id) FROM loc")
            #len = cur.fetchone()[0]
            #print(row[1], row[0])
            count += 1
    conn.commit()
    conn.close()
'''
# creates db for addresses
'''
def address_db():
    count = 0
    conn = get_db_connection()
    cur = conn.cursor()
    with open('../statewide.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            #print(row[0], row[1])
            if(count > 1000):
                break
            cur.execute("INSERT INTO address (num, street, city, region, post) VALUES (?, ?, ?, ?, ?)", (row[2], row[3], row[5], row[7], row[8]))
            cur.execute("SELECT MAX(add_id) FROM address")
            #len = cur.fetchone()[0]
            #print(row[1], row[0])
            count += 1
    conn.commit()
    conn.close()
'''

#gets random location, this is also subject to change with the use of Google Geocoding API in order to avoid unintellgible coords
def getRandLoc():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(loc_id) FROM loc;")
    len = cur.fetchone()[0]
    print(len)
    rand = random.randint(1, len)
    cur.execute("SELECT * FROM loc WHERE loc_id = ?", (rand,))
    rand_loc = cur.fetchone()
    lat_long = [rand_loc[1], rand_loc[2]]
    #print(lat_long)
    conn.close()
    return lat_long

# gets random address (should be used to ensure proper coords)
'''
def getRandAddress():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(add_id) FROM address;")
    len = cur.fetchone()[0]
    #print(len)
    rand = random.randint(0, len)
    cur.execute("SELECT * FROM address WHERE add_id = ?", (rand,))
    loc = cur.fetchone()
    address = f"{loc[1]} {loc[2]}, {loc[3]}, {loc[4]} {loc[5]}"
    #print(address)
    conn.close()
    return address
'''

#gets top scores to serve to leaderboard
def top_scores(region="nyc"):
    conn = get_db_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT u.username, s.points, s.distance
        FROM scores AS s
        JOIN users AS u ON u.user_id = s.user_id
        WHERE s.region = ?
        ORDER BY s.points DESC, s.distance ASC
        LIMIT 30;
    """, (region,))

    rows = cur.fetchall()
    conn.close()
    return rows

#create_db()
#loc_db()
