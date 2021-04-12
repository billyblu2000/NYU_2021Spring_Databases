from functools import wraps
from config import *

import mysql.connector


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


class MySQLTool:
    """A class deals all the things related to MYSQL"""

    # stored SQL queries
    STMT_GET_ALL_AIRLINES = 'SELECT airline_name FROM airline'

    # ###############
    # general methods
    # ###############

    def __init__(self):

        self._conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,

        )

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
    def guest_query(self, table, attribute, value):
        if table not in ['flight']:
            return None
        return self.__query_with_table_and_where(table=table, attribute=attribute, value=value)

    @validate_user(role='A')
    def stuff_insert(self, user, table, value):
        # TODO
        pass

    @validate_user(role='A')
    def stuff_update(self, user, table, value):
        # TODO
        pass

    @validate_user(role='A')
    def stuff_del(self, user, table, value):
        # TODO
        pass

    @validate_user(role='A')
    def stuff_query(self, user, table, value):
        # TODO
        pass

    # customer can only do query on flight table and purchase table
    @validate_user(role='C')
    def customer_query(self, user, table, attribute, value):
        if table not in ['flight', 'purchase']:
            return None
        return self.__query_with_table_and_where(table=table, attribute=attribute, value=value)

    # agent can only do query on flight table and purchase table
    @validate_user(role='B')
    def agent_query(self, user, table, attribute, value):
        if table not in ['flight', 'purchase']:
            return None
        return self.__query_with_table_and_where(table=table, attribute=attribute, value=value)

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
            # TODO
        stmt = 'INSERT INTO {t} VALUES '.format(t=table) + sub_stmt
        cursor.execute(stmt, filled_values)
        self._conn.commit()

    @validate_user(role='root')
    def root_sql_query(self, user, stmt):
        cursor = self._conn.cursor()
        cursor.execute(stmt)
        return cursor.fetchall()

    @validate_user(role='root')
    def root_sql_alter(self, user, stmt):
        cursor = self._conn.cursor()
        cursor.execute(stmt)
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
        cursor.execute(stmt, value)
        return len(cursor.fetchall())

    @validate_user(role='root')
    def root_get_new_agent_id(self, user):
        cursor = self._conn.cursor()
        cursor.execute('SELECT MAX(booking_agent_id) FROM booking_agent')
        result = cursor.fetchone()[0]
        return result + 1 if result is not None else 1

    # ############
    # util methods
    # ############

    # util method to do query, filling in table and values
    def __query_with_table_and_where(self, table, attribute, value):
        cursor = self._conn.cursor(prepared=True)
        sub_stmt = self.__create_stmt_attr_value(attribute=attribute, value=value)
        stmt = 'SELECT * FROM ' + table + ' WHERE' + sub_stmt
        cursor.execute(stmt, value)
        return cursor.fetchall()

    # util method to build sub_stmt, filling in attributes and values
    @staticmethod
    def __create_stmt_attr_value(attribute, value):
        if type(attribute) is not list:
            attribute, value = [attribute], [value]
        assert len(attribute) == len(value)
        sub_stmt = ''
        for i in range(len(attribute)):
            sub_stmt += 'AND ' + attribute[i] + ' = %s '
        sub_stmt = sub_stmt.lstrip('AND')
        return sub_stmt
