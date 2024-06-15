import json
import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import requests
from flask import Flask, jsonify, make_response
from flask_cors import CORS

# Parse service url
service_url = os.getenv("DATABASE_URL")
result = urlparse(service_url)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

# Connect to the database
conn = psycopg2.connect(
    dbname=database, user=username, password=password, host=hostname, port=port
)

cur = conn.cursor()


app = Flask(__name__)

origins = ["https://apostats.vercel.app", "http://localhost:3000"]

cors = CORS(app, resources={r"/*": {"origins": origins}})

# cors = CORS(
#    app,
#    resources={
#        r"/get_all_calls": {"origins": origins},
#        r"/get_fabian": {"origins": origins},
#        r"/change_date": {"origins": origins},
#    },
# )


all_calls = {
    "JULIA": 0,
    "MILLA": 0,
    "VALDEMAR": 0,
    "SOFIA": 0,
    "FABIAN": 0,
}


UsersKundtjanst = {
    "JULIA": "0104102466",
    "MILLA": "0104104951",
    "VALDEMAR": "0104102495",
    "SOFIA": "0104102496",
    "FABIAN": "0104104956",
}

UsersAPI = {
    "0104104956": os.environ["TELAVOX_API_KEY_FABIAN"],
    "0104102466": os.environ["TELAVOX_API_KEY_JULIA"],
    "0104102496": os.environ["TELAVOX_API_KEY_SOFIA"],
    "0104102495": os.environ["TELAVOX_API_KEY_VALDEMAR"],
    "0104104951": os.environ["TELAVOX_API_KEY_MILLA"],
}


def clear_calls():
    global all_calls
    for i in all_calls:
        all_calls[i] = 0


def getCurrentDate():
    current_date = datetime.now()
    todayDate = current_date.strftime("%Y-%m-%d")
    return todayDate


# DB-funcs
def add_one_call(username):
    update_sql = """
    UPDATE user_calls
    SET calls_count = calls_count + 1
    WHERE username = %s;
    """
    print(cur.execute(update_sql, (username,)))
    conn.commit()
    return 0


def update_prev(username, prev_id):
    update_prev = """
    UPDATE user_calls
    SET previous_id = %s
    WHERE username = %s;
    """
    cur.execute(
        update_prev,
        (
            prev_id,
            username,
        ),
    )
    conn.commit()
    return 0


def check_prev(username):
    check_prev = """
    SELECT previous_id FROM user_calls WHERE username = %s;
    """
    try:
        cur.execute(check_prev, (username,))
        result = cur.fetchone()
        if result is not None:
            print(f"User {username} has {result[0]}")
            return result[0]
        else:
            print(f"User {username} not found")
            return None
    except Exception as e:
        print(f"An error occured: {e}")
        return None


def fetch_all_db_calls():
    fetch_db_calls = """
    SELECT username, calls_count FROM user_calls;
    """
    cur.execute(fetch_db_calls)
    conn.commit()
    return 0


def countCallsForAllUsers():
    global today_date
    for username, user_id in UsersKundtjanst.items():
        USER_API = UsersAPI.get(user_id)
        headers = {
            "Authorization": f"Bearer {USER_API}",
        }
        params = {
            "fromDate": getCurrentDate(),
            "toDate": getCurrentDate(),
        }
        try:
            response = requests.get(
                "https://api.telavox.se/calls", headers=headers, params=params
            )
            response.raise_for_status()
            incoming_calls = response.json().get("incoming", [])

            if incoming_calls:
                latest_call_id = incoming_calls[0]["callId"]
                print(latest_call_id)
                if check_prev(username) != latest_call_id:
                    add_one_call(username)
                    print(f"{username} took a call. Added one call.")
                    update_prev(username, latest_call_id)
                    print(latest_call_id)

        except requests.exceptions.RequestException as req_err:
            print(f"Request exception occurred for {username}: {req_err}")
            return 209

    return 0


def is_sum_greater(data):
    return sum(data.values())


# Setting previous_calls & today_date
today_date = getCurrentDate()


# app.routes
@app.route("/get_fabian", methods=["GET"])
def get_fabian():
    add_one_call("FABIAN")
    return "Finish"


@app.route("/change_date", methods=["GET"])
def change_date():
    global today_date
    today_date = "2024-01-10"
    return "Date Changed"


previous_sum = 0


@app.route("/get_all_calls", methods=["GET"])
def get_all_calls():
    global today_date
    print(today_date)
    print(getCurrentDate())
    if today_date != getCurrentDate():
        today_date = getCurrentDate()
        cur.execute("UPDATE user_calls SET calls_count =0;")
        conn.commit()

    countCallsForAllUsers()
    cur.execute("SELECT username, calls_count FROM user_calls;")

    user_calls = cur.fetchall()

    calls_dict = {username: calls_count for username, calls_count in user_calls}

    return jsonify(calls_dict)


if __name__ == "__main__":
    app.run(debug=True)
