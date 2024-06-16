import psycopg2
from urllib.parse import urlparse
import os

service_url = os.getenv('DATABASE_URL')
result = urlparse(service_url)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

# Connect to the database
conn = psycopg2.connect(
    dbname=database,
    user=username,
    password=password,
    host=hostname,
    port=port
)

cur = conn.cursor()

def update_prev(username, prev_id):
    update_prev = """
    UPDATE user_calls
    SET previous_id = %s
    WHERE username = %s;
    """
    cur.execute(update_prev, (prev_id, username))
    conn.commit()
    return 0

print(update_prev('FABIAN', 'FABIAN'))
