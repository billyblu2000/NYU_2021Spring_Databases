# DATABASES FINAL PROJECT MANUAL



> Authored by Billy Yi[^1] and Ziyang Liao[^2].
>
> Copyright 2021. All rights reserved.
>
> You can access this manual at [/manual/](/manual/) after you launch the project.



## CATALOGUE

- [DATABASES FINAL PROJECT MANUAL](#databases-final-project-manual)
  * [CATALOGUE](#catalogue)
  * [PROJECT STRUCTURE](#project-structure)
  * [FUNCTION INTRODUCTION AND USAGE](#function-introduction-and-usage)
    + [General Discreption](#general-discreption)
    + [Functions for Different Roles](#functions-for-different-roles)
        * [Public (Guest)](#public--guest-)
        * [Login and Register](#login-and-register)
          + [Register](#register)
          + [Login](#login)
        * [Users](#users)
          + [Customer](#customer)
          + [Booking Agent](#booking-agent)
          + [Airline Staff](#airline-staff)
  * [MAIN IDEA OF IMPLEMENTATION](#main-idea-of-implementation)
    + [MySQL Tool and Validation Decorator](#mysql-tool-and-validation-decorator)
        * [Sessions and User Role](#sessions-and-user-role)
        * [MySQLTool](#mysqltool)
        * [User Role Validation](#user-role-validation)
    + [Prepared Statement for Preventing SQL Injection](#prepared-statement-for-preventing-sql-injection)
  * [ACKNOWLEDGE](#acknowledge)

## PROJECT STRUCTURE

```python
.
├── README.md                      # A project discreption
├── app.py                         # A project discreption
├── config.py                      # A project discreption
├── make_data.py                   # A project discreption
├── mysql_tool.py                  # A project discreption
├── static
│   ├── css
│   │   └── bootstrap.css          # A project discreption
│   ├── favicon.ico                # A project discreption
│   ├── img
│   │   └── banner-bg.jpg          # A project discreption
│   └── js
│       └── bootstrap.min.js       # A project discreption
├── templates
│   ├── admin.html                 # A project discreption
│   ├── admin_s.html
│   ├── home.html
│   ├── login.html
│   ├── register-agent.html
│   ├── register-customer.html
│   └── register-staff.html
└── utils.py
```



## FUNCTION INTRODUCTION AND USAGE

### General Discreption

This web application is a demo of a flight ticket reservation system, implemented by Python/Flask and  MySQL at the back-end, and Bootstrap CSS framework at the front-end. The application provides different functions for three kinds of users: customer, booking agent and airline staff. Generally, customers and booking agents can reserve or book flight tickets via the system, and airline staff can insert and update informations of flights and airplanes. Detailed functions will be provided in the later paragraphs. 

You can <u>start the application by running `app.py`  using a Python interpreter</u>. By default, the application will be running on localhost, port 80. After the app starts, hosts that are in the same LAN should be able to access the application by entering your local IP (LAN IP) in their browser. <u>If you want to access only from localhost, you can change `DEBUG = False` to `DEBUG = True` in the file `config.py`</u>.

<u>After the application starts, you can type “[localhost/](/)” or LAN IP in the address</u>, the application will automatically redirect to “[localhost/home/](/home/)” to view the home page. (**<u>Please notice that if you switch to `DEBUG = True`, you should type “[localhost:5000/](/)” in your address because the application is now running on port 5000</u>**). In our project, MySQL server is running on an Internet remote server (Tencent Cloud), so in order to better manage the database, we have also provided a webpage ([/admin/](/admin/)) for developers to run SQL and fetch results if any. 

### Functions for Different Roles

##### Public (Guest)



##### Login and Register

Users can login or register as different roles at the home page.

###### Register

Each of the three user roles has its own register page. Users will enter their informations according to the prompts in placeholders. After the user submit the register form, the server will first check whether the data match the domain in the database, if not, it will return an error message to the user interface. The following is an example of checking data integrity of airline staffs.

```python
# check name length
elif len(first_name) >= 50 or len(last_name) >= 50:
		return render_template('register-staff.html', airlines=airlines, error='Your name is too long!')

# check airline name is valid
elif airline_name == 'airline' or airline_name == None:
		return render_template('register-staff.html', airlines=airlines, error='Please select airline!')

else:
		try:
      	# check date is valid
				lst = dob.split("-")
				d = datetime.date(day=int(lst[2]), month=int(lst[1]), year=int(lst[0]))
		except:
				return render_template('register-staff.html', airlines=airlines, error='Please enter a valid birthday!')
```

Notice that an airline staff must choose an airline when they are doing registration. So before the register page is served to ''pre-airline staffs'', the server will have to ask the database for all existing airlines. 

```SQL
SELECT `airline_name` FROM `airline`
```

Airline staff will also be required to enter a permission code when registration. This is trying to protect the system from hostile users. For this demo, the permission code which the user entered must match an existing permission code stroed in the DB. An SQL example of user enters ''STAFF'':

```sql
SELECT * FROM `airline_staff_permission_code` WHERE `code` = 'STAFF'
```

In the method `mt.root_check_duplicates`, the server checked whether user is duplicate. An example SQL can be:

```sql
SELECT * FROM `airline_staff` WHERE `username` = 'billyblu'
```

After the server have ensure that no invalid data, it will first calculate the MD5 of the password, then run the SQL insertion. Example:

```sql
INSERT INTO airline_staff VALUE ('billyblu', '688dd96ed8c69b66d1f3e6a494050d28', 'Li', 'Yi', '2000-12-08', 'Air China')
```

###### Login

The login page is designed as one single page but can be used for all three kinds of users to login. User will enter their username (for customer and booking agent, it's their email) and password, then choose an identity. The server will run a SQL statement to check whether there exists a tuple in table *customer* / *booking_agent* / *airline_staff* which *email* / *username* and *password* is the same as which the user enters. An example SQL can be 

```sql
SELECT * FROM `customer` WHERE `email` = 'ly1387@nyu.edu' and `password` = '688dd96ed8c69b66d1f3e6a494050d28'
```

The SQL queries for booking agents and airline staffs are the same logic, so they are omitted.

##### Users

The next three sections will be the detailed usage of the functions and authorities of three roles: customer, booking agent and airline staff.

###### Customer

###### Booking Agent

###### Airline Staff



## MAIN IDEA OF IMPLEMENTATION

### MySQL Tool and Validation Decorator

##### Sessions and User Role

After the user logged in (completion of the register process will also followed by automatically logged in), a session will be created. <u>A string like `username:role` (i.e. "ly1387@nyu.edu:C") will be assign to a key call `'user'` in the session.</u> There are three roles in total, namely, "A": airline staff, "B": booking agent, "C": customer.

##### MySQLTool

Creating and processing SQL statement can be lengthy, and many operations are autually the same in different situations. In order to <u>imporve code reuse rate, and better manage database connection and user permissions</u>, we created an MySQL Utility class to manage all SQL related work. The whole class shares a same DB connection, and it will autometically refresh when it's dead. The following code gives a brief structure of the util class.

```python
class MySQLTool:
    """A class deals all the things related to MYSQL"""

    def __init__(self):
      	self._conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
        )
        refresh_thread = threading.Thread(target=self.__refresh_connection)
        refresh_thread.start()

    def get_connection(self):
      	pass

    # guest can only do query on flight table
    def guest_query(self, table, attribute=None, value=None):
      	pass

    @validate_user(role='A')
    def staff_insert(self, user, table, value=None, create_ticket=True, ticket_number=None,
                     airline_name=None, flight_num=None):
      	pass
		
    ...

    # customer can only do query on flight table and purchase table
    @validate_user(role='C')
    def customer_query(self, user, table, attribute, value):
      	pass
    ...
    @validate_user(role='root')
    def root_get_uid(self, user, role, pk):
      	pass
    ...
```

##### User Role Validation

To <u>provide different permissions to different users</u>, we created a decorator `@validate_user()`. Functions or methods decorated will not execute unless the argument `user` is validated. `user` is the string that stored in sessions. When users request to call a method, `user` in their sessions will be passed in. When decorating a method, you also have to pass in the role that you want to validate. For example, if a method is decorated by `@validate_user(role='BC')`, then it will not execute unless the user is registered as a customer or a booking agent. By default, `@validate_user()` is equal to `@validate_user(role='ABC')`. `@validate_user(role='root')` means that the method will execute if and only if `user = 'root'`. The validation is done by scaning through the corresponding user table and check whether the user is inside that table. <u>By using decorators, different users can get permissions to call different functions, and therefore do different operations to the database</u>.

### Prepared Statement for Preventing SQL Injection 

To prevent SQL injection, <u>all the SQL statements that involve user-entered parameters in the project are executed in a prepared form</u>. Python module `mysql.connector` provide an easy way to make SQL statement prepared, by passing in `prepared = True` when initialize a cursor. The following gives an example of executing prepared SQL statement.

```python
    ...
  	@validate_user(role='root')
    def root_sql_query(self, user, stmt, value):
        cursor = self._conn.cursor(prepared=True)
        cursor.execute(stmt,value)
        return cursor.fetchall()
    ...
```



## ACKNOWLEDGE

Special thanks to our professor Lihua Xu, who provided us with academic supports, and our instructor Qingshun Wang, who have helped us to set up our project.

[^1]: Billy Yi, CS majored sophomore @ NYU Shanghai, contribute mainly to the server construction, Python/Flask, MySQL connection and execution. Contact him at ly1387@nyu.edu
[^2]: Ziyang Liao, CS majored sophomore @ NYU Shanghai, contribute mainly to front-end construction, including HTML, CSS, Javascript and data visualization. Contact him at zl3057@nyu.edu


