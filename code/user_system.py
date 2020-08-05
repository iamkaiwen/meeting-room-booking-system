import hashlib
import mysql.connector
from mysql.connector import errorcode

create_table_sql = (
    "CREATE TABLE IF NOT EXISTS accounts ("
    "   name varchar(20) NOT NULL,"
    "   email varchar(50) NOT NULL PRIMARY KEY,"
    "   password varchar(128) NOT NULL,"
    "   role ENUM('user', 'admin') DEFAULT 'user' NOT NULL"
    ");"
)
create_account_sql = (
    "INSERT INTO accounts (email, password, name, role)"
    "VALUES (%(email)s, %(password)s, %(name)s, %(role)s);"
)

login_account_sql = (
    "SELECT name FROM accounts "
    "WHERE email = %(email)s AND password = %(password)s;"
)

class UserSystem:
    def __init__(self, cnx):
        self._create_requirements = ['name', 'email', 'password', 'role']
        self._login_requirements = ['email', 'password']

        self._cnx = cnx

        # Initialize table accounts
        try:
            cursor = self._cnx.cursor()
            cursor.execute(create_table_sql)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("[Success] Table accounts already exists")
            else:
                print(err.msg)
        else:
            print("[Success] Created Table accounts")
        finally:
            cursor.close()
    
    def _check(self, form, requirements):
        for parameter in requirements:
            if parameter not in form:
                return False
        return True
        
    def create(self, form):
        if not self._check(form, self._create_requirements):
            return ("Missing parameters", 400)

        # Hash password
        hashobj = hashlib.sha3_512()
        hashobj.update(form['password'].encode())
        form['password'] = hashobj.hexdigest()

        # Create a user account
        try:
            cursor = self._cnx.cursor()
            cursor.execute(create_account_sql, form)
            self._cnx.commit()
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_ENTRY:
                return ("Duplicate email", 400)
            elif err.errno == errorcode.WARN_DATA_TRUNCATED:
                return("role should be user/admin", 400)
            else:
                print(err.msg)
                return ("Server error", 500)
        else:
            return "Created a user account"
        finally:
            cursor.close()

    def login(self, form):
        if not self._check(form, self._login_requirements):
            return ("Missing parameters", 400)

        # Hash password
        hashobj = hashlib.sha3_512()
        hashobj.update(form['password'].encode())
        form['password'] = hashobj.hexdigest()

        # Login to a user account
        try:
            cursor = self._cnx.cursor()
            cursor.execute(login_account_sql, form)
            result = cursor.fetchone()
        except mysql.connector.Error as err:
                print(err.msg)
                return ("Server Error", 500)
        else:
            if result:
                name = result[0]
                return ("Login success", name)
            else:
                return ("Wrong email/password", 400)
        finally:
            cursor.close()
