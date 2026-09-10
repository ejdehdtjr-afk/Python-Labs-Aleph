# _7_board_test 문서

`security_events` 테이블을 중심으로 한 문서 모음입니다.

| 문서 | 무엇이 들어 있나 | 언제 보나 |
|---|---|---|
| [001_security_events_테이블_생성.md](001_security_events_테이블_생성.md) | 표가 **어디서 어떻게** 만들어지는지 — import 체인, 실제 DDL, `create_all()` 규칙 | 구조를 이해하고 싶을 때 |
| [002_코드_복붙용.md](002_코드_복붙용.md) | **주석을 뺀 순수 코드** — 파일명 + 코드블록만 | 그대로 복사해 만들 때 |
| [003_코드_주석_설명.md](003_코드_주석_설명.md) | **주석 포함 원본 + 줄별 해설** — 왜 그렇게 썼는지, 함정, 에러 표 | 코드가 이해 안 될 때 |

## 세 줄 요약

1. `models/security_event.py` 의 `SecurityEvent` 클래스가 표의 **설계도**다 (`__tablename__ = 'security_events'`).
2. 그 클래스가 **import 되어야** `db.metadata` 에 등록된다 — `models/__init__.py` 가 그 통로다.
3. `app.py` 의 `create_app()` 안 `db.create_all()` 이 **실제로 CREATE TABLE** 을 실행한다.

## 빠른 실행

```powershell
cd E:\0-Aleph-Python-Test\Python-Lab-ALeph-T
.\.venv\Scripts\Activate.ps1
cd _7_board_test
python app.py
```

## 빠른 확인

```sql
USE my_new_board_db;
SHOW TABLES;
DESC security_events;
```

## 주의

- `.env` 는 **깃에 올리지 않습니다** (`.gitignore` 등록됨). 공유용으로는 키 이름만 적힌 예시를 쓰세요.
- 문서에는 **실제 키 값을 절대 적지 않습니다.**
