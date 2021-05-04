import datetime
import json

from flask import Flask, session, request, render_template, redirect, Response

import utils
from mysql_tool import MySQLTool
from config import *
from hashlib import md5
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = PERMANENT_SESSION_LIFETIME

mt = MySQLTool()


####################
# login and register
####################

@app.route('/register/')
def register():
    return back_home()


@app.route('/register/customer/', methods=['POST', 'GET'])
def register_customer():
    if request.method == 'GET':
        return render_template('register-customer.html')
    else:
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        building_number = request.form.get('building_number')
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        phone_number = request.form.get('phone_number')
        passport_number = request.form.get('passport_number')
        passport_expiration = request.form.get('passport_expiration')
        passport_country = request.form.get('passport_country')
        dob = request.form.get('date_of_birth')

        if mt.root_check_duplicates(table='customer', attribute='email', value=email, user='root'):
            # duplicate
            # TODO
            return render_template('register-customer.html', error='User already exists!')

        elif len(email) >= 50 or len(email.split("@")) < 2:
            return render_template('register-customer.html', error='Please enter a valid email!')

        elif len(name) >= 50:
            return render_template('register-customer.html', error='Your name is too long!')

        elif len(city) >= 30 or len(state) >= 30 or len(building_number) >= 30 or len(street) >= 30:
            return render_template('register-customer.html', error='Your address is too long!')

        elif len(phone_number) != 11:
            return render_template('register-customer.html', error='Please enter a real phone number!')

        elif len(passport_number) >= 30:
            return render_template('register-customer.html', error='Your passport number is too long!')

        elif len(passport_country) >= 50:
            return render_template('register-customer.html', error='Your passport country is too long!')

        else:
            try:
                phone_number = int(phone_number)
            except:
                return render_template('register-customer.html', error='Please enter a real phone number!')

            try:
                lst = dob.split("-")
                d = datetime.date(day=int(lst[2]), month=int(lst[1]), year=int(lst[0]))
            except:
                return render_template('register-customer.html', error='Please enter a valid birthday!')
            try:
                lst = passport_expiration.split("-")
                d = datetime.datetime(day=int(lst[2]), month=int(lst[1]), year=int(lst[0]))
            except:
                return render_template('register-customer.html', error='Please enter a valid passport expiration!')

            if d < datetime.datetime.now():
                return render_template('register-customer.html', error='Your passport have already expired!')

            md5_pass = md5(password.encode('utf-8')).hexdigest()
            new_id = mt.root_new_user_gen_id(user='root')
            mt.root_insert(user='root', table='customer', value=[email, name, md5_pass, building_number,
                                                                 street, city, state, phone_number, passport_number,
                                                                 passport_expiration, passport_country, dob, new_id])
            # inform user
            # TODO
            session['user'] = email + ":C"
            return back_home()


@app.route('/register/agent/', methods=['POST', 'GET'])
def register_agent():
    if request.method == 'GET':
        return render_template('register-agent.html')

    else:
        email = request.form.get('email')
        password = request.form.get('password')

        # check duplicate
        if mt.root_check_duplicates(table='booking_agent', attribute='email', value=email, user='root'):
            # duplicate
            # TODO
            return render_template('register-agent.html', error='User already exists!')

        else:
            if len(email) >= 50:
                return render_template('register-agent.html', error='Email too long!')
            try:
                email.split('@')[1]
            except:
                return render_template('register-agent.html', error='Please enter a valid email!')
            md5_pass = md5(password.encode('utf-8')).hexdigest()
            agent_id = mt.root_get_new_agent_id(user='root')
            new_id = mt.root_new_user_gen_id(user='root')
            mt.root_insert(user='root', table='booking_agent', value=[email, md5_pass, agent_id, new_id])

            # inform user
            # TODO
            session['user'] = email + ":B"
            return back_home()


@app.route('/register/staff/', methods=['POST', 'GET'])
def register_staff():
    airlines = mt.root_sql_query(user='root', stmt=MySQLTool.STMT_GET_ALL_AIRLINES)
    airlines = [i[0] for i in airlines]
    if request.method == 'GET':
        return render_template('register-staff.html', airlines=airlines)
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('date_of_birth')
        airline_name = request.form.get('airline_name')
        permission_code = request.form.get('permission_code')
        if not mt.root_check_exists(user='root', table='airline_staff_permission_code',
                                    attribute='code', value=permission_code):
            return render_template('register-staff.html', airlines=airlines, error='Your permission code do not '
                                                                                   'exists!')
        # check duplicate
        if mt.root_check_duplicates(table='airline_staff', attribute='username', value=username, user='root'):
            # duplicate
            return render_template('register-staff.html', airlines=airlines, error='User already exists!')
        elif len(first_name) >= 50 or len(last_name) >= 50:
            return render_template('register-staff.html', airlines=airlines, error='Your name is too long!')
        elif airline_name == 'airline' or airline_name == None:
            return render_template('register-staff.html', airlines=airlines, error='Please select airline!')
        else:
            try:
                lst = dob.split("-")
                d = datetime.date(day=int(lst[2]), month=int(lst[1]), year=int(lst[0]))
            except:
                return render_template('register-staff.html', airlines=airlines, error='Please enter a valid '
                                                                                       'birthday!')
            md5_pass = md5(password.encode('utf-8')).hexdigest()
            new_id = mt.root_new_user_gen_id(user='root')
            if mt.root_insert(user='root', table='airline_staff', value=[username, md5_pass, first_name, last_name, dob,
                                                                         airline_name, new_id]):
                session['user'] = username + ":A"
            else:
                return render_template('register-staff.html', airlines=airlines, error='Register failed, please '
                                                                                       'try again later!')
            return back_home()


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if 'user' in session.keys():
        return back_home()
    if request.method == 'GET':
        return render_template('login.html')
    else:
        if request.form.get('customer'):
            return login_customer(email=request.form.get('username'), password=request.form.get('password'))
        if request.form.get('agent'):
            return login_agent(email=request.form.get('username'), password=request.form.get('password'))
        if request.form.get('staff'):
            return login_staff(username=request.form.get('username'), password=request.form.get('password'))


def login_customer(email, password):
    md5_pass = md5(password.encode('utf8')).hexdigest()
    if mt.root_check_exists(user='root', table='customer', attribute=['email', 'password'],
                            value=[email, md5_pass]):
        # login success
        session['user'] = email + ':C'
        return back_home()
    else:
        # login unsuccessful
        return render_template('login.html', error='Wrong username or password!')


def login_agent(email, password):
    md5_pass = md5(password.encode('utf8')).hexdigest()
    if mt.root_check_exists(user='root', table='booking_agent', attribute=['email', 'password'],
                            value=[email, md5_pass]):
        # login success
        session['user'] = email + ':B'
        return back_home()
    else:
        # login unsuccessful
        return render_template('login.html', error='Wrong username or password!')


def login_staff(username, password):
    md5_pass = md5(password.encode('utf8')).hexdigest()
    if mt.root_check_exists(user='root', table='airline_staff', attribute=['username', 'password'],
                            value=[username, md5_pass]):
        # login success
        session['user'] = username + ':A'
        return back_home()
    else:
        # login unsuccessful
        return render_template('login.html', error='Wrong username or password!')


@app.route('/logout', methods=['POST', 'GET'])
def log_out():
    session.clear()
    return back_home()


###########
# home page
###########

@app.route('/')
def home_redirect():
    return back_home()


@app.route('/home/', methods=['POST', 'GET'])
def home():
    if 'user' in session.keys():
        user = session['user']
        user_role = user[-1]
        if user_role == 'A':
            return home_staff(user=user)
        elif user_role == 'B':
            return home_agent(user=user)
        elif user_role == 'C':
            return home_customer(user=user)
        else:
            session.clear()
            return back_home()
    else:
        return home_guest()


def home_guest():
    airline, flight_num, departure_airport, departure_city, departure_time, arrival_airport, arrival_city, \
    arrival_time, price, status, airplane_id = utils.retrieve_get_args_for_flight_query(request)
    airlines_and_cities = utils.get_all_airlines_and_cities(mysqltool=mt)
    if airline == flight_num == departure_airport == departure_city == departure_time == arrival_airport \
            == arrival_city == arrival_time == price == status == airplane_id is None:
        flight_list = utils.flight_list_add_check_ticket_exists(mysqltool=mt,
                                                                flight_list=utils.get_popular_flights(mysqltool=mt))
        my_json = {"msg": "ok", "user": "None", "role": "Guest",
                   "flights": utils.flight_list_to_json_list(flight_list)}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    departure_airport = utils.airport_city_to_airport_name_list(mt, None, departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, None, arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        my_json = {"msg": "ok", "user": "None", "role": "Guest", "flights": []}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    flight_list = mt.guest_query(table='flight', attribute=attribute, value=value)
    flight_list = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=flight_list)
    my_json = {"msg": "ok", 'user': 'Guest', 'role': 'None',
               'flights': utils.flight_list_to_json_list(flight_list)}
    my_json.update(airlines_and_cities)
    return render_template('home.html', data=my_json)


def home_customer(user):
    airline, flight_num, departure_airport, departure_city, departure_time, arrival_airport, arrival_city, \
    arrival_time, price, status, airplane_id = utils.retrieve_get_args_for_flight_query(request)
    airlines_and_cities = utils.get_all_airlines_and_cities(mysqltool=mt)
    if airline == flight_num == departure_airport == departure_city == departure_time == arrival_airport \
            == arrival_city == arrival_time == price == status == airplane_id is None:
        flight_list = utils.get_recommendations(mt, user=user, how_many=10)
        flight_list = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=flight_list)
        my_json = {"msg": "ok", "user": user[:-2], "role": "Customer",
                   "flights": utils.flight_list_to_json_list(flight_list)}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    departure_airport = utils.airport_city_to_airport_name_list(mt, session['user'], departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, session['user'], arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        my_json = {"msg": "ok", "user": user[:-2], "role": "Customer", "flights": []}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.customer_query(user=session['user'], table='flight', attribute=attribute, value=value)
    if price:
        actual_result = []
        for i in result:
            if price[0] <= i[6] <= price[1]:
                actual_result.append(i)
        result = actual_result
    result = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=result)
    my_json = {"msg": "ok", "user": user[:-2], "role": "Customer",
               "flights": utils.flight_list_to_json_list(result)}
    my_json.update(airlines_and_cities)
    return render_template('home.html', data=my_json)


def home_agent(user):
    airline, flight_num, departure_airport, departure_city, departure_time, arrival_airport, arrival_city, \
    arrival_time, price, status, airplane_id = utils.retrieve_get_args_for_flight_query(request)
    airlines_and_cities = utils.get_all_airlines_and_cities(mysqltool=mt)

    if airline == flight_num == departure_airport == departure_city == departure_time == arrival_airport \
            == arrival_city == arrival_time == price == status == airplane_id is None:
        flight_list = utils.get_recommendations(mt, user=user, how_many=10)
        flight_list = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=flight_list)
        my_json = {"msg": "ok", "user": user[:-2], "role": "Booking Agent",
                   "flights": utils.flight_list_to_json_list(flight_list)}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    departure_airport = utils.airport_city_to_airport_name_list(mt, session['user'], departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, session['user'], arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        my_json = {"msg": "ok", "user": user[:-2], "role": "Booking Agent", "flights": []}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.agent_query(user=session['user'], table='flight', attribute=attribute, value=value)
    result = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=result)
    my_json = {"msg": "ok", 'user': user[:-2], 'role': 'Booking Agent',
               'flights': utils.flight_list_to_json_list(result)}
    my_json.update(airlines_and_cities)
    return render_template('home.html', data=my_json)


def home_staff(user):
    airline, flight_num, departure_airport, departure_city, departure_time, arrival_airport, arrival_city, \
    arrival_time, price, status, airplane_id = utils.retrieve_get_args_for_flight_query(request)
    airlines_and_cities = utils.get_all_airlines_and_cities(mysqltool=mt)

    if airline == flight_num == departure_airport == departure_city == departure_time == arrival_airport \
            == arrival_city == arrival_time == price == status == airplane_id is None:
        result = mt.staff_query(user=user, table='flight NATURAL JOIN airline_staff',
                                attribute='username', value=user[:-2])
        result = [i[:9] for i in result]
        result = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=result)
        airlines_and_cities = utils.get_all_airlines_and_cities(mysqltool=mt)
        my_json = {"msg": "ok", 'user': user[:-2], 'role': 'Airline Staff',
                   'flights': utils.flight_list_to_json_list(result)}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    departure_airport = utils.airport_city_to_airport_name_list(mt, session['user'], departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, session['user'], arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        my_json = {"msg": "ok", "user": user[:-2], "role": "Airline Staff", "flights": []}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.staff_query(user=session['user'], table='flight', attribute=attribute, value=value)
    result = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=result)
    my_json = {"msg": "ok", 'user': user[:-2], 'role': 'Airline Staff',
               'flights': utils.flight_list_to_json_list(result)}
    my_json.update(airlines_and_cities)
    return render_template('home.html', data=my_json)


#######################
# extra staff functions
#######################

def staff_insert_flight():
    pass


def staff_update_flight():
    airline_name = mt.root_get_staff_airline(user='root', staff=session['user'][:-2])
    flight_num = request.args.get('flight_num')
    status = request.args.get('status')
    if mt.staff_update(user=session['user'], table='flight',
                       attribute=['status'], value=[status]):
        return str({'msg': 'ok'})
    else:
        return str({'msg': 'failed'})


def staff_delete_flight():
    airline_name = mt.root_get_staff_airline(user='root', staff=session['user'][:-2])
    flight_num = request.args.get('flight_num')
    if mt.staff_del(user=session['user'], table='flight',
                    attribute=['airline_name', 'flight_num'], value=[airline_name, flight_num]):
        return str({'msg': 'ok'})
    else:
        return str({'msg': 'failed'})


def staff_insert_airport():
    airport_name = request.args.get('airport_name')
    airport_city = request.args.get('airport_city')
    if mt.staff_insert(user=session['user'], table='airport', value=[airport_name, airport_city]):
        return str({'msg': 'ok'})
    else:
        return str({'msg': 'failed'})


def staff_insert_airplane():
    airline_name = mt.root_get_staff_airline(user='root', staff=session['user'][:-2])
    airplane_id = int(request.args.get('airplane_id'))
    seats = int(request.args.get('seats'))
    if mt.staff_insert(user=session['user'], table='airplane', value=[airline_name, airplane_id, seats]):
        return str({'msg': 'ok'})
    else:
        return str({'msg': 'failed'})


#################################
# purchase for customer and agent
#################################

@app.route('/purchase/')
def purchase():
    if 'user' not in session.keys():
        return render_template('home.html', data=dict(msg="login_required"))
    if session['user'][-1] == 'C':
        airline_name = request.args.get('airline_name')
        flight_num = int(request.args.get('flight_num'))
        if not airline_name or not flight_num:
            return render_template('home.html', data=dict(msg="ok"))
        if _purchase(customer=session['user'][:-2], agent=None, airline_name=airline_name, flight_num=flight_num):
            print("success")
            return render_template('home.html', data=dict(msg="success"))
        else:
            return render_template('home.html', data=dict(msg="failed"))
    elif session['user'][-1] == 'B':
        airline_name = request.args.get('airline_name')
        flight_num = int(request.args.get('flight_num'))
        customer_email = request.args.get('customer_email')
        if not airline_name or not flight_num or not customer_email:
            return render_template('home.html', data=dict(msg='ok'))
        if _purchase(customer=customer_email, agent=session['user'][:-2],
                     airline_name=airline_name, flight_num=flight_num):
            print(session['user'][:-2])
            return render_template('home.html', data=dict(msg="success"))
        else:
            return render_template('home.html', data=dict(msg="failed"))
    else:
        return render_template('home.html', data=dict(msg="user_not_allowed"))


def _purchase(customer, agent, airline_name, flight_num):
    ticket_id = mt.root_get_ticket_id(user='root', airline_name=airline_name, flight_num=flight_num)
    if not ticket_id:
        return False
    if agent is None:
        date = str(datetime.date.today())
        if not mt.customer_insert(user=customer + ":C", table='purchases', value=[ticket_id, customer, None, date]):
            return False
    else:
        if not mt.root_check_exists(user='root', table='customer', attribute='email', value=customer):
            return False
        date = str(datetime.date.today())
        agent_id = mt.root_get_agent_id_from_email(user='root', email=agent)
        if not mt.agent_insert(user=agent + ":B", table="purchases", value=[ticket_id, customer, agent_id, date]):
            return False
    return True


##############
# profile page
##############

@app.route('/profile/', methods=['POST', 'GET'])
def profile():
    if 'user' in session.keys():
        if session['user'][-1] == 'C':
            return profile_customer(session['user'])
        if session['user'][-1] == 'B':
            return profile_agent(session['user'])
        if session['user'][-1] == 'A':
            return profile_staff(session['user'])
    else:
        return back_home()


def profile_customer(user):
    # get start end time
    start_year = int(request.args.get('start_year')) if request.args.get('start_year') is not None else None
    end_year = int(request.args.get('end_year')) if request.args.get('end_year') is not None else None
    start_month = int(request.args.get('start_month')) if request.args.get('start_month') is not None else None
    end_month = int(request.args.get('end_month')) if request.args.get('end_month') is not None else None
    if start_year and end_year and start_month and end_month:
        start_bar = datetime.date(month=start_month, year=start_year, day=1)
        start_total = datetime.date(month=start_month, year=start_year, day=1)
        if end_year == datetime.date.today().year and end_month == datetime.date.today().month:
            if datetime.date.today().month > 6:
                end = datetime.date(year=datetime.date.today().year,
                                    month=datetime.date.today().month, day=datetime.date.today().day)
            else:
                end = datetime.date(year=datetime.date.today().year,
                                    month=datetime.date.today().month, day=datetime.date.today().day)
        else:
            if end_month == 12:
                end = datetime.date(year=end_year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end = datetime.date(year=end_year, month=end_month + 1, day=1) - timedelta(days=1)
    elif not start_year and not end_year and not start_month and not end_month:
        start_total = datetime.date.today() - timedelta(days=365)
        if datetime.date.today().month > 6:
            start_bar = datetime.date(year=datetime.date.today().year, month=datetime.date.today().month - 5, day=1)
            end = datetime.date(year=datetime.date.today().year,
                                month=datetime.date.today().month, day=datetime.date.today().day)
        else:
            start_bar = datetime.date(year=datetime.date.today().year - 1, month=datetime.date.today().month + 7, day=1)
            end = datetime.date(year=datetime.date.today().year,
                                month=datetime.date.today().month, day=datetime.date.today().day)
    else:
        return str({'msg': 'time_range_incomplete'})

    my_flights = mt.customer_query(user=user, table='flight NATURAL JOIN ticket NATURAL JOIN purchases',
                                   attribute='customer_email', value=user[:-2])
    flights_list = utils.flight_list_to_json_list([i[1:10] for i in my_flights])
    date_price = [(i[12], i[7]) for i in my_flights]

    time_cursor = start_bar
    spent_dict = {}
    total = 0
    while time_cursor <= end:
        key = str(time_cursor.year) + '-' + str(time_cursor.month)
        spent_dict[key] = 0
        if time_cursor.month != 12:
            time_cursor = datetime.date(year=time_cursor.year, month=time_cursor.month + 1, day=1)
        else:
            time_cursor = datetime.date(year=time_cursor.year + 1, month=1, day=1)
    for i in date_price:
        date = i[0]
        price = i[1]
        if start_bar <= date <= end:
            total += price
            key = str(date.year) + '-' + str(date.month)
            spent_dict[key] += price
        elif start_total <= date < start_bar:
            total += price
    my_json = {'user': user[:-2], 'role': 'Customer', 'msg': 'ok',
               'flight': flights_list, 'total': total, 'bar': spent_dict}
    return str(my_json)


def profile_agent(user):
    return 'profile of agent: ' + user


def profile_staff(user):
    return 'profile of staff: ' + user


#################
# extra functions
#################

@app.route('/admin/', methods=['POST', 'GET'])
def admin():
    if request.method == 'GET':
        if request.args.get('action'):
            return render_template('admin_s.html')
        return render_template('admin.html', s='Welcome, Admin!', result=utils.useful_sqls)
    else:
        if request.form.get('password') not in ADMIN:
            return render_template('admin.html', s='Wrong Password')
        stmt = request.form.get('SQL')
        utils.log("Admin {a} execute SQL statement: {s}".format(a=request.form.get('password'), s=stmt))
        if request.form.get("optionsRadiosinline") == 'option2':
            mt.root_sql_alter(user='root', stmt=stmt)
            return render_template('admin.html', s='OK')
        else:
            try:
                result = mt.root_sql_query(user='root', stmt=stmt)
            except Exception as e:
                print(e)
                return render_template('admin.html', s='Your SQL might be wrong!')
            for i in range(len(result)):
                result[i] = str(result[i])
            return render_template('admin.html', s='Here is the result:', result=result)


@app.route('/favicon.ico')
def ico():
    return Response(open(ROOT_DIR + 'static/favicon.ico', 'rb'), mimetype="image/ico")


@app.errorhandler(404)
def error404(error):
    return 'Are you sure about this url?'


@app.errorhandler(403)
def error403(error):
    return 'You access was denied by the server!'


@app.errorhandler(500)
def error500(error):
    mt.refresh()
    return back_home()


def back_home():
    return redirect('/home/', code=302, Response=None)


@app.route('/test/')
def test():
    json_str = {"user": "billy", "role": "customer", "flight": [{"flight_num": "00001"}, {"flight_num": "00002"}]}
    return render_template('test.html', data=json_str)


@app.route('/manual/')
def manual():
    return render_template('Databases_Final_Project_Manual.html')


if __name__ == '__main__':

    if DEBUG:
        app.run(debug=DEBUG, host=HOST, port=PORT)
    else:
        print("LAN IP:", socket.gethostbyname(socket.gethostname()))
        app.run(debug=DEBUG, host='0.0.0.0', port=80)
