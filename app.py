from flask import Flask, render_template
import requests
from datetime import datetime
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

DATABASE = 'server_status.db'

servers = {
    "Main CS Server": "https://www.cs.odu.edu/~zeil/cs252/latest/Public/loggingin/",
    "Accounts Server": "https://accounts.cs.odu.edu/",
    "Unix and Linux Services": "https://systems.cs.odu.edu/Unix_and_Linux_Services/",
    "Computer Science Systems": "https://systems.cs.odu.edu/"
}

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS server_status (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            server_name TEXT,
                            status INTEGER,
                            response_time REAL,
                            headers TEXT,
                            last_checked TEXT
                          )''')
        conn.commit()
    print("Database initialized.")

def save_status_to_db(server_name, status_info):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO server_status (server_name, status, response_time, headers, last_checked)
                          VALUES (?, ?, ?, ?, ?)''',
                       (server_name, status_info['status'], status_info['response_time'], str(status_info['headers']), status_info['last_checked']))
        conn.commit()
        print(f"Saved status to DB for {server_name}: {status_info}")

def check_server_status(url):
    try:
        response = requests.get(url)
        headers = dict(response.headers)
        return {
            "status": response.status_code == 200,
            "response_time": response.elapsed.total_seconds(),
            "headers": headers
        }
    except requests.ConnectionError:
        return {
            "status": False,
            "response_time": None,
            "headers": None
        }

def check_servers():
    for name, url in servers.items():
        result = check_server_status(url)
        status_info = {
            "status": result["status"],
            "response_time": result["response_time"],
            "headers": result["headers"],
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_status_to_db(name, status_info)

@app.route('/')
def index():
    statuses = {}
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for name in servers.keys():
            cursor.execute('''SELECT status, response_time, headers, last_checked
                              FROM server_status
                              WHERE server_name = ?
                              ORDER BY last_checked DESC
                              LIMIT 1''', (name,))
            status_info = cursor.fetchone()
            print(f"Retrieved status for {name}: {status_info}")
            if status_info:
                statuses[name] = {
                    "status": bool(status_info[0]),
                    "response_time": status_info[1],
                    "headers": eval(status_info[2]),
                    "last_checked": status_info[3]
                }
    print(f"Statuses: {statuses}")
    return render_template('index.html', statuses=statuses)

@app.route('/historical')
def historical():
    historical_data = {}
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        for name in servers.keys():
            cursor.execute('''SELECT status, last_checked
                              FROM server_status
                              WHERE server_name = ?
                              ORDER BY last_checked DESC''', (name,))
            data = cursor.fetchall()
            historical_data[name] = [{"status": bool(row[0]), "last_checked": row[1]} for row in data]
    return render_template('historical.html', historical_data=historical_data)

if __name__ == '__main__':
    init_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_servers, trigger="interval", minutes=10)
    scheduler.start()
    app.run(debug=True)
