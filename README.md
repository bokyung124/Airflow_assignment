# Airflow assignment

## 1) airflow.cfg

- airflow의 설정을 관리하는 airflow.cfg 파일에 대한 질의응답

## 2) CountryInfo.py

**세계 나라 정보 API 사용 DAG 작성**

- <https://restcountries.com/>
    - 별도의 API Key 필요 없음
- 엔드포인트 : https://restcountries.com/v3/all
- JSON 형식의 데이터를 받을 수 있음

<br>

- Full Refresh로 구현해서 매번 국가 정보를 읽어오게 할 것
- API 결과에서 아래 3개 정보를 추출하여 Redshift에 각자 스키마 밑에 테이블 생성
    - country -> ['name']['official']
    - population -> ['population]
    - area -> ['area']
- UTC로 매주 토요일 오전 6시 30분에 실행되게 만들어볼 것

- **country_info_review** : 에러 기록
