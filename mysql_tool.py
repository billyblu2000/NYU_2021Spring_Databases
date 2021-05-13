"""
MySQLTool class to deal with DB
"""

import random
import threading
import time

from config import *

import mysql.connector

from utils import validate_user, log


class MySQLTool:
    """A class deals all the things related to MYSQL"""

    # stored SQL queries and constants
    STMT_GET_ALL_AIRLINES = 'SELECT airline_name FROM airline'
    STMT_GET_ALL_AIRPORTS = 'SELECT airport_name FROM airport'
    STMT_GET_ALL_AIRPLANES_GIVEN_STAFF = 'SELECT airplane_id, seats FROM airplane NATURAL JOIN airline_staff ' \
                                         'WHERE username = %s'
    STMT_GET_ALL_AIRPLANES_FOR_AIRLINE = 'SELECT airplane_id, seats FROM airplane ' \
                                         'NATURAL JOIN airline NATURAL JOIN airline_staff WHERE username = %s'
    STMT_GET_ALL_FLIGHTS = 'SELECT * FROM flight'
    STMT_GET_ALL_AIRLINNS_AND_CITIES = 'SELECT airline_name, s.airport_city, t.airport_city ' \
                                       'FROM (flight INNER JOIN airport s ' \
                                       'ON flight.departure_airport = s.airport_name) ' \
                                       'INNER JOIN airport t ON flight.arrival_airport = t.airport_name'
    A = 'airline_staff'
    B = 'booking_agent'
    C = 'customer'

    # ###############
    # general methods
    # ###############

    def __init__(self):

        self._conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME
        )
        refresh_thread = threading.Thread(target=self.__refresh_connection)
        refresh_thread.start()

    def get_connection(self):
        return self._conn

    # ####################################
    # methods designed for different users
    # ####################################

    # method name like: 'def role_action(self, user, [,])';
    # user like 'username:role' or 'root';
    # role in ['A':airline_stuff, 'B':booking_agent, 'C':customer, 'root':admin];
    # '@validate_user(role=role)' will let the method to validate user before executing;
    # if user is not authorized (username not in role OR role do not exist OR role not match validation),
    # method will return None.

    # guest can only do query on flight table
    def guest_query(self, table, attribute=None, value=None):
        if table not in ['flight', 'airport', 'airport']:
            return None
        log("Guest searched on {t}".format(t=table))
        return self.__query_with_table_and_where(table=table, attribute=attribute, value=value)

    @validate_user(role='A')
    def staff_insert(self, user, table, value=None, create_ticket=True, ticket_number=None,
                     airline_name=None, flight_num=None):
        if table == 'flight' or table == 'ticket' or create_ticket is True:
            flight_stmt, ticket_stmt, ticket_values = '', '', []
            if table == 'flight':
                flight_stmt += self.__staff_insert_flight(value)
            if table == 'ticket' or create_ticket == True:
                airplane_id = None
                if value is not None:
                    if airplane_id is None:
                        airline_name = value[0]
                    if flight_num is None:
                        flight_num = value[1]
                    if ticket_number is None:
                        airplane_id = value[-1]
                else:
                    if airplane_id is None or flight_num is None or ticket_number is None:
                        return False
                ticket_stmt, ticket_values = self.__staff_insert_ticket(ticket_number, airline_name, flight_num,
                                                                        airplane_id)
            if flight_stmt == '' and ticket_stmt == '':
                return False
            try:
                if flight_stmt != '':
                    print("f:",flight_stmt, value)
                    cursor = self._conn.cursor(prepared=True)
                    cursor.execute(flight_stmt, value)
                if ticket_stmt != '':
                    print("t:", table, ticket_values)
                    cursor = self._conn.cursor(prepared=True)
                    cursor.execute(ticket_stmt, ticket_values)
            except Exception as e:
                print(e)
                self._conn.rollback()
                return False
        if table == 'airport':
            stmt = 'INSERT INTO airport VALUE (%s,%s)'
            cursor = self._conn.cursor(prepared=True)
            print(stmt,value)
            try:
                cursor.execute(stmt, value)
            except:
                self._conn.rollback()
                return False
        if table == 'airplane':
            stmt = 'INSERT INTO airplane VALUE (%s,%s,%s)'
            cursor = self._conn.cursor(prepared=True)
            try:
                cursor.execute(stmt,value)
            except:
                self._conn.rollback()
                return False
        self._conn.commit()
        log("Staff {u} inserted to {t}".format(u=user[:-2], t=table))
        return True

    @staticmethod
    def __staff_insert_flight(value):
        sub_stmt = '('
        for i in range(len(value)):
            sub_stmt += '%s,'
        sub_stmt = sub_stmt.rstrip(',')
        sub_stmt += ');'
        stmt = 'INSERT INTO flight VALUE ' + sub_stmt
        return stmt

    def __staff_insert_ticket(self, ticket_number, airline_name, flight_num, airplane_id):
        if ticket_number is None:
            if airplane_id is None:
                return ''
            seats = self.root_sql_query(user='root', stmt='SELECT seats FROM airplane where airplane_id=%s',
                                        value=[airplane_id])[0][0]
            # only for test!
            seats //= 10
        else:
            seats = ticket_number

        # get ticket ids
        existing_ticket_id = self.root_sql_query(user='root', stmt='SELECT ticket_id FROM ticket')
        existing_ticket_id = [i[0] for i in existing_ticket_id]

        # create tickets with random ids
        if seats <= 0:
            return '', []
        sub_stmt = 'INSERT INTO ticket VALUES '
        values = []
        for i in range(seats):
            id = max(existing_ticket_id) + 1
            existing_ticket_id.append(id)
            sub_stmt += '(%s,%s,%s),'
            values += [id, airline_name, flight_num]
        sub_stmt = sub_stmt.rstrip(',')
        sub_stmt += ';'
        return sub_stmt, values

    @validate_user(role='A')
    def staff_update(self, user, table, pk, attribute, value):
        if table not in ['flight']:
            return None
        stmt = 'UPDATE flight SET '+ self.__create_stmt_attr_value(attribute, value) + ' ' \
               + 'WHERE airline_name = %s AND flight_num = %s'
        cursor = self._conn.cursor(prepared=True)
        try:
            cursor.execute(stmt, value + pk)
        except Exception as e:
            self._conn.rollback()
            return False
        self._conn.commit()
        log("Staff {u} updated {t}".format(u=user[:-2], t=table))
        return True

    @validate_user(role='A')
    def staff_del(self, user, table, attribute, value):
        if table not in ['flight']:
            return None

        stmt = 'DELETE FROM flight WHERE ' + self.__create_stmt_attr_value(attribute=attribute, value=value)
        cursor = self._conn.cursor(prepared=True)
        try:
            cursor.execute(stmt, value)
        except:
            self._conn.rollback()
            return False
        log("Staff {u} deleted from {t}".format(u=user[:-2], t=table))
        self._conn.commit()
        return True

    @validate_user(role='A')
    def staff_query(self, user, table, attribute=None, value=None, usestmt=False, s=None, v=None):
        if usestmt:
            return self.root_sql_query(user='root', stmt=s, value=v)
        if table not in ['flight NATURAL JOIN airline_staff', 'flight', 'airport',
                         'flight NATURAL JOIN ticket NATURAL JOIN purchases NATURAL JOIN booking_agent',
                         'flight NATURAL JOIN ticket NATURAL JOIN purchases NATURAL JOIN airline_staff',
                         'flight NATURAL JOIN ticket NATURAL JOIN purchases',
                         'flight NATURAL JOIN ticket NATURAL JOIN purchases '
                         'INNER JOIN airport ON (arrival_airport = airport.airport_name)']:
            return None
        log("Staff {u} searched on {t}".format(u=user[:-2], t=table))
        return self.__query_with_table_and_where(table=table, attribute=attribute, value=value)

    # customer can only do query on flight table and purchase table
    @validate_user(role='C')
    def customer_query(self, user, table, attribute, value):
        if table not in ['flight', 'flight NATURAL JOIN ticket NATURAL JOIN purchases', 'airport']:
            return None
        log("Customer {u} searched on {t}".format(u=user[:-2], t=table))
        return self.__query_with_table_and_where(table=table, attribute=attribute, value=value)

    @validate_user(role='C')
    def customer_insert(self, user, table, value):
        if table == 'purchases':
            cursor = self._conn.cursor(prepared=True)
            if value[2] is None:
                stmt = 'INSERT INTO purchases VALUE (%s,%s, NULL, %s)'
                try:
                    cursor.execute(stmt, value[:2] + [value[3]])
                except Exception as e:
                    print(e)
                    self._conn.rollback()
                    return False
            else:
                return False
            log("Customer {u} inserted to {t}".format(u=user[:-2], t=table))
            self._conn.commit()
            return True
        else:
            return False

    @validate_user(role='C')
    def customer_del(self, user, table, attribute, value):
        log("Customer {u} deleted from {t}".format(u=user[:-2], t=table))
        pass

    # agent can only do query on flight table and purchase table
    @validate_user(role='B')
    def agent_query(self, user, table, attribute, value):
        if table not in ['flight', 'purchase', 'airport', 'flight NATURAL JOIN ticket NATURAL JOIN purchases']:
            return None
        log("Agent {u} searched on {t}".format(u=user[:-2], t=table))
        return self.__query_with_table_and_where(table=table, attribute=attribute, value=value)

    @validate_user(role='B')
    def agent_insert(self, user, table, value):
        if table == 'purchases':
            cursor = self._conn.cursor(prepared=True)
            if value[2] is None:
                return False
            else:
                stmt = 'INSERT INTO purchases VALUE (%s,%s,%s,%s)'
                try:
                    cursor.execute(stmt, value)
                except Exception as e:
                    self._conn.rollback()
                    return False
            self._conn.commit()
            log("Agent {u} inserted to {t}".format(u=user[:-2], t=table))
            return True
        else:
            return False

    @validate_user(role='root')
    def root_insert(self, user, table, value):
        cursor = self._conn.cursor(prepared=True)
        filled_values = []
        sub_stmt = ''
        if type(value) is not list:
            filled_values.append(value)
            sub_stmt = '(%s)'
        elif type(value) is list and type(value[0]) is not list:
            filled_values = value
            sub_stmt = '%s,' * len(value)
            sub_stmt = sub_stmt.rstrip(',')
            sub_stmt = '(' + sub_stmt + ')'
        else:
            for i in value:
                filled_values += i
        stmt = 'INSERT INTO {t} VALUES '.format(t=table) + sub_stmt
        try:
            cursor.execute(stmt, filled_values)
        except Exception as e:
            self._conn.rollback()
            return False
        self._conn.commit()
        return True

    @validate_user(role='root')
    def root_sql_query(self, user, stmt, value=None):
        if not value:
            cursor = self._conn.cursor()
            cursor.execute(stmt)
            result = cursor.fetchall()
            result = [list(result[i]) for i in range(len(result))]
            for i in range(len(result)):
                if result[i] is not None:
                    for j in range(len(result[i])):
                        if type(result[i][j]) is bytearray:
                            result[i][j] = result[i][j].decode('utf-8')
            return result
        else:
            cursor = self._conn.cursor(prepared=True)
            cursor.execute(stmt, value)
            result = cursor.fetchall()
            result = [list(result[i]) for i in range(len(result))]
            for i in range(len(result)):
                if result[i] is not None:
                    for j in range(len(result[i])):
                        if type(result[i][j]) is bytearray:
                            result[i][j] = result[i][j].decode('utf-8')
            #print(result)
            return result

    @validate_user(role='root')
    def root_sql_alter(self, user, stmt):
        try:
            cursor = self._conn.cursor()
            cursor.execute(stmt)
        except Exception as e:
            self._conn.rollback()
            print(e)
            return False
        self._conn.commit()
        return True

    @validate_user(role='root')
    def root_check_duplicates(self, user, table, attribute, value):
        cursor = self._conn.cursor(prepared=True)
        stmt = 'SELECT * FROM {t} WHERE {a} = %s'.format(t=table, a=attribute)
        cursor.execute(stmt, [value])
        if len(cursor.fetchall()) > 0:
            return True
        else:
            return False

    @validate_user(role='root')
    def root_check_exists(self, user, table, attribute, value):
        cursor = self._conn.cursor(prepared=True)
        sub_stmt = self.__create_stmt_attr_value(attribute, value)
        stmt = 'SELECT * FROM ' + table + ' WHERE' + sub_stmt
        if type(value) is not list:
            value = [value]
        cursor.execute(stmt, value)
        return len(cursor.fetchall())

    @validate_user(role='root')
    def root_get_new_agent_id(self, user):
        cursor = self._conn.cursor()
        cursor.execute('SELECT MAX(booking_agent_id) FROM booking_agent')
        result = cursor.fetchone()[0]
        return result + 1 if result is not None else 1

    def root_get_agent_id_from_email(self, user, email):
        cursor = self._conn.cursor(prepared=True)
        cursor.execute('SELECT booking_agent_id FROM booking_agent WHERE email=%s', [email])
        result = cursor.fetchone()[0]
        return result

    @validate_user(role='root')
    def root_new_user_gen_id(self, user):
        cursor = self._conn.cursor()
        cursor.execute('SELECT MAX(uid) FROM `user`')
        new_id = cursor.fetchone()[0] + 1
        cursor = self._conn.cursor()
        try:
            cursor.execute('INSERT INTO `user` VALUE ({r})'.format(r=str(new_id)))
        except Exception as e:
            self._conn.rollback()
            return None
        self._conn.commit()
        return new_id

    @validate_user(role='root')
    def root_get_uid(self, user, role, pk):
        cursor = self._conn.cursor(prepared=True)
        stmt = ''
        if role == "A":
            stmt = 'SELECT uid FROM airline_staff WHERE username = %s'
        if role == "B":
            stmt = 'SELECT uid FROM booking_agent WHERE email = %s'
        if role == "C":
            stmt = 'SELECT uid FROM customer WHERE email = %s'
        cursor.execute(stmt, [pk])
        return cursor.fetchall()

    def root_get_staff_airline(self, user, staff):
        cursor = self._conn.cursor(prepared=True)
        result = self.root_sql_query(user=user, stmt='SELECT airline_name FROM airline_staff WHERE username=%s',
                                     value=[staff])[0][0]
        return result

    def root_get_ticket_id(self, user, airline_name, flight_num):
        stmt = 'SELECT t.ticket_id FROM ticket AS t ' \
               'WHERE t.airline_name=%s AND t.flight_num=%s AND t.ticket_id NOT IN ' \
               '(SELECT ticket_id FROM purchases)'
        result = self.root_sql_query(user=user, stmt=stmt, value=[airline_name, flight_num])
        print(result)
        if len(result) == 0:
            return False
        else:
            ticket_id = result[0][0]
            return ticket_id

    # ############
    # util methods
    # ############

    # util method to do query, filling in table and values
    def __query_with_table_and_where(self, table, attribute, value):
        cursor = self._conn.cursor(prepared=True)
        if type(attribute) is list:
            assert len(attribute) == len(value)
            new_attribute, new_value = [], []
            for i in range(len(attribute)):
                if value[i] is not None:
                    new_attribute.append(attribute[i])
                    new_value.append(value[i])
            attribute, value = new_attribute, new_value
        if attribute is not None:
            if 'departure_time' in attribute:
                index = attribute.index('departure_time')
                departure_time = value[index]
                if departure_time is not None:
                    departure_time_start, departure_time_end = departure_time + " 00:00:00", departure_time + " 23:59:59"
                    value = value[:index] + [[departure_time_start, departure_time_end]] + value[index+1:]
            if 'arrival_time' in attribute:
                index = attribute.index('arrival_time')
                arrival_time = value[index]
                if arrival_time is not None:
                    arrival_time_start, arrival_time_end = arrival_time + " 00:00:00", arrival_time + " 23:59:59"
                    value = value[:index] + [[arrival_time_start, arrival_time_end]] + value[index + 1:]
        sub_stmt = self.__create_stmt_attr_value(attribute=attribute, value=value)
        if sub_stmt != '':
            stmt = 'SELECT * FROM ' + table + ' WHERE' + sub_stmt
        else:
            stmt = 'SELECT * FROM ' + table
            cursor.execute(stmt)
            return cursor.fetchall()
        filled_in_values = []
        if type(value) is list:
            for i in value:
                if type(i) is not list:
                    filled_in_values.append(i)
                else:
                    filled_in_values += i
        else:
            filled_in_values = [value]
        print(stmt, filled_in_values)
        cursor.execute(stmt, filled_in_values)
        result = cursor.fetchall()
        result = [list(result[i]) for i in range(len(result))]
        for i in range(len(result)):
                if result[i] is not None:
                    for j in range(len(result[i])):
                        if type(result[i][j]) is bytearray:
                            result[i][j] = result[i][j].decode('utf-8')

        return result

    # util method to build sub_stmt, filling in attributes and values
    @staticmethod
    def __create_stmt_attr_value(attribute, value):
        if attribute is None and value is None:
            return ''
        if type(attribute) is not list:
            attribute, value = [attribute], [value]
        sub_stmt = ''
        for i in range(len(attribute)):
            if attribute[i] == 'departure_time' or attribute[i] == 'arrival_time':
                sub_stmt += 'AND ' + attribute[i] + ' BETWEEN %s AND %s '
            elif type(value[i]) is list:
                temp = '('
                for j in range(len(value[i])):
                    temp += '%s, '
                temp = temp.rstrip(', ')
                temp = temp + ') '
                sub_stmt += 'AND ' + attribute[i] + ' in ' + temp
            else:
                sub_stmt += 'AND ' + attribute[i] + ' = %s '
        sub_stmt = sub_stmt.lstrip('AND')
        return sub_stmt

    @staticmethod
    def pretty(lst):
        str_ = ''
        if lst is None:
            return str_
        for i in lst:
            str_ += str(i) + '<br/>'
        return str_

    def __refresh_connection(self, thread=True):
        if thread:
            while True:
                time.sleep(100)
                try:
                    cursor = self._conn.cursor()
                    cursor.close()
                    log('APP DB connection check: OK')
                except Exception as e:
                    self._conn.close()
                    time.sleep(1)
                    self._conn = mysql.connector.connect(
                        host=DB_HOST,
                        user=DB_USER,
                        password=DB_PASS,
                        db=DB_NAME,
                    )
                    log('APP DB connection check: REFRESHED')
        else:
            self._conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASS,
                db=DB_NAME,
            )

    def refresh(self):
        self.__refresh_connection(thread=False)
