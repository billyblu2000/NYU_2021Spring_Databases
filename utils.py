import json
from functools import wraps
import datetime
import numpy as np

recommendations_params = {
    'airline': -0.000001,
    'city_weight': 0.6,
    'airport_weight': 0.4,
}

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


# decorator to validate user before method executed
def validate_user(role="ABC"):
    def decorator(func):

        @wraps(func)
        def decorated(*args, **kwargs):
            user = kwargs['user']
            if user == 'root':
                return func(*args, **kwargs)

            key, identity = user[:-2], user[-1]
            cursor = args[0].get_connection().cursor(prepared=True)

            if identity not in role:
                print("Unauthorized user")
                return None

            if identity == 'A':
                stmt = 'SELECT username FROM airline_staff WHERE username = %s'
            elif identity == 'B':
                stmt = 'SELECT email FROM booking_agent WHERE email = %s'
            elif identity == 'C':
                stmt = 'SELECT email FROM customer WHERE email = %s'
            else:
                raise Exception("Can't understand user when validation")

            cursor.execute(stmt, [key])
            result = cursor.fetchall()

            if len(result) == 1:
                return func(*args, **kwargs)
            else:
                print("Unknown user, database query and alteration stopped!")
                return None

        return decorated

    return decorator


def retrieve_get_args_for_flight_query(request):
    departure_city = request.args.get('departure_city')
    departure_airport = request.args.get('departure_airport')
    arrival_city = request.args.get('arrival_city')
    arrival_airport = request.args.get('arrival_airport')
    departure_time = request.args.get('departure_time')
    arrival_time = request.args.get('arrival_time')
    airline = request.args.get('airline_name')
    flight_num = None
    if airline is not None:
        flight_num = request.args.get('flight_num')
        if flight_num is not None:
            flight_num = int(flight_num)
    price = request.args.get('price')
    if price:
        price = (float(price.split("|")[0]), float(price.split("|")[1]))
    status = request.args.get('status')
    airplane_id = request.args.get('airplane_id')
    return (airline, flight_num, departure_airport, departure_city, departure_time,
            arrival_airport, arrival_city, arrival_time, price, status, airplane_id)


def airport_city_to_airport_name_list(mysqltool, mysqltool_user, airport_city, airport_name):
    if mysqltool_user == 'A':
        query_func = mysqltool.staff_query
    elif mysqltool_user == 'B':
        query_func = mysqltool.agent_query
    elif mysqltool_user == 'C':
        query_func = mysqltool.customer_query
    else:
        query_func = mysqltool.guest_query
    if airport_name:
        if airport_city:
            check = query_func(table='airport', attribute=['airport_name', 'airport_city'],
                               value=[airport_name, airport_city])
            if len(check) != 1:
                return False
        else:
            return airport_name
    if airport_city:
        airports = query_func(table='airport', attribute='airport_city', value=airport_city)
        if len(airports) > 0:
            return [airport[0] for airport in airports]
        else:
            return False
    return None


@validate_user(role='BC')
def get_recommendations(mysqltool, user, how_many):
    all_flights = mysqltool.guest_query(table='flight')
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
    rec_flight_num = str(rec_flight_num)
    rec_flight_num = rec_flight_num[1:-1]
    rec_flight_num = '(' + rec_flight_num + ')'
    stmt = 'SELECT * FROM flight WHERE (airline_name, flight_num) IN ' + str(rec_flight_num)
    result = mysqltool.root_sql_query(stmt=stmt, user='root')
    return result


def flight_list_to_json_list(flight_list):
    json_list = []
    for flight in flight_list:
        json_dict = dict()
        json_dict['airline_name'] = flight[0]
        json_dict['flight_num'] = flight[1]
        json_dict['departure_airport'] = flight[2]
        json_dict['departure_year'] = flight[3].year
        json_dict['departure_month'] = flight[3].month
        json_dict['departure_day'] = flight[3].day
        json_dict['departure_hour'] = flight[3].hour
        json_dict['departure_mintue'] = flight[3].minute
        json_dict['departure_second'] = flight[3].second
        json_dict['arrival_airport'] = flight[4]
        json_dict['arrival_year'] = flight[5].year
        json_dict['arrival_month'] = flight[5].month
        json_dict['arrival_day'] = flight[5].day
        json_dict['arrival_hour'] = flight[5].hour
        json_dict['arrival_mintue'] = flight[5].minute
        json_dict['arrival_second'] = flight[5].second
        json_dict['price'] = str(flight[6])
        json_dict['status'] = flight[7]
        json_dict['airplane_id'] = str(flight[8])
        json_list.append(json_dict)
    return json_list


if __name__ == '__main__':
    pass
