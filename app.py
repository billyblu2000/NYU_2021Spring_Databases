import datetime

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


@app.route('/register/')
def register():
    return render_template('index.html')


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
            return render_template('register-customer.html', error = 'User already exists!')

        elif len(email) >= 50 or len(email.split("@")) < 2:
            return render_template('register-customer.html', error = 'Please enter a valid email!')

        elif len(name) >= 50:
            return render_template('register-customer.html', error = 'Your name is too long!')

        elif len(city) >= 30 or len(state)>= 30 or len(building_number)>=30 or len(street) >= 30:
            return render_template('register-customer.html', error = 'Your address is too long!')

        elif len(phone_number) != 11:
            return render_template('register-customer.html', error = 'Please enter a real phone number!')

        elif len(passport_number) >= 30:
            return render_template('register-customer.html', error = 'Your passport number is too long!')

        elif len(passport_country) >= 50:
            return render_template('register-customer.html', error = 'Your passport country is too long!')

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
            return render_template('register-agent.html', error = 'User already exists!')

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
        return render_template('register-staff.html', airlines= airlines)
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
            return render_template('register-staff.html', airlines= airlines, error = 'Your permission code do not '
                                                                                      'exists!')
        # check duplicate
        if mt.root_check_duplicates(table='airline_staff', attribute='username', value=username, user='root'):
            # duplicate
            return render_template('register-staff.html', airlines= airlines, error = 'User already exists!')
        elif len(first_name) >= 50 or len(last_name)>=50:
            return render_template('register-staff.html', airlines= airlines, error = 'Your name is too long!')
        elif airline_name == 'airline' or airline_name == None:
            return render_template('register-staff.html', airlines=airlines, error='Please select airline!')
        else:
            try:
                lst = dob.split("-")
                d = datetime.date(day=int(lst[2]),month=int(lst[1]),year=int(lst[0]))
            except:
                return render_template('register-staff.html', airlines= airlines, error = 'Please enter a valid '
                                                                                          'birthday!')
            md5_pass = md5(password.encode('utf-8')).hexdigest()
            new_id = mt.root_new_user_gen_id(user='root')
            if mt.root_insert(user='root', table='airline_staff', value=[username, md5_pass, first_name, last_name, dob,
                                                                      airline_name, new_id]):
                session['user'] = username + ":A"
            else:
                return render_template('register-staff.html', airlines= airlines, error = 'Register failed, please '
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
        return render_template('login.html', error = 'Wrong username or password!')


def login_agent(email, password):
    md5_pass = md5(password.encode('utf8')).hexdigest()
    if mt.root_check_exists(user='root', table='booking_agent', attribute=['email', 'password'],
                            value=[email, md5_pass]):
        # login success
        session['user'] = email + ':B'
        return back_home()
    else:
        # login unsuccessful
        return render_template('login.html', error = 'Wrong username or password!')


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

    departure_airport = utils.airport_city_to_airport_name_list(mt, None, departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, None, arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        return ''

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.guest_query(table='flight', attribute=attribute, value=value)
    return 'Home page: Guest' + '</br>' + mt.pretty(result)


def home_customer(user):
    airline, flight_num, departure_airport, departure_city, departure_time, arrival_airport, arrival_city, \
    arrival_time, price, status, airplane_id = utils.retrieve_get_args_for_flight_query(request)

    departure_airport = utils.airport_city_to_airport_name_list(mt, None, departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, None, arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        return ''

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.guest_query(table='flight', attribute=attribute, value=value)
    if price:
        actual_result = []
        for i in result:
            if price[0] <= i[6] <= price[1]:
                actual_result.append(i)
        result = actual_result
    return 'Home page: customer ' + session['user'] + '</br>' + mt.pretty(result)


def home_agent(user):
    airline, flight_num, departure_airport, departure_city, departure_time, arrival_airport, arrival_city, \
    arrival_time, price, status, airplane_id = utils.retrieve_get_args_for_flight_query(request)

    departure_airport = utils.airport_city_to_airport_name_list(mt, None, departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, None, arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        return ''

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.guest_query(table='flight', attribute=attribute, value=value)
    return 'Home page: booking agent ' + session['user'] + '</br>' + mt.pretty(result)


def home_staff(user):
    airline, flight_num, departure_airport, departure_city, departure_time, arrival_airport, arrival_city, \
    arrival_time, price, status, airplane_id = utils.retrieve_get_args_for_flight_query(request)

    departure_airport = utils.airport_city_to_airport_name_list(mt, None, departure_city, departure_airport)
    arrival_airport = utils.airport_city_to_airport_name_list(mt, None, arrival_city, arrival_airport)
    if departure_airport == False or arrival_airport == False:
        return ''

    attribute = ['airline_name', 'flight_num', 'departure_airport', 'departure_time', 'arrival_airport', 'arrival_time']
    value = [airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time]
    result = mt.guest_query(table='flight', attribute=attribute, value=value)
    return 'Home page: airline staff ' + session['user'] + '</br>' + mt.pretty(result)


@app.route('/profile/', methods=['POST', 'GET'])
def profile_redirect():
    if 'user' in session.keys():
        user = session['user']
        user_name = user[:-2]
        user_role = user[-1]
        uid = mt.root_get_uid(user='root', role=user_role, pk=user_name)[0][0]
        return redirect('/profile/{uid}/'.format(uid=uid))

    else:
        return back_home()


@app.route('/profile/<uid>/', methods=['POST', 'GET'])
def profile(uid):
    if 'user' in session.keys():
        user_name = session['user'][:-2]
        user_role = session['user'][-1]
        if user_role == 'A':
            if mt.root_check_exists(user='root', table='airline_staff',
                                    attribute=['username', 'uid'], value=[user_name, uid]):
                return profile_staff(user=session['user'])
            else:
                return
        elif user_role == 'B':
            if mt.root_check_exists(user='root', table='booking_agent',
                                    attribute=['email', 'uid'], value=[user_name, uid]):
                return profile_agent(user=session['user'])
        elif user_role == 'C':
            if mt.root_check_exists(user='root', table='customer',
                                    attribute=['email', 'uid'], value=[user_name, uid]):
                return profile_customer(user=session['user'])
        else:
            return back_home()
    else:
        return back_home()


def profile_customer(user):
    return 'profile of customer: ' + user


def profile_agent(user):
    return 'profile of agent: ' + user


def profile_staff(user):
    return 'profile of staff: ' + user


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
        print(stmt)
        if request.form.get("optionsRadiosinline") == 'option2':
            mt.root_sql_alter(user='root', stmt=stmt)
            return render_template('admin.html', s='OK')
        else:
            try:
                result = mt.root_sql_query(user='root', stmt=stmt)
            except Exception as e:
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
    return back_home()


def back_home():
    return redirect('/home/', code=302, Response=None)


@app.route('/test/')
def test():
    num = request.args.get('num')
    if num is None:
        num = 10
    else:
        num = int(num)
    if 'user' in session.keys():
        rec = utils.get_recommendations(mt, user=session['user'], how_many=num)
        return mt.pretty(rec)
    else:
        return ''


if __name__ == '__main__':

    if DEBUG:
        app.run(debug=DEBUG, host=HOST, port=PORT)
    else:
        print("LAN IP:", socket.gethostbyname(socket.gethostname()))
        app.run(debug=DEBUG, host='0.0.0.0', port=80)
