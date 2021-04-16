import datetime
import random

random.seed(0)


class Airline:

    def __init__(self, airline_name, country):
        self.airline_name = airline_name
        self._country = country

    def __str__(self):
        str_ = "("
        str_ += "'" + self.airline_name + "'" + ")"
        return str_


class Airport:

    def __init__(self, airport_name, airport_city, country):
        self.airport_name = airport_name
        self.airport_city = airport_city
        self._country = country

    def __str__(self):
        str_ = "("
        str_ += "'" + self.airport_name + "'" + ","
        str_ += "'" + self.airport_city + "'" + ")"
        return str_


class Airplane:

    def __init__(self, airplane_id, airline, seats):
        self.airplane_id = airplane_id
        self.airline = airline
        self.seats = seats

    def __str__(self):
        str_ = "("
        str_ += "'" + self.airline.airline_name + "'" + ","
        str_ += str(self.airplane_id) + ","
        str_ += str(self.seats) + ")"
        return str_



class Flight:

    def __init__(self, airline, flight_num, departure_airport, departure_time, arrival_airport, arrival_time, price,
                 status, airplane):
        self.airline = airline
        self.flight_num = flight_num
        self.departure_airport = departure_airport
        self.departure_time = departure_time
        self.arrival_airport = arrival_airport
        self.arrival_time = arrival_time
        self.price = price
        self.status = status
        self.airplane = airplane

    def __str__(self):
        str_ = "("
        str_ += "'" + self.airline.airline_name + "'" + ","
        str_ += str(self.flight_num) + ","
        str_ += "'" + self.departure_airport.airport_name + "'" + ","
        str_ += "'" + str(self.departure_time) + "'" + ","
        str_ += "'" + self.arrival_airport.airport_name + "'" + ","
        str_ += "'" + str(self.arrival_time) + "'" + ","
        str_ += str(self.price) + ","
        str_ += "'" + self.status + "'" + ","
        str_ += str(self.airplane.airplane_id) + ")"
        return str_


class Ticket:

    def __init__(self, ticket_id, airline, flight):
        self.ticket_id = ticket_id
        self.airline = airline
        self.flight = flight


def domestic(d, a):
    if d._country == a._country:
        return True
    else:
        return False


def choose_airline(d, a, airlines):
    d_country = d._country
    a_country = a._country
    waiting = []
    if d_country == 'China' and a_country == 'China':
        waiting = airlines[:6]
    elif d_country != 'China' and a_country != 'China':
        if d_country == 'America' or a_country == 'America':
            waiting.append(airlines[6])
        if d_country == 'Canada' or a_country == 'Canada':
            waiting.append(airlines[7])
        if d_country == 'France' or a_country == 'France':
            waiting.append(airlines[8])
        if d_country == 'Japan' or a_country == 'Japan':
            waiting.append(airlines[9])
    else:
        waiting = airlines[:3]
        if d_country == 'America' or a_country == 'America':
            waiting.append(airlines[6])
        if d_country == 'Canada' or a_country == 'Canada':
            waiting.append(airlines[7])
        if d_country == 'France' or a_country == 'France':
            waiting.append(airlines[8])
        if d_country == 'Japan' or a_country == 'Japan':
            waiting.append(airlines[9])
    choice = random.choice(waiting)
    return choice


def choose_airplane(airline, airplanes):
    airplanes_checked = []
    for airplane in airplanes:
        if airplane.airline == airline:
            airplanes_checked.append(airplane)
    return random.choice(airplanes_checked)


def make_flights(airports, airlines, airplanes, num):
    flights = []
    start_time = datetime.datetime(year=2021, month=6, day=1)
    flight_nums = random.sample([i for i in range(1000000, 9999999)], num)
    for i in range(num):
        my_airports = random.choices(airports, k=2)
        if my_airports[0].airport_city == my_airports[1].airport_city:
            continue
        departure_airport = my_airports[0]
        arrival_airport = my_airports[1]
        airline = choose_airline(departure_airport, arrival_airport, airlines)
        if domestic(departure_airport, arrival_airport):
            price = random.randint(400, 3000)
            time_last = random.randint(120 * 60, 360 * 60)
        else:
            price = random.randint(3000, 10000)
            time_last = random.randint(240 * 60, 720 * 60)
        status = random.choices(['upcoming', 'delayed', 'canceled'], weights=[1, 0.05, 0.01])[0]
        flight_num = flight_nums[i]
        if random.choices([1, 0], weights=[0.01, 1])[0]:
            start_time += datetime.timedelta(days=1)
        real_start_time = start_time + datetime.timedelta(seconds=random.randint(420 * 60, 1200 * 60))
        real_end_time = real_start_time + datetime.timedelta(seconds=time_last)
        airplane = choose_airplane(airline=airline, airplanes=airplanes)
        flight = Flight(airline=airline, flight_num=flight_num, departure_airport=departure_airport,
                        departure_time=real_start_time, arrival_airport=arrival_airport,
                        arrival_time=real_end_time, price=price, status=status, airplane=airplane)
        flights.append(flight)
    return flights

def create_sql_insert(lst, table):
    sql = 'INSERT INTO {t} VALUES '.format(t=table)
    for i in lst:
        sql += str(i) + ','
    sql = sql.rstrip(',')
    sql += ';'
    return sql


if __name__ == '__main__':
    sql = ''
    airline_names_n = ['China Southern', 'Air China', 'China Eastern', 'Sichuan Airlines', 'Xiamen Airlines',
                       'Hainan Airlines']
    airline_names_i = ['America Airlines', 'Air Canada', 'Air France', 'Japan Airlines']
    airline_country_i = ['America', 'Canada', 'France', 'Japan']
    airport_data = [
        ('PVG', 'Shanghai', 'China'),
        ('SHA', 'Shanghai', 'China'),
        ('PEK', 'Beijing', 'China'),
        ('PKX', 'Beijing', 'China'),
        ('SJW', 'Shijiazhuang', 'China'),
        ('CTU', 'Chengdu', 'China'),
        ('CAN', 'Guangzhou', 'China'),
        ('HGH', 'Hangzhou', 'China'),
        ('ZQZ', 'Zhangjiakou', 'China'),
        ('CGQ', 'Changchun', 'China'),
        ('CKG', 'Chongqing', 'China'),
        ('HRB', 'Harbin', 'China'),
        ('KMG', 'Kunming', 'China'),
        ('LHW', 'Lanzhou', 'China'),
        ('KHN', 'Nanchang', 'China'),
        ('SHE', 'Shenyang', 'China'),
        ('TSN', 'Tianjin', 'China'),
        ('SZX', 'Shenzhen', 'China'),
        ('XMN', 'Xiamen', 'China'),
        ('NKG', 'Nanjing', 'China'),
        ('SYX', 'Sanya', 'China'),
        ('WUH', 'Wuhan', 'China'),
        ('CGO', 'Zhengzhou', 'China'),
        ('HFE', 'Hefei', 'China'),
        ('JFK', 'New York', 'America'),
        ('ORD', 'Chicago', 'America'),
        ('ATL', 'Atlanta', 'America'),
        ('LAX', 'Los Angeles', 'America'),
        ('SFO', 'San Francisco', 'America'),
        ('YQB', 'Quebec', 'Canada'),
        ('YYZ', 'Toronto', 'Canada'),
        ('YVR', 'Vancouver', 'Canada'),
        ('YYJ', 'Victoria', 'Canada'),
        ('CDG', 'Paris', 'France'),
        ('ORY', 'Paris', 'France'),
        ('LYS', 'Lyon', 'France'),
        ('MRS', 'Marseille', 'France'),
        ('HND', 'Tokyo', 'Japan'),
        ('NRT', 'Narita', 'Japan'),
        ('NGO', 'Tokoname', 'Japan'),
        ('ITM', 'Osaka', 'Japan'),
        ('KIX', 'Kansai', 'Japan')
    ]

    airlines = []
    for i in airline_names_n:
        airlines.append(Airline(i, country='China'))
    for i in range(len(airline_names_i)):
        airlines.append(Airline(airline_names_i[i], country=airline_country_i[i]))
    airports = []
    for i in airport_data:
        airports.append(Airport(airport_name=i[0], airport_city=i[1], country=i[2]))
    airplanes = []
    for i in range(len(airlines)):
        apn = random.randint(10, 30)
        ids = random.sample([i for i in range(1000000, 9999999)], apn)
        for j in range(apn):
            id = ids[j]
            seats = random.randrange(100, 500, 10)
            airplanes.append(Airplane(airplane_id=id, airline=airlines[i], seats=seats))
    flights = make_flights(airports=airports, airlines=airlines, airplanes=airplanes, num=1000)
    print(create_sql_insert(lst=airlines,table='airline'))
    print(create_sql_insert(airports,table='airport'))
    print(create_sql_insert(airplanes, table='airplane'))
    print(create_sql_insert(flights, table='flight'))
