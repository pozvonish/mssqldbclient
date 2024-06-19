import pymssql


def connect_to_db(USER, PASSWORD) -> object:
    try:
        conn = pymssql.connect(
            server='PC',
            user=USER,
            password=PASSWORD,
            database='GPUSHOP',
            charset = 'UTF-8',
            as_dict=True
        )
    except:
        return None
    return conn


def get_table_datatypes(CONN, TABLENAME):
    cursor = CONN.cursor()
    cursor.execute(f"""SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{TABLENAME}'""")
    results = cursor.fetchall()
    datatypes = [result ['DATA_TYPE'] for result in results]
    print(datatypes)
    return datatypes


def get_db_objects(CONN) -> dict:
    cursor = CONN.cursor()
    cursor.execute(
        '''SELECT 
    dp1.name AS RoleName, 
    dp2.name AS UserName, 
    o.name AS ObjectName, 
    p.permission_name,
    CASE 
        WHEN o.type IS NULL THEN 'No Object/Not Applicable'
        ELSE o.type 
    END AS ObjectType
FROM sys.database_role_members AS drm
    INNER JOIN sys.database_principals AS dp1 ON drm.role_principal_id = dp1.principal_id
    INNER JOIN sys.database_principals AS dp2 ON drm.member_principal_id = dp2.principal_id
    INNER JOIN sys.database_permissions AS p ON dp1.principal_id = p.grantee_principal_id
    LEFT JOIN sys.objects AS o ON p.major_id = o.object_id
WHERE dp2.name = USER_NAME()'''
)
    results = cursor.fetchall()
    if not results:
        cursor.close()
        return 'NO RESULTS'
    results_keys = results[0].keys()
    keys = list(results_keys)
    return {'results': results, 'keys': keys}


def add_to_table(CONN, TABLENAME, VALUES):
    predicate = '('
    keys = VALUES.keys()
    datatypes = get_table_datatypes(CONN, TABLENAME)

    for key in keys:
        predicate+= f"{key}"
        if key != list(keys)[-1]:
            predicate += ', '

    predicate+= ') VALUES ('
    
    for key, datatype in zip(keys, datatypes):
        if 'int' in datatype:
            predicate+= f"{int(sanitize_string(VALUES[key]))}" 
        elif 'money' in datatype:
            predicate+= f"{float(sanitize_string(VALUES[key]))}"
        else: 
            predicate+= f"'{sanitize_string(VALUES[key])}'"

        if key != list(keys)[-1]:
            predicate += ', '
    predicate+= ')'

    cursor = CONN.cursor()
    print(f'{TABLENAME} | {predicate}')
    try:
        cursor.execute(f'''INSERT INTO {TABLENAME} {predicate}''')
        print(cursor.rowcount)
        CONN.commit()
        return 0
    except Exception as e:
        print(e)
        return e



def delete_from_table(CONN, TABLENAME, VALUES):
    predicate = ''
    keys = VALUES.keys()
    datatypes = get_table_datatypes(CONN, TABLENAME)

    for key, datatype in zip(keys, datatypes):
        if 'int' in datatype:
            predicate+= f"{key} = {int(sanitize_string(VALUES[key]))}" 
        elif 'money' in datatype:
            predicate+= f"{key} = {float(sanitize_string(VALUES[key]))}"
        elif 'date' in datatype or 'time' in datatype:
            continue
        else: 
            predicate+= f"{key} = '{sanitize_string(VALUES[key])}'"

        if key != list(keys)[-1]:
            predicate += ' AND '
    
    cursor = CONN.cursor()
    print(f"DELETE FROM {TABLENAME} WHERE {predicate}")
    try:
        cursor.execute(f"DELETE FROM {TABLENAME} WHERE {predicate}")
        CONN.commit()
        print(cursor.rowcount)
        return 0
    except Exception as e:
        print(e)
        return e


def update_value_in_table(CONN, TABLENAME, VALUES, current_key, new_value):
    predicate = ''
    keys = VALUES.keys()
    datatypes = get_table_datatypes(CONN, TABLENAME)

    for key, datatype in zip(keys, datatypes):
        if 'int' in datatype:
            predicate+= f"{key} = {int(sanitize_string(VALUES[key]))}" 
        elif 'money' in datatype:
            predicate+= f"{key} = {float(sanitize_string(VALUES[key]))}"
        elif 'date' in datatype or 'time' in datatype:
            continue
        else: 
            predicate+= f"{key} = '{sanitize_string(VALUES[key])}'"

        if key != list(keys)[-1]:
            predicate += ' AND '
    
    cursor = CONN.cursor()
    query = ''

    try:
        if 'int' in datatypes[list(keys).index(current_key)]:
            query = f"UPDATE {TABLENAME} SET {current_key} = {int(sanitize_string(new_value))} WHERE {predicate}"
        elif 'money' in datatypes[list(keys).index(current_key)]:
            query = f"UPDATE {TABLENAME} SET {current_key} = {float(sanitize_string(new_value))} WHERE {predicate}"
        else:
            query = f"UPDATE {TABLENAME} SET {current_key} = '{sanitize_string(new_value)}' WHERE {predicate}"
        print(query)
        cursor.execute(query)
        print(cursor.rowcount)
        CONN.commit()
        return 0
    except Exception as e:
        print(e)
        return e


def get_table(CONN, TABLENAME):
    cursor = CONN.cursor()
    cursor.execute(
        f'SELECT * FROM {TABLENAME}'
    )
    results = cursor.fetchall()
    if not results:
        cursor.close()
        return 'NO RESULTS'
    results_keys = results[0].keys()
    keys = list(results_keys)
    return {'results': results, 'keys': keys}


def get_table_func_params(CONN, FUNCNAME):
    cursor = CONN.cursor()
    query = f"""SELECT
    p.name AS Name, 
    t.name AS DataType
FROM 
    sys.objects o
JOIN 
    sys.parameters p ON o.object_id = p.object_id
JOIN 
    sys.types t ON p.system_type_id = t.system_type_id
WHERE 
    o.type IN ('IF', 'P')
    AND o.schema_id = SCHEMA_ID('dbo')
	AND t.name != 'sysname'
    AND o.name = '{FUNCNAME}'
ORDER BY 
    o.name, 
    p.parameter_id;
"""
    cursor.execute(query)

    results = cursor.fetchall()
    if not results:
        cursor.close()
        return 0

    return results


def exec_table_func(CONN, FUNCNAME, VALUES, DATATYPES):
    cursor = CONN.cursor()
    if 'P_' in FUNCNAME:
        query = f"EXEC {FUNCNAME} "
        if VALUES:
            for value, datatype in zip(VALUES, DATATYPES):
                if 'int' in datatype['DataType']:
                    query+= f"{datatype['Name']} = {int(sanitize_string(value))}"
                elif 'money' in datatype['DataType']:
                    query+= f"{datatype['Name']} = {float(sanitize_string(value))}"
                elif 'date' in datatype['DataType'] or 'time' in datatype:
                    continue
                else: 
                    query+= f"{datatype['Name']} = '{sanitize_string(value)}'"

                if value != VALUES[-1]:
                    query+= ', '
    else:
        query = f"SELECT * FROM {FUNCNAME}("
        if VALUES:
            for value, datatype in zip(VALUES, DATATYPES):
                if 'int' in datatype['DataType']:
                    query+= f"{int(sanitize_string(value))}"
                elif 'money' in datatype['DataType']:
                    query+= f"{float(sanitize_string(value))}"
                elif 'date' in datatype['DataType'] or 'time' in datatype:
                    continue
                else: 
                    query+= f"'{sanitize_string(value)}'"

                if value != VALUES[-1]:
                    query+= ', '
        query+= ')'
    
    print(query)

    try:
        cursor.execute(query)
        # CONN.commit()
        results = cursor.fetchall()
        if results == []:
            return 'NO RESULTS'
        else:
            print(cursor.rowcount)
            results_keys = results[0].keys()
            keys = list(results_keys)
            return {'results': results, 'keys': keys}
    except Exception as e:
        print(e)
        return 0


def db_transcact_isol_lvl(CONN):
    cursor = CONN.cursor()
    query = """SELECT CASE transaction_isolation_level 
       WHEN 0 THEN 'Unspecified'
       WHEN 1 THEN 'ReadUncommitted'
       WHEN 2 THEN 'ReadCommitted'
       WHEN 3 THEN 'RepeatableRead'
       WHEN 4 THEN 'Serializable'
       WHEN 5 THEN 'Snapshot'
       ELSE 'Unknown'
       END AS TX_Isolation_Level
FROM sys.dm_exec_sessions
WHERE session_id = @@SPID;"""
    cursor.execute(query)
    results = cursor.fetchall()
    print(results)


def get_user_roles(CONN):
    cursor = CONN.cursor()
    query = """SELECT 
    dp.name AS DatabaseRoleName
FROM 
    sys.database_role_members drm
JOIN 
    sys.database_principals dp ON drm.role_principal_id = dp.principal_id
JOIN 
    sys.database_principals dp2 ON drm.member_principal_id = dp2.principal_id
WHERE 
    dp2.name = USER_NAME();"""
    print(query)

    cursor.execute(query)
    results = cursor.fetchall()
    roles = []

    if results:
        for result in results:
            roles.append(result['DatabaseRoleName'])
        return roles
    else:
        return 0
    

def query_to_db(CONN, QUERY) -> dict:
    cursor = CONN.cursor()
    try:
        cursor.execute(QUERY)
        print(QUERY)
    except Exception as e:
        return e
    try:
        results = cursor.fetchall()
        if results == []:
            return 'NO RESULTS'
        elif type(results) == list:
            results_keys = results[0].keys()
            keys = list(results_keys)
            return {'results': results, 'keys': keys}
        else:
            return results
    except:
        CONN.commit()
        return 0
    

def sanitize_string(input_string):
    if type(input_string) != str:
        return input_string
    else:
        sanitized = input_string.replace("'", "''")
        sanitized = sanitized.replace(";", "")
        sanitized = sanitized.replace("--", "")
        sanitized = sanitized.replace("/*", "")
        sanitized = sanitized.replace("*/", "")
        sanitized = sanitized.replace("@@", "")
        sanitized = sanitized.replace("@", "")
        return sanitized