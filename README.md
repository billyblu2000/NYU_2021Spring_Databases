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
    + [Flight Recommendation for Customers and Booking Agents](#flight-recommendation-for-customers-and-booking-agents)
  * [ACKNOWLEDGE](#acknowledge)


## PROJECT STRUCTURE

```python
.
├── static
│   ├── css
│   │   └── bootstrap.css                   # bootstrap framework css file
│   ├── favicon.ico													# project logo
│   ├── img
│   │   └── banner-bg.jpg                   # picture on main page
│   └── js
│       └── bootstrap.min.js                # bootstrap framework js file
├── templates
│   ├── Databases_Final_Project_Manual.html # this file
│   ├── admin.html                          # admin HTML page for admin to excute SQL
│   ├── admin_s.html                        # admin HTML page for admin to excute SQL
│   ├── home.html                           # home (main) HTML page 
│   ├── login.html                          # login HTML page
│   ├── profile.html                        # profile HTML page
│   ├── insert_airplane.html                # HTML page for staffs to insert airplanes
│   ├── insert_airport.html                 # HTML page for staffs to insert airports
│   ├── insert_flight.html                  # HTML page for staffs to insert flights
│   ├── agent_purchase.html                 # HTML page for agents to purchase for customers
│   ├── purchase_failed.html                # HTML page when purchase failed
│   ├── purchase_success.html               # HTML page when purchase success
│   ├── register-agent.html                 # register HTML page for booking agent
│   ├── register-customer.html              # register HTML page for customer
│   └── register-staff.html                 # register HTML page for airline staff
├── app.py                                  # Main Flask back-end
├── config.py																# all config settings
├── make_data.py                            # produce fake data for testing
├── mysql_tool.py                           # MySQLTool class that deals everything involving SQL execution
└── utils.py                                # supporting functions
```



## FUNCTION INTRODUCTION AND USAGE

### General Discreption

This web application is a demo of a flight ticket reservation system, implemented by Python/Flask and  MySQL at the back-end, and Bootstrap CSS framework at the front-end. The application provides different functions for three kinds of users: customer, booking agent and airline staff. Generally, customers and booking agents can reserve or book flight tickets via the system, and airline staff can insert and update informations of flights and airplanes. Detailed functions will be provided in the later paragraphs. 

You can <u>start the application by running `app.py`  using a Python interpreter</u>. By default, the application will be running on localhost, port 80. After the app starts, hosts that are in the same LAN should be able to access the application by entering your local IP (LAN IP) in their browser. <u>If you want to access only from localhost, you can change `DEBUG = False` to `DEBUG = True` in the file `config.py`</u>.

<u>After the application starts, you can type “[localhost/](/)” or LAN IP in the address</u>, the application will automatically redirect to “[localhost/home/](/home/)” to view the home page. (**<u>Please notice that if you switch to `DEBUG = True`, you should type “[localhost:5000/](/)” in your address because the application is now running on port 5000</u>**). In our project, MySQL server is running on an Internet remote server (Tencent Cloud), so in order to better manage the database, we have also provided a webpage ([/admin/](/admin/)) for developers to run SQL and fetch results if any. 

### Functions for Different Roles

##### Public (Guest)

After a user access the website, two main block will be displayed, one block is where you can login or register, and the other is the  searching function. User can do search by choosing a departure / arrival city, choosing a departure / arrival date, choosing an airline or enter a flight number. 

![截屏2021-05-10 上午2.22.21](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-10 上午2.22.21.png)

All cities and all airlines will be returned together with this page, in order to achieve this, the server will do a pre-search in the database. 

```sql
SELECT airline_name, s.airport_city, t.airport_city 
FROM (flight INNER JOIN airport s ON flight.departure_airport = s.airport_name) 
INNER JOIN airport t ON flight.arrival_airport = t.airport_name;
```

After the user complete the search information and click on the 'Order Ticket Now' button, the server will run the following SQL query, for example.

```sql
SELECT `airline_name`, `flight_num`, `departure_airport`, `departure_time`, `arrival_airport`, `arrival_time`, `price`, `status`, `airplane_id` 
FROM (flight INNER JOIN airport s ON flight.departure_airport = s.airport_name) 
INNER JOIN airport t ON flight.arrival_airport = t.airport_name
WHERE s.airport_city = 'Shanghai' AND t.airport_city = 'Beijing' AND departure_time BETWEEN '2021-06-01 00:00:00' AND '2021-06-01 23:59:59';
```

The following is the result of the example SQL query. But please notice that guests are not allowed to purchase tickets. If he/she click on 'Purchase', the page will be redirected to the login page.

![截屏2021-05-10 下午1.28.46](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-10 下午1.28.46.png)

Our project creates an additional function for different roles on the home page. For guests, he/she will see a 'popular flight recommendation' before searching anything. These flights recommended are based on the number of ticket sold. A flight will be more likly to be recommended if a lot of tickets were sold. Of course, if a flight have no ticket left, it will not be recommended.

##### ![截屏2021-05-10 下午1.37.04](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-10 下午1.37.04.png)

##### Login and Register

Users can login or register as different roles at the home page.

###### Register

Each of the three user roles has its own register page. Users will enter their informations according to the prompts in placeholders. After the user submit the register form, the server will first check whether the data match the domain in the database, if not, it will return an error message to the user interface. The following is an example of checking data integrity of airline staffs.

Notice that an airline staff must choose an airline when they are doing registration. So before the register page is served to ''pre-airline staffs'', the server will have to ask the database for all existing airlines. 

```SQL
SELECT `airline_name` FROM `airline`;
```

Airline staff will also be required to enter a permission code when registration. This is trying to protect the system from hostile users. For this demo, the permission code which the user entered must match an existing permission code stroed in the DB. An SQL example of user enters ''STAFF'':

```sql
SELECT * FROM `airline_staff_permission_code` WHERE `code` = 'STAFF';
```

In the method `mt.root_check_duplicates`, the server checked whether user is duplicate. An example SQL can be:

```sql
SELECT * FROM `airline_staff` WHERE `username` = 'billyblu';
```

After the server have ensure that no invalid data, it will first calculate the MD5 of the password, then run the SQL insertion. Example:

```sql
INSERT INTO airline_staff VALUE ('billyblu', '688dd96ed8c69b66d1f3e6a494050d28', 'Li', 'Yi', '2000-12-08', 'Air China');
```

###### Login

The login page is designed as one single page but can be used for all three kinds of users to login. User will enter their username (for customer and booking agent, it's their email) and password, then choose an identity. The server will run a SQL statement to check whether there exists a tuple in table *customer* / *booking_agent* / *airline_staff* which *email* / *username* and *password* is the same as which the user enters. An example SQL can be 

```sql
SELECT * FROM `customer` WHERE `email` = 'ly1387@nyu.edu' and `password` = '688dd96ed8c69b66d1f3e6a494050d28';
```

The SQL queries for booking agents and airline staffs are the same logic, so they are omitted.

##### Users

The next three sections will be the detailed usage of the functions and authorities of three roles: customer, booking agent and airline staff.

###### Customer

The following are functions of customer. SQL statement presented are only for example. In the graph example and SQL example, we will take this customer account: `('ly1387@nyu.edu', 'billyblu', '688dd96ed8c69b66d1f3e6a494050d28', ... )`.

Customer role shares the searching fucntion discribed in the Guest section, so it will not be reintroduced here. The following is some special functions for customers.

1. Recommend flights

   After a customer logged in, he/she will be seeing a recommended flights section on the home page, while the 'popular flights recommendation' section hiddened. ![截屏2021-05-10 下午3.16.33](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-10 下午3.16.33.png)

   These flights recommended are bases on the customer previous purchase experience. <u>The recommendation algorithm will consider the customer's past flight's airline preference, departure airport and departure city preference, arrival airport and arrival city preference, departure time preference and price preference, and calculate a "prefer coefficient" for each upcoming flight, and finally pick out 10 flights with the highest "prefer coefficient" and recommended them to the customer.</u>

   The total algorithm is too complecated so it is not shown here.

2. Purchase flight

   Customers can purchase flight by clicking the purchase button in the flight table. After the button is clicked, a webpage will jump out to show the purchase result. A simple SQL is executed during this process:

   ```sql
   INSERT INTO purchases VALUE (1000000, 'ly1387@nyu.edu', NULL, '2021-5-12');
   ```

3. View my flights

   Customers can view the flights that they already purchased by entering the profile page. The profile page can be entered through a link on the home page after the customer have logged in.![截屏2021-05-12 下午3.57.45](/Users/billyyi/Desktop/截屏2021-05-12 下午3.57.45.png)

   ![截屏2021-05-12 下午3.55.48](/Users/billyyi/Desktop/截屏2021-05-12 下午3.55.48.png)

   The server retrieved the flights information by executing the following SQL:

   ```sql
   SELECT airline_name, flight_num, departure_airport, departure_date, arrival_airport, arrival_date, price, status, airplane_id  FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE customer_email = 'ly1387@nyu.edu';
   ```

4. View total spending and month wise spending

   Customer can also view their spending on the profile page. He / She can specify a start month and end month to view the total spending and the month wise spending. If no parameters, the default is showing the total spent of last year and the month wise spent of last six months.![截屏2021-05-12 下午4.03.37](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午4.03.37.png)

   This function is realized by executing the following SQL, for example:

   ```sql
   SELECT SUM(price) FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE purchase_date BETWEEN '2020-12-01' AND '2021-5-12' AND customer_email = 'ly1387@nyu.edu';
   ```

   

###### Booking Agent

The following are functions of booking agent. SQL statement presented are only for example. In the graph example and SQL example, we will take this booking agent account: `('ly1387@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 1)`.

1. Recommended flights

   The recommendation process of booking agent is similar to customer. So it will not be shown here.

2. Purchase flight for customer

   Booking agent can purchase ticket for customers, by clicking the purchase button. Upon click, the website will jump to a page to ask the booking agent to input the customer email. ![截屏2021-05-12 下午6.46.47](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午6.46.47.png)

   The SQL statement for booking agent is similar to customer's SQL statement.

   ```sql
   INSERT INTO purchases VALUE (1000000, 'ly1387@nyu.edu', 'billy@nyu.edu', '2021-5-12');
   ```

3. View my flights

   Booking agent can view the flights that they already purchased by entering the profile page. The profile page can be entered through a link on the home page after the booking agent have logged in. (Same with customer.)

   ![截屏2021-05-12 下午6.52.19](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午6.52.19.png)

   SQL statement is as follows:

   ```sql
   SELECT airline_name, flight_num, departure_airport, departure_date, arrival_airport, arrival_date, price, status, airplane_id  FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE booking_agent_id = 1;
   ```

4. View Commission

   Booking agent have the permission to view his / her commission by entering a time range. If no time range is specified, the default will be past 30 days.

   ![截屏2021-05-12 下午6.54.53](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午6.54.53.png)

   The function is realized by executing the following SQL statement:

   ```sql
   SELECT price FROM flight NATURAL JOIN ticket NATURAL JOIN purchases NATURAL JOIN booking_agent WHERE booking_agent_id = 1 AND purchase_date BETWEEN '2021-04-12' AND '2021-05-12';
   ```

5. View Top Customers

   Top customers

   ![截屏2021-05-12 下午8.24.03](/Users/billyyi/Desktop/截屏2021-05-12 下午8.24.03.png)

   ![截屏2021-05-12 下午8.24.13](/Users/billyyi/Desktop/截屏2021-05-12 下午8.24.13.png)

   The SQL statement is similar with the one in function 4, we just add more post-processing using python, so the SQL statement will not be shown here.

###### Airline Staff

The following are functions of airline staff. SQL statement presented are only for example. In the graph example and SQL example, we will take this airline staff account: `('billyblu', '688dd96ed8c69b66d1f3e6a494050d28', 'Li', 'Yi', '2000-12-08', 'Air China')`

1. View my flights

   Airline staff can see all the flights of his airline company on the home page. 

   ![截屏2021-05-12 下午9.43.01](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.43.01.png)

   The function will execute the following SQL statement, for example:

   ```sql
   SELECT airline_name, flight_num, departure_airport, departure_date, arrival_airport, arrival_date, price, status, airplane_id FROM flight NATURAL JOIN airline_staff WHERE username = 'billy';
   ```

2. Add new flight

   Airline staff can enter his / her profile and enter the insert page of new flights / airports / airplanes on the home page.

   ![截屏2021-05-13 下午3.49.46](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-13 下午3.49.46.png)

   Airline staff can add new flight for his / her company. The user will be asked to input the flight number, departure / arrival airport, departure / arrival time, price, status, and airplane ID. 

   ![截屏2021-05-12 下午9.43.32](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.43.32.png)

   Notice that the server will search first on the database, for all existing airports and all existing airplanes that belongs to the staff's airline, before the insert page is returned to the user. This is done by the following SQL:

   ```sql
   SELECT airplane_id FROM airplane NATURAL JOIN airline NATURAL JOIN airline_staff WHERE username = 'billy';
   SELECT airport_name FROM airport;
   ```

   After the user click insert, the server will first insert a ticket into the database:

   ```sql
   INSERT INTO flight VALUE ('Air China', 10000, 'PVG', '2021-06-01 00:00:00', 'PEK', '2021-06-01 12:00:00', 2000, 'upcoming', 11111);
   ```

   If the user check 'Automatic create ticket' on the insert page, the server will also insert tickets of this flight into the database. The amount of ticket is same with the seats of the airplane.

   ```sql
   INSERT INTO ticket VALUES 
   (1000001, 'Air China', 10000),
   (1000002, 'Air China', 10000),
   (1000003, 'Air China', 10000),
   ...;
   ```

3. Add new airport

   Airline staff can also add airports to the system. He / She will be ask to input the airport name and the airport city on the insert page.

   ![截屏2021-05-12 下午9.44.27](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.44.27.png)

   The following SQL will be executed:

   ```sql
   INSERT INTO airport VALUE ('PEK', 'Beijing');
   ```

4. Add new airplane

   Similarly, airline staffs can insert airplanes to the system.

   ![截屏2021-05-12 下午9.44.00](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.44.00.png)

   The following SQL will be executed:

   ```sql
   INSERT INTO airplane VALUE ('Air China', 100000, 250);
   ```

   Airline staff can also see all airplanes that belongs to his / her airline.

   ```sql
   SELECT airplane_id, seats FROM airplane NATURAL JOIN airline NATURAL join airline_staff WHERE username = 'billyblu';
   ```

5. Change status of a flight 

   Airline staff can change status of a flight easily, by clicking on the edit button on the right side of each flight. After the button is clicked, the status cell will change into an editable mode, airline staffs can then select a status. Finally, users can click on the save button to save the changes.

   ![截屏2021-05-12 下午9.44.50](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.44.50.png)

   This process is done by executing the following SQL:

   ```sql
   UPDATE flight SET status = 'delayed' WHERE airline_name = 'Air China' AND flight_num = 10000;
   ```

6. View top booking agents

   When a airline staff enters the profile page, he / she will be able to view the top five booking agent base on their ticket sold last month, ticket sold last year, commission last year, respectively. 

   ![截屏2021-05-12 下午9.45.20](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.45.20.png)

   This is achieved by executing the following sql:

   ```sql
   SELECT booking_agent.email, price FROM flight NATURAL JOIN ticket NATURAL JOIN purchases NATURAL JOIN booking_agent WHERE purchase_date BETWEEN '2020-05-12' AND '2021-05-12';
   ```

7. View frequent customer and customer flights

   AIrline staff can also view the most frequent customer in the whole sysytem and see all flights of his / her airline, that a specific customer purchaseed by submitting a customer email. By default, it will show all flights of the frequent customer.

   ![截屏2021-05-12 下午9.45.55](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.45.55.png)

   ![截屏2021-05-12 下午9.46.06](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.46.06.png)

   This is achieved by executing the following SQLs:

   ```sql
   WITH customer_count AS (SELECT customer_email, COUNT(customer_email) AS cc 
                           FROM flight NATURAL JOIN ticket NATURAL JOIN purchases 
                           WHERE purchase_date >= %s GROUP BY customer_email) 
   SELECT customer_email FROM customer_count WHERE customer_count.cc = (SELECT MAX(cc) FROM customer_count);
   SELECT airline_name, flight_num, departure_airport, departure_date, arrival_airport, arrival_date, price, status, airplane_id FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE customer_email = 'ly1387@nyu.edu';
   ```

8. View and compare revenue

   Airline staff can view a month wise ticket sold report. By default is the past six month, but he / she will also have tht option to specify a date range.

   ![截屏2021-05-12 下午9.46.55](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.46.55.png)

   This is done by the following SQL statement:

   ```sql
   SELECT * FROM flight NATURAL JOIN ticket NATURAL JOIN purchases NATURAL JOIN airline_staff WHERE purchase_date BETWEEN '2020-11-12' AND '2021-05-12' AND username = 'billyblu'
   ```

9. View top destinations

   Similar to view top booking agents, airline staffs can also view top destinations.

   ![截屏2021-05-12 下午9.45.34](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.45.34.png)

   The SQL statement is in the following pattern:

   ```sql
   SELECT airport_city, COUNT(airport_city) AS cac 
   FROM flight NATURAL JOIN ticket NATURAL JOIN purchases INNER JOIN airport ON (arrival_airport = airport.airport_name) 
   WHERE purchase_date > '2020-05-12' GROUP BY airport_city ORDER BY cac DESC LIMIT 3
   ```

10. View revenue

    Airline staffs can view a comparision graph of revenue for last month and last year, respectively. The graph will show the amount comparison between direct purchase (by customer) and indirect purchase (by booking agent).

    ![截屏2021-05-12 下午9.48.00](/Users/billyyi/Library/Application Support/typora-user-images/截屏2021-05-12 下午9.48.00.png)

    The SQL statement is in the following pattern:

    ```sql
    WITH count_null_month AS (SELECT SUM(price) AS cnm FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE booking_agent_id IS NULL AND purchase_date > '2021-04-12' AND airline_name = 'Air China'), 
    count_null_year AS (SELECT SUM(price) AS cny FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE booking_agent_id IS NULL AND purchase_date > '2020-05-12' AND airline_name = 'Air China'), 
    count_not_null_month AS (SELECT SUM(price) AS cnnm FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE booking_agent_id IS NOT NULL AND purchase_date > '2021-04-12' AND airline_name = 'Air China'), 
    count_not_null_year AS (SELECT SUM(price) AS cnny FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE booking_agent_id IS NOT NULL AND purchase_date > '2020-05-12' AND airline_name = 'Air China') 
    SELECT cnm, cny, cnnm, cnny FROM count_null_month, count_null_year, count_not_null_month, count_not_null_year
    ```

    

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

### Flight Recommendation for Customers and Booking Agents

To make our application more user-friendly, we also create a recommendation algorithm for customers and booking agents. This algorithm will analyze the purchase history of customers and booking agents, and select ten upcoming flights in the system and recommend them to the customer and booking agent.

In the algorithm, we consider four features: airline, (departure airport, arrival airport), departure time, and price. We create four distcance function, with $d_i$ representing the i-th distcance function. The distance function $d_i(x)$ refers to the distance between the value of feature x  and  the user expected $E[x]$, which was calculated from the purchase history. Then we apply a linear function to calculate the distance for each upcoming flight. 
$$
D(flight) = \omega_{airline}d_1(airline) + \omega_{airport}d_2(dparture \ airport, arrival \ airport) + \omega_{time}d_3(time) + \omega_{price}d_4(price)
$$
Filght with smaller distance will have the higher probability to be recommended.

## ACKNOWLEDGE

Special thanks to our professor Lihua Xu, who provided us with academic supports, and our instructor Qingshun Wang, who have helped us to set up our project.

[^1]: Billy Yi, CS majored sophomore @ NYU Shanghai, contribute mainly to the server construction, Python/Flask, MySQL connection and execution. Contact him at ly1387@nyu.edu
[^2]: Ziyang Liao, CS majored sophomore @ NYU Shanghai, contribute mainly to front-end construction, including HTML, CSS, Javascript and data visualization. Contact him at zl3057@nyu.edu


