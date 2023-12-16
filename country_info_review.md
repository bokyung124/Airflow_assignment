## UndefinedColumn 오류

```log
[2023-12-15, 13:49:49 UTC] {logging_mixin.py:137} INFO - INSERT INTO leebk1124.country_info (country, population, area) VALUES ("Hong Kong Special Administrative Region of the People's Republic of China", 7500700, 1104.0);
[2023-12-15, 13:49:49 UTC] {logging_mixin.py:137} INFO - column "hong kong special administrative region of the people's republic of china" does not exist in country_info
[2023-12-15, 13:49:49 UTC] {taskinstance.py:1768} ERROR - Task failed with exception
Traceback (most recent call last):
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/decorators/base.py", line 217, in execute
    return_value = super().execute(context)
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/operators/python.py", line 175, in execute
    return_value = self.execute_callable()
  File "/home/airflow/.local/lib/python3.7/site-packages/airflow/operators/python.py", line 192, in execute_callable
    return self.python_callable(*self.op_args, **self.op_kwargs)
  File "/opt/airflow/dags/Country_Info.py", line 50, in load
    cur.execute(sql)
psycopg2.errors.UndefinedColumn: column "hong kong special administrative region of the people's republic of china" does not exist in country_info
```

- INSERT문에서 VALUES에 넣었던 값이 컬럼으로 인식되는 오류가 있었음
- 값들 중에 작은 따옴표`'`가 포함된 값들이 있어서 문자열을 큰 따옴표`"`로 감쌌는데, Postgresql에서는 문자열을 작은 따옴표로만 감싸는 것이었다!
    - Oracle SQL도 이렇다고 한다.
- 문자열 내에서 작은 따옴표를 넣으려면 작은 따옴표를 두 번 넣어주면 된다.
- PostgreSQL에서 큰 따옴표는 테이블 이름이나 컬럼명의 대소문자를 구분해주어야 할 때 사용한다.
    - "UserName" != "username"

## 방법1: `'` -> `''`

- extract_transform 함수에서 country를 읽어올 때 replace 함수를 사용하여 작은 따옴표 한 개를 두 개로 바꾸어주는 방법

```python
@task
def extract_transform():
    r = requests.get('https://restcountries.com/v3/all')
    rj = r.json()
    records = []

    for d in rj:
        country = d['name']['official']
        country = country.replace("'", "''")
        population = d['population']
        area = d['area']
        records.append([country, population, area])
    
    return records

@task
def load(schema, table, records):
    logging.info("load started")
    cur = get_Redshift_connection()
    try:
        cur.execute("BEGIN;")
        create_table(cur, schema, table)
        
        for r in records:
            sql = f"INSERT INTO {schema}.{table} VALUES ('{r[0]}', {r[1]}, {r[2]});"
            print(sql)
            cur.execute(sql)
        cur.execute("COMMIT;")
    except Exception as error:
        print(error)
        cur.execute("ROLLBACK;")
        raise
    logging.info("load done")
```

## 방법 2: 문자열 포맷팅

```python
@task
def extract_transform():
    r = requests.get('https://restcountries.com/v3/all')
    rj = r.json()
    records = []

    for d in rj:
        country = d['name']['official']
        population = d['population']
        area = d['area']
        records.append([country, population, area])
    
    return records

@task
def load(schema, table, records):
    logging.info("load started")
    cur = get_Redshift_connection()
    try:
        cur.execute("BEGIN;")
        create_table(cur, schema, table)
        
        for r in records:
            sql = f'INSERT INTO {schema}.{table} VALUES (%s, %s::bigint, %s);'
            print(sql, (r[0], r[1], r[2]))
            cur.execute(sql, (r[0], r[1], r[2]))
        cur.execute("COMMIT;")
    except Exception as error:
        print(error)
        cur.execute("ROLLBACK;")
        raise
    logging.info("load done")
```

### 플레이스홀더 오류

- Airflow의 psycopg2 모듈에서는 `%s`만 사용할 수 있다!
    - 숫자 컬럼에 `%d`, `%f`를 사용하면 오류가 발생함
- SQL 인젝션 공격 방지를 위해서도 이 방법이 좋음