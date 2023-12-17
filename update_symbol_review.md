## UpdateSymbol DAG

- Yahoo Finance API (yfinancee)를 호출하여 애플 주식 정보를 수집하는 DAG
- 기본적으로 지난 한 달의 주식 가격을 반환

- 기존의 Incremental Update job에서 Primary Key Uniqueness를 유지할 수 있도록 수정

- `created_date` 컬럼을 만들어 primary key인 `date` 값이 같은 경우에 더 최근의 정보만 저장하도록!
    - sql의 `ROW_NUMBER()` 이용
    

```sql
DELETE FROM {schema}.{table};
INSERT INTO {schema}.{table}
SELECT date, "open", high, low, close, volume 
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY date ORDER BY created_date DESC) seq
    FROM t
)
WHERE seq = 1;
```

### GROUP BY와 PARTITION BY

- **GROUP BY**
    - 주로 집계 함수와 함께 사용되어 특정 열(들)에 대한 집계 수행
    - return: 그룹화된 열의 고유한 값에 대한 행만 포함
    - ex) 국가별 총 매출
        - '국가' 열을 기준으로 그룹화 -> 그 그룹의 '매출' 열 합산

- **PARTITION BY**
    - 윈도우 함수와 함께 사용
    - 전체 결과 세트를 특정 열(들)에 따라 여러 파티션으로 분할
    - 각 파티션은 독립적으로 계산되며, 원래 행의 순서 유지
    - return: 원래 결과 세트의 모든 행 포함
    - ex) 국가별 매출 순위
        - '국가' 열로 파티션 -> 각 파티션 내에서 '매출' 열에 대해 RANK() 함수 적용
        
- GROUP BY는 주로 전체 데이터셋을 그룹화하고 집계하려는 경우,
- PARTITION BY는 동일한 데이터셋 내에서 여러 윈도우 혹은 세그먼트를 만들고 각각에 대해 계산을 수행하려는 경우에 사용


### error

- 터미널에서 airflow에 접속해서 `pip3 install yfinance`를 실행해도 적용이 되지 않아 DAG가 뜨지 않았음
- docker-compose.yaml 파일에서 추가


```yaml
x-airflow-common:
  &airflow-common
  image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.5.1}
  # build: .
  environment:
    &airflow-common-env
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    # For backward compatibility, with Airflow <2.3
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'true'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth,airflow.api.auth.backend.session'
    _PIP_ADDITIONAL_REQUIREMENTS: ${_PIP_ADDITIONAL_REQUIREMENTS:- yfinance}
```

- `x-airflow-common` 의 `_PIP_ADDITIONAL_REQUIREMENTS`에 yfinance 추가!
    - `airflow-init`에도 `_PIP_ADDITIONAL_REQUIREMENTS`가 있는데, 여기에 추가하면 오류가 발생하며 컨테이너가 실행되지 않음