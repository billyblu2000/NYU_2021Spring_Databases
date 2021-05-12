"""
project main functions;
run this file to start the app
"""

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


@app.route('/logout/', methods=['POST', 'GET'])
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
        my_json = {"msg": "ok", "user": "None", "role": "Guest", 'searched': 0,
                   "flights": utils.flight_list_to_json_list(flight_list)}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)
    departure_airport = utils.airport_city_to_airport_name_list(mt, None, departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, None, arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        my_json = {"msg": "ok", "user": "None", "role": "Guest", "flights": [], 'searched': 0, }
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)
    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    flight_list = mt.guest_query(table='flight', attribute=attribute, value=value)
    flight_list = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=flight_list)
    my_json = {"msg": "ok", 'user': 'None', 'role': 'Guest', 'searched': 1,
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
        if len(flight_list) == 0:
            flight_list = utils.get_popular_flights(mysqltool=mt)
        flight_list = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=flight_list)
        my_json = {"msg": "ok", "user": user[:-2], "role": "Customer", 'searched': 0,
                   "flights": utils.flight_list_to_json_list(flight_list)}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    departure_airport = utils.airport_city_to_airport_name_list(mt, session['user'], departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, session['user'], arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        my_json = {"msg": "ok", "user": user[:-2], "role": "Customer", "flights": [], 'searched': 0, }
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    print(value)
    result = mt.customer_query(user=session['user'], table='flight', attribute=attribute, value=value)
    if price:
        actual_result = []
        for i in result:
            if price[0] <= i[6] <= price[1]:
                actual_result.append(i)
        result = actual_result
    result = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=result)
    my_json = {"msg": "ok", "user": user[:-2], "role": "Customer", 'searched': 1,
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
        if len(flight_list) == 0:
            flight_list = utils.get_popular_flights(mysqltool=mt)
        flight_list = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=flight_list)
        my_json = {"msg": "ok", "user": user[:-2], "role": "Agent", 'searched': 0,
                   "flights": utils.flight_list_to_json_list(flight_list)}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    departure_airport = utils.airport_city_to_airport_name_list(mt, session['user'], departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, session['user'], arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        my_json = {"msg": "ok", "user": user[:-2], "role": "Agent", "flights": [], 'searched': 0, }
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.agent_query(user=session['user'], table='flight', attribute=attribute, value=value)
    result = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=result)
    my_json = {"msg": "ok", 'user': user[:-2], 'role': 'Agent', 'searched': 1,
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
        my_json = {"msg": "ok", 'user': user[:-2], 'role': 'Staff', 'searched': 0,
                   'flights': utils.flight_list_to_json_list(result)}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    departure_airport = utils.airport_city_to_airport_name_list(mt, session['user'], departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, session['user'], arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        my_json = {"msg": "ok", "user": user[:-2], "role": "Staff", "flights": [], 'searched': 0}
        my_json.update(airlines_and_cities)
        return render_template('home.html', data=my_json)

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.staff_query(user=session['user'], table='flight', attribute=attribute, value=value)
    staff_airline = mt.root_get_staff_airline(user='root', staff=session['user'][:-2])
    new_result = []
    for i in result:
        if i[0] == staff_airline:
            new_result.append(i)
    result = new_result
    result = utils.flight_list_add_check_ticket_exists(mysqltool=mt, flight_list=result)
    my_json = {"msg": "ok", 'user': user[:-2], 'role': 'Staff', 'searched': 1,
               'flights': utils.flight_list_to_json_list(result)}
    my_json.update(airlines_and_cities)
    return render_template('home.html', data=my_json)


#######################
# extra staff functions
#######################

@app.route('/home/insert/flight/')
def staff_insert_flight():
    if session['user'][-1] != 'A':
        return back_home()
    airplanes = mt.root_sql_query(user='root', stmt=mt.STMT_GET_ALL_AIRPLANES_FOR_AIRLINE,
                                  value=[session['user'][:-2]])
    airplanes = [i[0] for i in airplanes]
    airports = mt.root_sql_query(user='root', stmt=mt.STMT_GET_ALL_AIRPORTS)
    airports = [i[0] for i in airports]
    if request.method == 'GET' and not request.args.get('flight_num'):
        return render_template('insert_flight.html', data={'airport': airports, 'airplane': airplanes})
    else:
        flight_num = request.args.get('flight_num')
        departure_time = request.args.get('departure_time') + ':00'
        arrival_time = request.args.get('arrival_time') + ':00'
        departure_airport = request.args.get('departure_airport')
        arrival_airport = request.args.get('arrival_airport')
        price = request.args.get('price')
        status = request.args.get('status')
        airplane_id = request.args.get('airplane_id')

        try:
            print(flight_num, price, airplane_id)
            flight_num = int(flight_num)
            price = int(price)
            airplane_id = int(airplane_id)
        except:
            return render_template('insert_flight.html', data={'airport': airports, 'airplane': airplanes,
                                                               'msg': 'Invaild Data!'})

        ticket = request.args.get('ticket')
        if ticket == 'ticket':
            ticket_number = None
            c = True
        else:
            ticket_number = 0
            c = False

        airline_name = mt.root_get_staff_airline(user='root', staff=session['user'][:-2])
        if mt.staff_insert(user=session['user'], table='flight', ticket_number=ticket_number, create_ticket=c,
                           value=[airline_name, flight_num, departure_airport, departure_time,
                                  arrival_airport, arrival_time, price, status, airplane_id]):
            return render_template('insert_flight.html', data={'airport': airports, 'airplane': airplanes,
                                                               'msg': 'Inserted!'})
        else:
            return str({'msg': 'Failed!'})


@app.route('/home/update/')
def staff_update_flight():
    if session['user'][-1] != 'A':
        return back_home()
    airline_name = mt.root_get_staff_airline(user='root', staff=session['user'][:-2])
    flight_num = int(request.args.get('flight_num'))
    if not mt.root_check_exists(user='root', table='flight', attribute=['airline_name', 'flight_num'],
                            value=[airline_name, flight_num]):
        return 'Update failed you do not belongs to this airline'
    status = request.args.get('status')
    if mt.staff_update(user=session['user'], table='flight', pk=[airline_name, flight_num],
                       attribute=['status'], value=[status]):
        return back_home()
    else:
        return 'Update failed you do not belongs to this airline?'


@app.route('/home/insert/airport/')
def staff_insert_airport():
    if session['user'][-1] != 'A':
        return back_home()
    if request.method == 'GET' and not request.args.get('airport_name'):
        return render_template('insert_airport.html', data={'msg': ''})
    else:
        airport_name = request.args.get('airport_name')
        airport_city = request.args.get('airport_city')
        if mt.staff_insert(user=session['user'], table='airport', create_ticket=False,
                           value=[airport_name, airport_city]):
            return render_template('insert_airport.html', data={'msg': 'Inserted!'})
        else:
            return render_template('insert_airport.html', data={'msg': 'Failed! Please check if airport already '
                                                                       'exists!'})


@app.route('/home/insert/airplane/')
def staff_insert_airplane():
    if session['user'][-1] != 'A':
        return back_home()
    if request.method == 'GET' and not request.args.get('airplane_id'):
        result = mt.root_sql_query(user='root', stmt=mt.STMT_GET_ALL_AIRPLANES_GIVEN_STAFF,
                                   value=[session['user'][:-2]])
        data = {'airplane': result}
        return render_template('insert_airplane.html', data=data)
    else:
        airline_name = mt.root_get_staff_airline(user='root', staff=session['user'][:-2])
        airplane_id = int(request.args.get('airplane_id'))
        seats = int(request.args.get('seats'))
        if mt.staff_insert(user=session['user'], table='airplane', create_ticket=False,
                           value=[airline_name, airplane_id, seats]):
            result = mt.root_sql_query(user='root', stmt=mt.STMT_GET_ALL_AIRPLANES_GIVEN_STAFF,
                                       value=[session['user'][:-2]])
            data = {'airplane': result, 'msg': 'Inserted!'}
            return render_template('insert_airplane.html', data=data)
        else:
            result = mt.root_sql_query(user='root', stmt=mt.STMT_GET_ALL_AIRPLANES_GIVEN_STAFF,
                                       value=[session['user'][:-2]])
            data = {'airplane': result, 'msg': 'Failed! Please check your airplane id or seats!'}
            return render_template('insert_airplane.html', data=data)


#################################
# purchase for customer and agent
#################################

@app.route('/purchase/')
def purchase():
    if 'user' not in session.keys():
        return render_template('login.html', data=dict(msg="login_required"))
    if session['user'][-1] == 'C':
        airline_name = request.args.get('airline_name')
        flight_num = int(request.args.get('flight_num'))
        if not airline_name or not flight_num:
            return render_template('home.html', data=dict(msg="ok"))
        if _purchase(customer=session['user'][:-2], agent=None, airline_name=airline_name, flight_num=flight_num):
            return render_template('purchase_success.html', data=dict(msg="ok"))
        else:
            return render_template('purchase_failed.html', data=dict(msg="no ticket left"))
    elif session['user'][-1] == 'B':
        airline_name = request.args.get('airline_name')
        flight_num = int(request.args.get('flight_num'))
        customer_email = request.args.get('customer_email')
        if not customer_email:
            return render_template('agent_purchase.html', data={'airline_name': airline_name,
                                                                'flight_num': flight_num})
        if not airline_name or not flight_num or not customer_email:
            return render_template('home.html', data=dict(msg='ok'))
        if _purchase(customer=customer_email, agent=session['user'][:-2],
                     airline_name=airline_name, flight_num=flight_num):
            print(session['user'][:-2])
            return render_template('purchase_success.html', data=dict(msg="ok"))
        else:
            return render_template('purchase_failed.html', data=dict(msg="unknown_reason"))
    else:
        return render_template('purchase_failed.html', data=dict(msg="user_not_allowed"))


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
    start_total, start_bar, end = utils.retrieve_get_args_for_customer_date_spent(request)

    my_flights = mt.customer_query(user=user, table='flight NATURAL JOIN ticket NATURAL JOIN purchases',
                                   attribute='customer_email', value=user[:-2])
    flights_list = utils.flight_list_to_json_list([i[1:10] for i in my_flights])
    date_price = [(i[12], i[7]) for i in my_flights]

    if start_total is False:
        my_json = {'user': user[:-2], 'role': 'Customer', 'msg': 'time incomplete',
                   'flight': flights_list, }
        return render_template('profile.html', data=my_json)

    time_cursor = start_bar
    spent_dict = {}
    total = 0
    while time_cursor <= end:
        key = str(time_cursor.year) + "-" + str(time_cursor.month)
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
    spent_dict = [[i, int(spent_dict[i])] for i in spent_dict.keys()]
    print(spent_dict)
    my_json = {'user': user[:-2], 'role': 'Customer', 'msg': 'ok',
               'flight': flights_list, 'total': total, 'bar': spent_dict}
    print(my_json)
    return render_template('profile.html', data=my_json)


def profile_agent(user):
    start, end = utils.retrieve_get_args_for_agent_date_commission(request)

    id = mt.root_get_agent_id_from_email(user='root', email=user[:-2])
    my_flights = mt.agent_query(user=user, table='flight NATURAL JOIN ticket NATURAL JOIN purchases',
                                attribute='booking_agent_id', value=id)
    flights_list = utils.flight_list_to_json_list([i[1:10] for i in my_flights])
    customer_date_price = [(i[10], i[12], i[7]) for i in my_flights]

    six_month_before = datetime.date.today() - timedelta(days=30 * 6)
    one_year_before = datetime.date.today() - timedelta(days=365)
    now = datetime.date.today()
    top_five_bought, top_five_commission = {}, {}

    for i in customer_date_price:
        if six_month_before <= i[1] <= now:
            if i[0] not in top_five_commission:
                top_five_commission[i[0]] = i[2] / 10
            else:
                top_five_commission[i[0]] += i[2] / 10
            if i[0] not in top_five_bought:
                top_five_bought[i[0]] = 1
            else:
                top_five_bought[i[0]] += 1
        elif one_year_before <= i[1] <= now:
            if i[0] not in top_five_commission:
                top_five_commission[i[0]] = i[2] / 10
            else:
                top_five_commission[i[0]] += i[2] / 10

    top_five_bought_list = sorted(top_five_bought.items(), key=lambda x: x[1], reverse=True)
    top_five_commission_list = sorted(top_five_commission.items(), key=lambda x: x[1], reverse=True)
    nb = 5 if len(top_five_bought_list) >= 5 else len(top_five_bought_list)
    nc = 5 if len(top_five_commission_list) >= 5 else len(top_five_commission_list)
    top_five_bought = {top_five_bought_list[i][0]: top_five_bought_list[i][1] for i in range(nb)}
    top_five_commission = {top_five_commission_list[i][0]: top_five_commission_list[i][1] for i in range(nc)}

    if start is False:
        my_json = {'user': user[:-2], 'role': 'Agent', 'msg': 'time incomplete',
                   'flight': flights_list, 'top_five_bought': top_five_bought,
                   'top_five_commission': top_five_commission}
        return render_template('profile.html', data=my_json)

    total_commission = 0
    ticket_num = 0
    for i in customer_date_price:
        if start <= i[1] <= end:
            total_commission += i[2]
            ticket_num += 1
    if ticket_num == 0:
        average_commission = 0
    else:
        average_commission = total_commission / ticket_num

    top_five_bought = [[i[0], i[1]] for i in top_five_bought.items()]
    top_five_commission = [[i[0], i[1]] for i in top_five_commission.items()]

    my_json = {'user': user[:-2], 'role': 'Agent', 'msg': 'ok',
               'flight': flights_list, 'top_five_bought': top_five_bought, 'top_five_commission': top_five_commission,
               'total_commission': total_commission, 'average_commission': average_commission,
               'total_sold': ticket_num}

    print(my_json)
    return render_template('profile.html', data=my_json)


def profile_staff(user):
    # functions too complected, moved to utils.py
    top_ba_ticket_last_month, top_ba_ticket_last_year, top_ba_commission_last_year = \
        utils.staff_functions(mt, user, request, action='all_booking_agents')
    frequent_customer, customer_flight = utils.staff_functions(mt, user, request, action='frequent_customers')
    customer_flight = utils.flight_list_to_json_list(customer_flight)
    total_ticket, month_wise_ticket = utils.staff_functions(mt, user, request, action='report')
    result = utils.staff_functions(mt, user, request, action='revenue')
    result = [result[i] if result[i] is not None else 0 for i in range(len(result))]
    revenue_direct_last_month, revenue_direct_last_year, \
    revenue_indirect_last_month, revenue_indirect_last_year = \
        result[0], result[1], result[2], result[3]
    top_destination_last_three_month, top_destination_last_year = \
        utils.staff_functions(mt, user, request, action='destinations')
    myjson = {'user': user[:-2], 'role': 'Staff', 'msg': 'ok',
              'top_ba_ticket_last_month': top_ba_ticket_last_month,
              'top_ba_ticket_last_year': top_ba_ticket_last_year,
              'top_ba_commission_last_year': top_ba_commission_last_year,
              'frequent_customer': frequent_customer,
              'customer_email': request.args.get('customer_email'),
              'customer_flight': customer_flight,
              'total_ticket': total_ticket,
              'month_wise_ticket': month_wise_ticket,
              'revenue_direct_last_month': revenue_direct_last_month,
              'revenue_direct_last_year': revenue_direct_last_year,
              'revenue_indirect_last_month': revenue_indirect_last_month,
              'revenue_indirect_last_year': revenue_indirect_last_year,
              'top_destination_last_three_month': top_destination_last_three_month,
              'top_destination_last_year': top_destination_last_year}
    return render_template('profile.html', data=myjson)


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
    stmt = 'select airline_name, flight_num from flight'
    result = mt.root_sql_query(user='root', stmt=stmt)
    insert = 'INSERT INTO ticket values '
    id = 1000000000
    for i in result:
        temp = "(" + str(id) + ", " + "'" + i[0] + "'" + ", " + str(i[1]) + ")" + ", "
        temp += "(" + str(id + 1) + ", " + "'" + i[0] + "'" + ", " + str(i[1]) + ")" + ", "
        temp += "(" + str(id + 2) + ", " + "'" + i[0] + "'" + ", " + str(i[1]) + ")" + ", "
        temp += "(" + str(id + 3) + ", " + "'" + i[0] + "'" + ", " + str(i[1]) + ")" + ", "
        temp += "(" + str(id + 4) + ", " + "'" + i[0] + "'" + ", " + str(i[1]) + ")" + ", "
        insert += temp
        id += 5
    insert = insert.rstrip(', ')
    print(insert)

    insert = 'INSERT INTO user VALUES (14), (15), (16), (17), (18), (19), (20), (21),(22), (23),(24), (25),' \
             '(26), (27),(28), (29), (30), (31), (32), (33), (34), (35), (36), (37), (38), (39), (40), (41)'
    print(insert)
    insert = 'INSERT INTO airline_staff VALUES '
    insert += "('ce@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 'TEST', 'TEST', '2000-01-01', 'China Eastern', 14),"
    insert += "('cs@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 'TEST', 'TEST', '2000-01-01', 'China Southern', 15),"
    insert += "('ha@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 'TEST', 'TEST', '2000-01-01', 'Hainan Airlines', 16),"
    insert += "('sa@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 'TEST', 'TEST', '2000-01-01', 'Sichuan Airlines', 17),"
    insert += "('ja@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 'TEST', 'TEST', '2000-01-01', 'Japan Airlines', 18),"
    insert += "('aa@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 'TEST', 'TEST', '2000-01-01', 'America Airlines', 19),"
    insert += "('ac@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 'TEST', 'TEST', '2000-01-01', 'Air Canada', 20),"
    insert += "('af@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 'TEST', 'TEST', '2000-01-01', 'Air France', 21),"
    print(insert)
    insert = 'INSERT INTO customer VALUES '
    x = "'688dd96ed8c69b66d1f3e6a494050d28', '1555', 'Century Avenue','Shanghai', 'Shanghai', 18210770129, 'E00000001', '2029-01-01', 'China', '2000-01-01',"
    insert += "('jack@nyu.edu', 'Jack', " + x + " 22),"
    insert += "('andy@nyu.edu', 'Andy', " + x + " 23),"
    insert += "('lucy@nyu.edu', 'Lucy', " + x + " 24),"
    insert += "('wayne@nyu.edu', 'Wayne', " + x + " 25),"
    insert += "('tomas@nyu.edu', 'Tomas', " + x + " 26),"
    insert += "('lily@nyu.edu', 'Lily', " + x + " 27),"
    insert += "('eric@nyu.edu', 'Eric', " + x + " 28),"
    insert += "('harry@nyu.edu', 'Harry', " + x + " 29),"
    insert += "('mike@nyu.edu', 'Mike', " + x + " 30),"
    insert += "('richard@nyu.edu', 'Richard', " + x + " 31),"
    insert += "('fred@nyu.edu', 'Fred', " + x + " 32),"
    insert += "('bill@nyu.edu', 'Bill', " + x + " 33),"
    insert += "('michael@nyu.edu', 'Michael', " + x + " 34),"
    print(insert)
    insert = 'INSERT INTO booking_agent VALUES '
    insert += "('albert@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 4, 35),"
    insert += "('carl@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 5, 36),"
    insert += "('david@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 6, 37),"
    insert += "('george@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 7, 38),"
    insert += "('gavin@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 8, 39),"
    insert += "('justin@nyu.edu', '688dd96ed8c69b66d1f3e6a494050d28', 9, 40),"
    print(insert)
    return 'ok'


@app.route('/manual/')
def manual():
    return render_template('Databases_Final_Project_Manual.html')


if __name__ == '__main__':

    if DEBUG:
        app.run(debug=DEBUG, host=HOST, port=PORT)
    else:
        print("LAN IP:", socket.gethostbyname(socket.gethostname()))
        app.run(debug=DEBUG, host='0.0.0.0', port=80)
