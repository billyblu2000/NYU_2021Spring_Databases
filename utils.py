import numpy as np

recommendations_params = {
    'airline': 0,
    'city_weight': 0,
    'airport_weight': 0,
    'city_middle': 0,
    'airport_middle': 0,
    'time': 0,
    'price': 0
}


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


def get_recommendations(mysqltool, user, how_many=10):
    all_flights = mysqltool.guest_query(table='flight')
    all_user_purchases = []
    all_user_flights = mysqltool.customer_query(table='purchase')
    recommended_flights = []
    p = recommendations_params
    weights = np.zeros(shape=(4, 1), dtype=float)
    weights[1, 0], weights[2, 0], weights[3, 0], weights[4, 0] = 0.1, 0.5, 0.25, 0.25
    raw = np.zeros(shape=(len(all_flights), 4), dtype=float)

    # four dimensions: airline, airports, departure time and price
    # airline
    all_user_airlines = [i[0] for i in all_user_flights]
    for i in range(len(all_flights)):
        if all_flights[i][0] not in all_user_airlines:
            raw[i,0] = 0
        else:
            count = 0
            for j in all_user_flights:
                if j[0] == all_flights[i][0]:
                    count += 1
            l2 = count/len(all_user_flights)
            latest = 0
            for j in all_user_purchases:
                pass

    # airports and cities
    for i in range(len(all_flights)):
        pass

    # departure time
    for i in range(len(all_flights)):
        pass

    # price
    for i in range(len(all_flights)):
        pass

    for i in range(4):
        raw[:i] = normalized(raw[:, i])
    score_list = raw.dot(weights)[:, 0].tolist()
    for i in range(how_many):
        max_index = score_list.index(max(score_list))
        recommended_flights.append(all_flights[max_index])
        del score_list[max_index]
        del all_flights[max_index]
    return recommended_flights


def normalized(lst):
    lst_min = min(lst)
    lst_max = max(lst)
    new_lst = []
    for i in lst:
        new_lst.append((i - lst_min) / (lst_max - lst_min))
    return new_lst