"""
util functions that mostly called by functions in app.py
a few will be called by MySQLTool
"""

import json
import time
from functools import wraps
import datetime
import numpy as np

from config import SQL_LOG

# parameters used in get_recommendations()
recommendations_params = {
    'airline': -0.000001,
    'city_weight': 0.6,
    'airport_weight': 0.4,
}

# string used in admin page
useful_sqls = ["-------------------------",
               "Useful SQLs",
               "-------------------------",
               "Return flight that a user purchased",
               "SELECT airline_name, departure_airport, arrival_airport, departure_time, price, purchase_date "
               "FROM (purchases INNER JOIN ticket USING (ticket_id)) INNER JOIN flight USING (airline_name, flight_num) "
               "WHERE customer_email = ''",
               "Return spent in a date interval",
               "SELECT SUM(price) "
               "FROM (purchases INNER JOIN ticket USING (ticket_id)) INNER JOIN flight USING (airline_name, flight_num) "
               "WHERE purchase_date > '' AND purchase_date < ''",
               ]


# APP log, can switch off in config.py by setting SQL_LOG = False
def log(*args):
    if SQL_LOG:
        print("APP LOG - - [{t}] - ".format(t=time.asctime(time.localtime())), end=' ')
        for i in args:
            print(i, end=' ')
        print('')


# decorator to validate user before method executed
def validate_user(role="ABC"):
    def decorator(func):

        @wraps(func)
        def decorated(*args, **kwargs):
            user = kwargs['user']
            if user is not 'root':
                log("{u} applies to call method '{f}'".format(u=user[:-2], f=func.__name__))
            if user == 'root':
                return func(*args, **kwargs)

            key, identity = user[:-2], user[-1]
            cursor = args[0].get_connection().cursor(prepared=True)

            if identity not in role:
                log("Unauthorized user, blocked")
                return None

            if identity == 'A':
                identity = 'Airline Staff'
                stmt = 'SELECT username FROM airline_staff WHERE username = %s'
            elif identity == 'B':
                identity = 'Booking Agent'
                stmt = 'SELECT email FROM booking_agent WHERE email = %s'
            elif identity == 'C':
                identity = 'Customer'
                stmt = 'SELECT email FROM customer WHERE email = %s'
            else:
                raise Exception("Can't understand user when validation")

            cursor.execute(stmt, [key])
            result = cursor.fetchall()

            if len(result) == 1:
                log("User validated as {i}, permission granted".format(i=identity))
                return func(*args, **kwargs)
            else:
                log("Unknown user, blocked")
                return None

        return decorated

    return decorator


###############################
# some functions to retrieve
# the GET arguments in requests
###############################

def retrieve_get_args_for_flight_query(request):
    departure_city = get_arg_value_with_key_name(request,'departure_city')
    departure_airport = get_arg_value_with_key_name(request,'departure_airport')
    arrival_city = get_arg_value_with_key_name(request,'arrival_city')
    arrival_airport = get_arg_value_with_key_name(request,'arrival_airport')
    departure_time = get_arg_value_with_key_name(request,'departure_time')
    arrival_time = get_arg_value_with_key_name(request,'arrival_time')
    flight_num = get_arg_value_with_key_name(request,'flight_num')
    airline = get_arg_value_with_key_name(request,'airline_name')
    if flight_num:
        flight_num = int(flight_num)
    price, status, airplane_id = None, None, None
    return (airline, flight_num, departure_airport, departure_city, departure_time,
            arrival_airport, arrival_city, arrival_time, price, status, airplane_id)


def get_arg_value_with_key_name(request, key):
    result = request.args.get(key)
    if result != '' and result is not None:
        return result
    else:
        return None


def retrieve_get_args_for_customer_date_spent(request):
    start = request.args.get('start_month')
    end = request.args.get('end_month')
    if start and end:
        start_year = int(start[:4])
        start_month = int(start[5:])
        end_year = int(end[:4])
        end_month = int(end[5:])
    else:
        start_year, end_year, start_month, end_month = None, None, None, None
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
                end = datetime.date(year=end_year + 1, month=1, day=1) - datetime.timedelta(days=1)
            else:
                end = datetime.date(year=end_year, month=end_month + 1, day=1) - datetime.timedelta(days=1)
    elif not start_year and not end_year and not start_month and not end_month:
        start_total = datetime.date.today() - datetime.timedelta(days=365)
        if datetime.date.today().month > 6:
            start_bar = datetime.date(year=datetime.date.today().year, month=datetime.date.today().month - 5, day=1)
            end = datetime.date(year=datetime.date.today().year,
                                month=datetime.date.today().month, day=datetime.date.today().day)
        else:
            start_bar = datetime.date(year=datetime.date.today().year - 1, month=datetime.date.today().month + 7, day=1)
            end = datetime.date(year=datetime.date.today().year,
                                month=datetime.date.today().month, day=datetime.date.today().day)
    else:
        return False, False, False
    return start_total, start_bar, end


def retrieve_get_args_for_agent_date_commission(request):
    start = request.args.get('start')
    end = request.args.get('end')
    if start and end:
        start_year = int(start[:4])
        start_month = int(start[5:7])
        start_date = int(start[8:])
        end_year = int(end[:4])
        end_month = int(end[5:7])
        end_date = int(end[8:])
    else:
        start_year, end_year, start_month, end_month, start_date, end_date = None, None, None, None, None, None
    if start_year and end_year and start_month and end_month and start_date and end_date:
        start = datetime.date(year=start_year, month=start_month, day=start_date)
        end = datetime.date(year=end_year, month=end_month, day=end_date)
    else:
        start = datetime.date.today() - datetime.timedelta(days=30)
        end = datetime.date.today()
    return start, end


def retrieve_get_args_for_staff_date_report(request):
    start = request.args.get('start')
    end = request.args.get('end')
    if start and end:
        start_year = int(start[:4])
        start_month = int(start[5:7])
        start_date = int(start[8:])
        end_year = int(end[:4])
        end_month = int(end[5:7])
        end_date = int(end[8:])
    else:
        start_year, end_year, start_month, end_month, start_date, end_date = None, None, None, None, None, None
    if start_year and end_year and start_month and end_month and start_date and end_date:
        start = datetime.date(year=start_year, month=start_month, day=start_date)
        end = datetime.date(year=end_year, month=end_month, day=end_date)
    else:
        start = datetime.date.today() - datetime.timedelta(days=183)
        end = datetime.date.today()
    return start, end


def staff_functions(mysqltool, mysqltool_user, request, action, user=None):
    if action == 'all_booking_agents':
        result = mysqltool.staff_query(user=mysqltool_user,
                                       table='flight NATURAL JOIN ticket NATURAL JOIN purchases NATURAL JOIN '
                                             'booking_agent')
        result = [list(result[i]) for i in range(len(result))]
        for i in range(len(result)):
            if result[i] is not None:
                for j in range(len(result[i])):
                    if type(result[i][j]) is bytearray:
                        result[i][j] = result[i][j].decode('utf-8')
        price_email_date = [(i[8], i[13], i[12]) for i in result]
        one_month_before = datetime.date.today() - datetime.timedelta(days=30)
        one_year_before = datetime.date.today() - datetime.timedelta(days=365)
        top_ticket_last_month, top_ticket_last_year, top_commission_last_year = {}, {}, {}
        for i in price_email_date:
            if i[2] > one_month_before:
                if i[1] not in top_ticket_last_month.keys():
                    top_ticket_last_month[i[1]] = 1
                else:
                    top_ticket_last_month[i[1]] += 1
                if i[1] not in top_ticket_last_year.keys():
                    top_ticket_last_year[i[1]] = 1
                else:
                    top_ticket_last_year[i[1]] += 1
                if i[1] not in top_commission_last_year.keys():
                    top_commission_last_year[i[1]] = i[0]
                else:
                    top_commission_last_year[i[1]] += i[0]
            elif i[2] > one_year_before:
                if i[1] not in top_ticket_last_year.keys():
                    top_ticket_last_year[i[1]] = 1
                else:
                    top_ticket_last_year[i[1]] += 1
                if i[1] not in top_commission_last_year.keys():
                    top_commission_last_year[i[1]] = i[0]
                else:
                    top_commission_last_year[i[1]] += i[0]
        top_ticket_last_month = sort_dictionary(top_ticket_last_month, limit=5)
        top_commission_last_year = sort_dictionary(top_commission_last_year, limit=5)
        top_ticket_last_year = sort_dictionary(top_ticket_last_year, limit=5)
        return list(top_ticket_last_month.keys()), \
               list(top_ticket_last_year.keys()), \
               list(top_commission_last_year.keys())

    elif action == 'frequent_customers':
        one_year_before = datetime.date.today() - datetime.timedelta(days=365)
        stmt = 'WITH customer_count AS (SELECT customer_email, COUNT(customer_email) AS cc ' \
               'FROM flight NATURAL JOIN ticket NATURAL JOIN purchases WHERE purchase_date >= %s GROUP BY customer_email) ' \
               'SELECT customer_email FROM customer_count WHERE customer_count.cc = (' \
               'SELECT MAX(cc) FROM customer_count)'
        try:
            frequent_customer = mysqltool.root_sql_query(user='root', stmt=stmt, value=[str(one_year_before)])[0][0]
        except:
            return None, None

        stmt = 'SELECT * FROM customer WHERE email = %s'
        customer_info = mysqltool.root_sql_query(user='root', stmt=stmt, value=[frequent_customer])[0]
        if len(customer_info) != 0:
            customer_info = {
                'email':customer_info[0],
                'name':customer_info[1],
                'city':customer_info[5],
                'state':customer_info[6],
                'nationality':customer_info[10],
                'birthday':customer_info[11]
            }
        else:
            customer_info = {
                'email': None,
                'name': None,
                'city': None,
                'state': None,
                'nationality': None,
                'birthday': None
            }
        if request.args.get('customer_email'):
            customer_email = request.args.get('customer_email')
        else:
            customer_email = customer_info['email']

        result = mysqltool.staff_query(user=mysqltool_user,
                                       table='flight NATURAL JOIN ticket NATURAL JOIN purchases NATURAL JOIN '
                                             'airline_staff',
                                       attribute=['customer_email', 'username'],
                                       value=[customer_email, mysqltool_user[:-2]])
        result = [[i[0]] + list(i[2:10]) for i in result]
        return customer_info, result

    elif action == 'report':
        start, end = retrieve_get_args_for_staff_date_report(request)
        str_start = str(start)
        str_end = str(end)
        stmt = 'SELECT * FROM flight NATURAL JOIN ticket NATURAL JOIN purchases NATURAL JOIN airline_staff ' \
               'WHERE purchase_date BETWEEN %s AND %s AND username=%s'
        result = mysqltool.staff_query(user=mysqltool_user, table=None,
                                       usestmt=True, s=stmt, v=[str_start, str_end, mysqltool_user[:-2]])
        date = [i[12] for i in result]
        bar_dict = {}
        cursor = start
        while cursor <= end:
            key = str(cursor.year) + '-' + str(cursor.month)
            bar_dict[key] = 0
            if cursor.month != 12:
                cursor = datetime.date(year=cursor.year, month=cursor.month + 1, day=1)
            else:
                cursor = datetime.date(year=cursor.year + 1, month=1, day=1)
        for i in date:
            key = str(i.year) + '-' + str(i.month)
            bar_dict[key] += 1
        bar_dict = [[i[0],i[1]] for i in bar_dict.items()]
        return len(date), bar_dict

    elif action == 'revenue':
        last_month = str(datetime.date.today() - datetime.timedelta(days=90))
        last_year = str(datetime.date.today() - datetime.timedelta(days=365))
        airline_name = mysqltool.root_get_staff_airline(user='root', staff=user)
        stmt = 'WITH count_null_month AS (SELECT SUM(price) AS cnm FROM flight NATURAL JOIN ticket NATURAL JOIN purchases ' \
               'WHERE booking_agent_id IS NULL AND purchase_date > %s AND airline_name = %s), ' \
               'count_null_year AS (SELECT SUM(price) AS cny FROM flight NATURAL JOIN ticket NATURAL JOIN purchases ' \
               'WHERE booking_agent_id IS NULL AND purchase_date > %s AND airline_name = %s), ' \
               'count_not_null_month AS (SELECT SUM(price) AS cnnm FROM flight NATURAL JOIN ticket NATURAL JOIN purchases ' \
               'WHERE booking_agent_id IS NOT NULL AND purchase_date > %s AND airline_name = %s), ' \
               'count_not_null_year AS (SELECT SUM(price) AS cnny FROM flight NATURAL JOIN ticket NATURAL JOIN purchases ' \
               'WHERE booking_agent_id IS NOT NULL AND purchase_date > %s AND airline_name = %s) ' \
               'SELECT cnm, cny, cnnm, cnny ' \
               'FROM count_null_month, count_null_year, count_not_null_month, count_not_null_year'
        result = mysqltool.staff_query(user=mysqltool_user, table=None,
                                       usestmt=True, s=stmt, v=[last_month, airline_name,
                                                                last_year, airline_name,
                                                                last_month, airline_name,
                                                                last_year, airline_name])
        result = list(result[0])
        return result
    elif action == 'destinations':
        stmt = 'SELECT airport_city, COUNT(airport_city) AS cac ' \
               'FROM flight NATURAL JOIN ticket NATURAL JOIN purchases ' \
               'INNER JOIN airport ON (arrival_airport = airport.airport_name) ' \
               'WHERE purchase_date > %s GROUP BY airport_city ORDER BY cac DESC LIMIT 3'
        three_month_before = datetime.date.today() - datetime.timedelta(days=90)
        one_year_before = datetime.date.today() - datetime.timedelta(days=365)
        month_result = mysqltool.staff_query(user=mysqltool_user, table=None,
                                             usestmt=True, s=stmt, v=[str(three_month_before)])
        month_result = [i[0] for i in month_result]
        year_result = mysqltool.staff_query(user=mysqltool_user, table=None,
                                            usestmt=True, s=stmt, v=[str(one_year_before)])
        year_result = [i[0] for i in year_result]
        return month_result, year_result
    else:
        return None


# return all airports in specific city
def airport_city_to_airport_name_list(mysqltool, mysqltool_user, airport_city, airport_name):
    if mysqltool_user is None:
        query_func = mysqltool.guest_query
    elif mysqltool_user[-1] == 'A':
        query_func = mysqltool.staff_query
    elif mysqltool_user[-1] == 'B':
        query_func = mysqltool.agent_query
    elif mysqltool_user[-1] == 'C':
        query_func = mysqltool.customer_query
    else:
        query_func = mysqltool.guest_query
    if airport_name:
        if airport_city:
            check = query_func(user=mysqltool_user, able='airport',
                               attribute=['airport_name', 'airport_city'],
                               value=[airport_name, airport_city])
            if len(check) != 1:
                return False
        else:
            return airport_name
    if airport_city:
        airports = mysqltool.root_sql_query(user='root', stmt='SELECT * FROM airport WHERE airport_city LIKE %s',
                                            value=[airport_city+ '%'])
        if len(airports) > 0:
            return [airport[0] for airport in airports]
        else:
            return False
    return None


# return all airlines and cities
def get_all_airlines_and_cities(mysqltool):
    result = mysqltool.root_sql_query(user='root', stmt=mysqltool.STMT_GET_ALL_AIRLINNS_AND_CITIES)
    airlines = list(set([i[0] for i in result]))
    d_cities = list(set([i[1] for i in result]))
    a_cities = list(set([i[2] for i in result]))
    result = dict(airlines=airlines, departure_cities=d_cities, arrival_cities=a_cities)
    return result


# get recommendations for booking agents and customers
# staff can't call this func
@validate_user(role='BC')
def get_recommendations(mysqltool, user, how_many):
    all_flights = mysqltool.root_sql_query(user='root', stmt=mysqltool.STMT_GET_ALL_FLIGHTS)
    stmt = 'SELECT airline_name, departure_airport, arrival_airport, departure_time, price, purchase_date ' \
           'FROM (purchases INNER JOIN ticket USING (ticket_id)) INNER JOIN flight USING (airline_name, flight_num) ' \
           'WHERE {t} = %s'
    if user[-1] == 'C':
        c_stmt = stmt.format(t='customer_email')
        all_user_flights = mysqltool.root_sql_query(user='root', stmt=c_stmt, value=[user[:-2]])
    else:
        b1_stmt = 'SELECT booking_agent_id FROM booking_agent WHERE email = %s'
        agent_id = mysqltool.root_sql_query(user='root', stmt=b1_stmt, value=[user[:-2]])[0][0]
        b2_stmt = stmt.format(t='booking_agent_id')
        all_user_flights = mysqltool.root_sql_query(user='root', stmt=b2_stmt, value=[agent_id])
    if len(all_user_flights) == 0:
        return get_popular_flights(mysqltool)
    recommended_flights = []
    p = recommendations_params
    weights = np.zeros(shape=(4, 1), dtype=float)
    weights[0, 0], weights[1, 0], weights[2, 0], weights[3, 0] = 0.1, 0.5, 0.25, 0.25
    raw = np.zeros(shape=(len(all_flights), 4), dtype=float)

    # four dimensions: airline, airports, departure time and price
    # airline
    all_user_airlines = [i[0] for i in all_user_flights]
    l1s, l2s = [], []
    for i in range(len(all_flights)):
        if all_flights[i][0] not in all_user_airlines:
            l2s.append(0)
            l1s.append(0)
        else:
            count = 0
            for j in all_user_flights:
                if j[0] == all_flights[i][0]:
                    count += 1
            l2s.append(count / len(all_user_flights))
            now = datetime.datetime.now()
            min_seconds = np.inf
            seconds = 0
            for j in all_user_flights:
                if j[0] == all_flights[i][0]:
                    seconds = 86400 * (now.day - j[5].day)
                    if seconds < min_seconds:
                        min_seconds = seconds
            l1s.append(np.exp(p['airline'] * seconds))
    l1s, l2s = normalized(l1s), normalized(l2s)
    raw[:, 0] = normalized([i[0] * i[1] for i in zip(l1s, l2s)])

    # airports and cities
    user_airport_dict = {}
    for i in all_user_flights:
        if (i[1], i[2]) in user_airport_dict.keys():
            user_airport_dict[(i[1], i[2])] += 1
        else:
            user_airport_dict[(i[1], i[2])] = 1
    length = len(all_user_flights)
    user_airport_dict = {item[0]: item[1] / length for item in user_airport_dict.items()}
    user_city_dict = {}
    result = mysqltool.root_sql_query(user='root', stmt='SELECT airport_name, airport_city FROM airport')
    airport_city_dict = {i[0]: i[1] for i in result}
    for item in user_airport_dict.items():
        d_airport, a_airport = item[0][0], item[0][1]
        d_city = airport_city_dict[d_airport]
        a_city = airport_city_dict[a_airport]
        if (d_city, a_city) not in user_city_dict.keys():
            user_city_dict[(d_city, a_city)] = 1
        else:
            user_city_dict[(d_city, a_city)] += 1
    user_city_dict = {item[0]: item[1] / length for item in user_city_dict.items()}
    ls = []
    for i in all_flights:
        airports = [i[2], i[4]]
        d_city = airport_city_dict[airports[0]]
        a_city = airport_city_dict[airports[1]]
        cities = [d_city, a_city]
        score = match_airport_and_city(airports, cities, user_airport_dict, user_city_dict)
        ls.append(score)

    raw[:, 1] = normalized(ls)

    # departure time
    departure_time_avg = 0
    for i in all_user_flights:
        departure_time_avg += 3600 * i[3].hour + 60 * i[3].minute + i[3].second
    departure_time_avg /= len(all_user_flights)
    ls = []
    for i in all_flights:
        time = 3600 * i[3].hour + 60 * i[3].minute + i[3].second
        ls.append((departure_time_avg - time) ** 2)
    raw[:, 2] = normalized(ls, mode='penal_large')

    # price
    print(all_user_flights)
    price_avg = sum([i[4] for i in all_user_flights]) / len(all_user_flights)
    ls = []
    for i in all_flights:
        ls.append((price_avg - i[6]) ** 2)
    raw[:, 3] = normalized(ls, mode='penal_large')

    score_list = raw.dot(weights)[:, 0].tolist()
    for i in range(how_many):
        max_index = score_list.index(max(score_list))
        recommended_flights.append(all_flights[max_index])
        del score_list[max_index]
        del all_flights[max_index]
    return recommended_flights


# called by get_recommendations()
def match_airport_and_city(airports, cities, user_p_airport_dict, user_p_city_dict):
    score = 0
    w_c = recommendations_params['city_weight']
    w_a = recommendations_params['airport_weight']
    reverse_penal = 0.7
    if (airports[0], airports[1]) in user_p_airport_dict.keys():
        score += w_a * user_p_airport_dict[(airports[0], airports[1])]
    elif (airports[1], airports[0]) in user_p_airport_dict.keys():
        score += w_a * user_p_airport_dict[(airports[1], airports[0])] * reverse_penal
    if (cities[0], cities[1]) in user_p_city_dict.keys():
        score += w_c * user_p_city_dict[(cities[0], cities[1])]
    elif (cities[1], cities[0]) in user_p_city_dict.keys():
        score += w_c * user_p_city_dict[(cities[1], cities[0])] * reverse_penal
    return score


# called by get_recommendations()
def normalized(lst, mode='penal_small'):
    lst_min = min(lst)
    lst_max = max(lst)
    if lst_min == lst_max:
        return [1] * len(lst)
    new_lst = []
    if mode == 'penal_small':
        for i in lst:
            new_lst.append((i - lst_min) / (lst_max - lst_min))
    if mode == 'penal_large':
        for i in lst:
            new_lst.append((lst_max - i) / (lst_max - lst_min))
    return new_lst


# get popular flights for guests
# flight that sold out will not be returned
def get_popular_flights(mysqltool, how_many=10):
    stmt = 'SELECT airline_name, flight_num, COUNT(*) FROM purchases NATURAL JOIN ticket ' \
           'GROUP BY flight_num, airline_name'
    result_popularity = mysqltool.root_sql_query(stmt=stmt, user='root')
    result_popularity_dict = {(i[0], i[1]): i[2] for i in result_popularity}
    result_popularity_dict = sorted(result_popularity_dict.items(), key=lambda x: x[1], reverse=True)
    result_popularity_dict = {i[0]: i[1] for i in result_popularity_dict}
    stmt = 'SELECT airline_name, flight_num, COUNT(*) FROM ticket GROUP BY flight_num, airline_name'
    result_tot_ticket = mysqltool.root_sql_query(stmt=stmt, user='root')
    result_tot_ticket_dict = {(i[0], i[1]): i[2] for i in result_tot_ticket}
    rec_flight_num = []
    count = 0
    for item in result_popularity_dict.items():
        if item[1] < result_tot_ticket_dict[item[0]]:
            rec_flight_num.append(item[0])
            count += 1
        if count >= how_many:
            break
    if len(rec_flight_num) == 0:
        stmt = 'SELECT * FROM flight LIMIT {t}'.format(t=how_many)
        result = mysqltool.root_sql_query(stmt=stmt, user='root')
        return result
    rec_flight_num = str(rec_flight_num)
    rec_flight_num = rec_flight_num[1:-1]
    rec_flight_num = '(' + rec_flight_num + ')'
    stmt = 'SELECT * FROM flight WHERE (airline_name, flight_num) IN ' + str(rec_flight_num)
    result = mysqltool.root_sql_query(stmt=stmt, user='root')
    return result


# add an additional attribute to flight
# to indicate whether the flight is sold out or not
def flight_list_add_check_ticket_exists(mysqltool, flight_list):
    stmt = 'WITH purchases_join_ticket AS (SELECT * FROM purchases NATURAL JOIN ticket), ' \
           'count_purchased_ticket AS (SELECT airline_name, flight_num, COUNT(ticket_id) as ct ' \
           'FROM purchases_join_ticket GROUP BY airline_name, flight_num), ' \
           'count_total_ticket AS (SELECT airline_name, flight_num, COUNT(ticket_id) as ct ' \
           'FROM ticket GROUP BY airline_name, flight_num) ' \
           'SELECT p.airline_name, p.flight_num FROM count_purchased_ticket AS p, count_total_ticket as t ' \
           'WHERE p.airline_name = t.airline_name AND p.flight_num = t.flight_num ' \
           'AND p.ct = t.ct'
    flight_no_ticket = mysqltool.root_sql_query(user='root', stmt=stmt)
    new_list = []
    for i in flight_list:
        if (i[0], i[1]) in flight_no_ticket:
            new_list.append(list(i) + [0])
        else:
            new_list.append(list(i) + [1])
    return new_list


# convert flight list to json
def flight_list_to_json_list(flight_list):
    json_list = []
    if flight_list is None or len(flight_list) == 0:
        return []
    for flight in flight_list:
        json_dict = dict()
        json_dict["airline_name"] = flight[0]
        json_dict["flight_num"] = flight[1]
        json_dict["departure_airport"] = flight[2]
        json_dict["departure_date"] = str(flight[3].year) + "-" + str(flight[3].month) + "-" + str(flight[3].day)
        json_dict["departure_time"] = '{:0>2d}'.format(flight[3].hour) + ":" + '{:0>2d}'.format(flight[3].minute)
        json_dict["arrival_airport"] = flight[4]
        json_dict["arrival_date"] = str(flight[5].year) + "-" + str(flight[5].month) + "-" + str(flight[5].day)
        json_dict["arrival_time"] = '{:0>2d}'.format(flight[5].hour) + ":" + '{:0>2d}'.format(flight[5].minute)
        json_dict["price"] = str(flight[6])
        json_dict["status"] = flight[7]
        json_dict["airplane_id"] = str(flight[8])
        try:
            json_dict["ticket"] = str(flight[9])
        except Exception as e:
            pass
        json_list.append(json_dict)
    return json_list


def sort_dictionary(dictionary, limit):
    sorted_items = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_items) >= limit:
        sorted_items = sorted_items[:limit]
    new_dict = {i[0]: i[1] for i in sorted_items}
    return new_dict


if __name__ == '__main__':
    print(datetime.date.today())
