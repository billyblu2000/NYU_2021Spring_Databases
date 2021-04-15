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
