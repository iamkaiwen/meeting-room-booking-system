from flask import Flask, jsonify, request, Response, session
import mysql.connector

from booking_system import BookingSystem
from user_system import UserSystem

# connect to database
db_config = {
    'host': 'db',
    'port': '3306',
    'user': 'kaiwen',
    'password': 'kai',
    'database': 'meeting-rooms-booking-system',
    'raise_on_warnings': True
}

try:
    print("Connect to database...")
    cnx = mysql.connector.connect(**db_config)
    print("[Success] Server connected to database")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("[Failed] Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("[Failed] Database does not exist")
    else:
        print(err)

# initialize user system
uSys = UserSystem(cnx)

# initialize booking system
bSys = BookingSystem(cnx)

# initialize web app
app = Flask(__name__)
app.secret_key = b'\xc1.\x97y\xff\x13&\xa1}\xe2\xc3a\x91\x9d\x9f\xc8'

@app.route('/')
def home():
    return "<h1>Welcome to Meeting Room Booking System!</h1>"

@app.route('/accounts', methods=['POST'])
def accounts():
    return uSys.create(request.form)

@app.route('/login', methods=['POST'])
def login():
    resp = uSys.login(request.form)
    if resp[0] == "Login success":
        session['name'] = resp[1]
        session['email'] = request.form['email']
        resp = resp[0]
    return resp

@app.route('/bookings', methods=['GET', 'POST', 'DELETE'])
def bookings():
    if request.method == 'GET':
        return bSys.query(request.args)
    elif request.method == 'POST':
        if 'name' in session:
            form = request.form.copy()
            form['name'] = session['name']
            form['email'] = session['email']
            return bSys.book(form)
        else:
            return ('You are not logged in', 401)
    else:
        if 'email' in session:
            form = request.form.copy()
            form['email'] = session['email']
            return bSys.cancel(form)
        else:
            return ('You are not logged in', 401)

@app.route('/bookings/free', methods=['GET'])
def freeroom():
    return bSys.freeroom(request.args)

app.run(host="0.0.0.0", port=5000, debug=True)