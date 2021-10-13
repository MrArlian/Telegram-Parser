from configobj import ConfigObj
from typing import Union, List

import psycopg2

cfg = ConfigObj('static/config.cfg')

DATABASE_URL = cfg.get('DATABASE_URL')

connect = psycopg2.connect(DATABASE_URL)
commit = connect.commit
db = connect.cursor()


def add(table: str, data: dict, conflict: str = None) -> None:
    assert table and data, 'Table name and data cannot be empty!'

    var_key, var_value = [], []
    sql = ''

    for key, value in data.items():
        var_key.append(key)

        if isinstance(value, str):
            value = value.replace("'", '')
            var_value.append(f"'{value}'")
        else:
            var_value.append(f"{value}")

    if conflict:
        sql = 'ON CONFLICT (%s) DO NOTHING' % conflict


    db.execute(
        'INSERT INTO %s (%s) VALUES (%s) %s' % (table, ', '.join(var_key), ', '.join(var_value), sql)
    )

    commit()


def update(table: str, data: dict, condition: dict = None):
    assert table and data, 'Table name and data cannot be empty!'

    obj, sql = [], ''
    elements = []

    for key, value in data.items():
        if isinstance(value, str):
            value = value.replace("'", '')
            obj.append(f"{key}='{value}'")
        else:
            obj.append(f"{key}={value}")


    if condition:

        for key, value in  condition.items():
            if isinstance(value, str):
                value = value.replace("'", '')
                elements.append(f"{key}='{value}'")
            else:
                elements.append(f"{key}={value}")

        sql += 'WHERE ' + ' AND '.join(elements)


    db.execute(
        "UPDATE %s SET %s %s" % (table, ', '.join(obj), sql)
    )

    commit()


def get(
    table: str, 
    objects: Union[str, List[str]], 
    condition: dict = None, 
    compressing: bool = True
    ) -> list:

    assert table and objects, 'Table name and lookup objects cannot be empty!'

    obj = ', '.join(objects) if isinstance(objects, list) else objects
    elements = []
    objs = []
    sql = ''


    if condition:
        for key, value in condition.items():

            if isinstance(value, str):
                value = value.replace("'", '')
                objs.append(f"{key}='{value}'")
            else:
                objs.append(f"{key}={value}")

        sql += 'WHERE ' + ' AND '.join(objs)


    db.execute(
        'SELECT %s FROM %s %s' % (obj, table, sql)
    )


    response = db.fetchall()

    if not compressing:
        return response

    #Сбор полученных данных
    for objs in response:
        for obj in objs:
            elements.append(obj)

    return elements


#Удалить что-то с базы данных
def delete(table: str, condition: dict = None) -> None:

    sql, objs = '', []

    if condition:
        for key, value in condition.items():

            if isinstance(value, str):
                value = value.replace("'", '')
                objs.append(f"{key}='{value}'")
            else:
                objs.append(f"{key}={value}")

        sql += 'WHERE ' + ' AND '.join(objs)


    db.execute(
        "DELETE FROM %s %s" % (table, sql)
    )

    commit()