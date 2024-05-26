from flask import Flask, render_template
import requests
from datetime import datetime

app = Flask(__name__)

servers = {
    "Main CS Server": "https://www.cs.odu.edu/~zeil/cs252/latest/Public/loggingin/",
    "Accounts Server": "https://accounts.cs.odu.edu/"
}

def check_server_status(url):
    try:
        response = requests.get(url)
        return response.status_code == 200, response.elapsed.total_seconds()
    except requests.ConnectionError:
        return False, None

@app.route('/')
def index():
    statuses = {}
    for name, url in servers.items():
        status, response_time = check_server_status(url)
        statuses[name] = {
            "status": status,
            "response_time": response_time,
            "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    return render_template('index.html', statuses=statuses)

if __name__ == '__main__':
    app.run(debug=True)
