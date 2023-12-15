## airflow.cfg

- docker 앱에서 webserver/opt/airflow 에서 파일 열 수 있음
- airflow 동작, 설정 옵션 수정 

<br>

## 1) DAGs 폴더는 어디에 지정되는가?

```conf
# The folder where your airflow pipelines live, most likely a
# subfolder in a code repository. This path must be absolute.
dags_folder = /opt/airflow/dags
```

- `opt/airflow/dags` 폴더에 DAG들이 저장됨
- 보통 코드 리포지토리의 하위 폴더


## 2) DAGs 폴더에 새로운 DAG를 만들면 언제 실제로 Airflow 시스템에서 이를 알게 되나? 이 스캔 주기를 결정해주는 키의 이름이 무엇인가?

- 새로운 DAG를 만들면 기본적으로 **5분** 후에 시스템에서 알게 됨
- 스캔 주기를 결정해주는 키는 `dag_dir_list_interval` !

```conf
# How often (in seconds) to scan the DAGs directory for new files. Default to 5 minutes.
dag_dir_list_interval = 300
```


## 3) 이 파일에서 Airflow를 API 형태로 외부에서 조작하고 싶다면 어느 섹션을 변경해야 하는가?

<img width="1032" alt="스크린샷 2023-12-14 오후 5 15 49" src="https://github.com/bokyung124/AWS_Exercise/assets/53086873/4a58b143-344f-4bc3-9f15-f5446e395901">

- 파일 내에 [api] 섹션이 있음 !
- Airflow를 API 형태로 외부에서 조작할 수 있게 하는 키는 `auth_backends`
    - 기본 값은 `airflow.api.auth.backend.session` : API로 조작할 수 없음
    - `airflow.api.auth.backend.basic_auth`로 변경하면 API 형태로 외부에서 조작 가능
        - ID/PW로 인증하는 형태

```conf
# Comma separated list of auth backends to authenticate users of the API. See
# https://airflow.apache.org/docs/apache-airflow/stable/security/api.html for possible values.
# ("airflow.api.auth.backend.default" allows all requests for historic reasons)
auth_backends = airflow.api.auth.backend.session
```

<br>

- `access_control_allow_headers` : 브라우저에게 허용되는 HTTP 헤더를 알려주는 키
- `access_control_allow_methods` : 요청 가능한 HTTP Request 종류를 알려주는 키 (GET, POST 등)
- `access_control_allow_origins` : 요청을 보낼 수 있는 도메인 주소


## 4) Variable에서 변수의 값이 Encrypted가 되려면 변수의 이름에 어떤 단어들이 들어가야 하는데 이 단어들은 무엇일까?

- Encrypted: 암호화
- 변수 이름에 `secret`, `password`, `passwd`, `authorization`, `api_key`, `apikey`, `access_token` 키워드가 들어가면 됨!


## 5) 이 환경 설정 파일이 수정되었다면 이를 실제로 반영하기 위해서 해야 하는 일은?

- Docker -> 컨테이너 재실행 (down -> up)

- airflow 웹 서버, 스케줄러 재실행

```bash
sudo systemctl restart airflow-webserver
sudo systemctl restart airflow-scheduler
```

<br>

- `airflow db init`은 백엔드나 Metadata DB가 바뀐 것과 같이 큰 변경이 생긴 경우에만 사용


## 6) Metadata DB의 내용을 암호화하는데 사용되는 키는 무엇인가?

- `fernet_key` 를 사용하여 Metadata DB 내용을 암호화할 수 있음
- 암호화 및 복호하에 사용되는 대칭키

```conf
# Secret key to save connection passwords in the db
fernet_key = 
```