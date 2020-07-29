from datetime import date
from flask import jsonify
import mysql.connector
from mysql.connector import errorcode

create_table_sql = (
    "CREATE TABLE IF NOT EXISTS bookings ("
    "   title varchar(50) NOT NULL,"
    "   description varchar(50) NOT NULL,"
    "   id tinyint NOT NULL,"
    "   date date NOT NULL,"
    "   start tinyint NOT NULL,"
    "   end tinyint NOT NULL,"    
    "   status ENUM('public', 'private') DEFAULT 'public' NOT NULL,"
    "   host varchar(20) NOT NULL,"
    "   email varchar(50) NOT NULL,"
    "   FOREIGN KEY (email) REFERENCES accounts(email)"
    ");"
)

create_booking_sql = (
    "INSERT INTO bookings (title, description, id, date, start, end, status, host, email)"
    "VALUES (%(title)s, %(description)s, %(id)s, %(date)s, %(start)s, %(end)s, %(status)s, %(name)s, %(email)s);"
)

cancel_sql = (
    "DELETE FROM bookings "
    "WHERE email = %(email)s AND id = %(id)s AND date = %(date)s AND start = %(start)s AND end = %(end)s;"
)

cancel_check_sql = (
    "SELECT email FROM bookings "
    "WHERE id = %(id)s AND date = %(date)s AND start = %(start)s AND end = %(end)s;"
)

query_booked_sql = (
    "SELECT COUNT(*) FROM bookings "
    "WHERE id = %(id)s AND date = %(date)s AND start < %(end)s AND end > %(start)s;"
)

query_room_sql = (
    "SELECT id FROM bookings "
    "WHERE date = %(date)s AND start < %(end)s AND end > %(start)s;"
)

class BookingSystem:
    def __init__(self, cnx):
        self._create_requirements = ['title', 'description', 'id', 'date', 'start', 'end', 'status', 'name', 'email']
        self._cancel_requirements = ['id', 'date', 'start', 'end', 'email']
        self._query_requirements = ['id', 'date', 'start', 'end']
        self._free_room_requirements = ['date', 'start', 'end']

        self._cnx = cnx

        # Initialize table accounts
        try:
            cursor = self._cnx.cursor()
            cursor.execute(create_table_sql)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("[Success] Table bookings already exists")
            else:
                print(err.msg)
        else:
            print("[Success] Created Table bookings")
        finally:
            cursor.close()

    def _check(self, form, requirements):
        for parameter in requirements:
            if parameter not in form:
                return False
        return True

    def query(self, form):
        if not self._check(form, self._query_requirements):
            return ("Missing parameters", 400)
        
        week = date.fromisoformat(form['date']).weekday()
        if week > 4:
            return ("Invalid date: Should be Mon-Fri", 400)
        elif int(form['start']) < 9 or int(form['end']) > 18 or int(form['end']) - int(form['start']) < 1:
            return ("Invalid time: Should be 9-18 & end - start >= 1", 400)
        elif int(form['id']) < 1 or int(form['id']) > 6:
            return ("Invalid Room ID: Should be 1-6", 400)

        # Check time overlapped
        try:
            cursor = self._cnx.cursor()
            cursor.execute(query_booked_sql, form)
            result = cursor.fetchone()[0]
        except mysql.connector.Error as err:
                print(err.msg)
                return ("Server Error", 500)
        else:
            if result:
                return ("Already booked", 200)
            else:
                return ("Not booked", 200)
        finally:
            cursor.close()


    def _ok_to_book(self, form):
        if not self._check(form, self._create_requirements):
            return ("Missing parameters", 400)

        return self.query(form)
    
    def book(self, form):
        # check if it's ok to book
        resp = self._ok_to_book(form)
        if resp[1] != 200:
            return resp
        elif resp[0] == "Already booked":
            resp = ("Already booked", 400)
            return resp

        # create a booking
        try:
            cursor = self._cnx.cursor()
            cursor.execute(create_booking_sql, form)
            self._cnx.commit()
        except mysql.connector.Error as err:
            if err.errno == errorcode.WARN_DATA_TRUNCATED:
                return("status should be public/private", 400)
            else:
                print(err.msg)
                return ("Server error", 500)
        else:
            return ("Created a booking", 200)
        finally:
            cursor.close()
    
    def _ok_to_cancel(self, form):
        if not self._check(form, self._cancel_requirements):
            return ("Missing parameters", 400)
        
        try:
            cursor = self._cnx.cursor()
            cursor.execute(cancel_check_sql, form)
            result = cursor.fetchone()
        except mysql.connector.Error as err:
            print(err.msg)
            return ("Server error", 500)
        else:
            if result:
                if result[0] != form['email']:
                    return ("Invalid host", 401)
                else:
                    return ("Okay to cancel", 200)
            else:
                return ("Invalid meeting time", 400)
        finally:
            cursor.close()

    def cancel(self, form):
        # check if it's ok to cancel a booking
        resp = self._ok_to_cancel(form)
        if resp[1] != 200:
            return resp
        
        # cancel a booking
        try:
            cursor = self._cnx.cursor()
            cursor.execute(cancel_sql, form)
            self._cnx.commit()
        except mysql.connector.Error as err:
            print(err.msg)
            return ("Server error", 500)
        else:
            return ("Canceled a booking", 200)
        finally:
            cursor.close()

    def freeroom(self, form):
        if not self._check(form, self._free_room_requirements):
            return ("Missing parameters", 400)
        
        week = date.fromisoformat(form['date']).weekday()
        if week > 4:
            return ("Invalid date: Should be Mon-Fri", 400)
        elif int(form['start']) < 9 or int(form['end']) > 18 or int(form['end']) - int(form['start']) < 1:
            return ("Invalid time: Should be 9-18 & end - start >= 1", 400)
        
        # Check time overlapped
        freeRoom = set([tmp for tmp in range(1, 7)])
        try:
            cursor = self._cnx.cursor()
            cursor.execute(query_room_sql, form)
            for roomid in cursor:
                freeRoom.discard(roomid[0])
        except mysql.connector.Error as err:
            print(err.msg)
            return ("Server Error", 500)
        else:
            return jsonify({"freeRoomIds": list(freeRoom)})
        finally:
            cursor.close()
