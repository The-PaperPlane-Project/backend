# Paper Plane Airport Backend

Backend доведен до рабочего состояния под ТЗ: FastAPI, SQLAlchemy, Pydantic, Poetry, структура `src/repositories`, `src/services`, `src/routes`, `src/models`, `src/schemas`.

## Запуск

```bash
poetry config virtualenvs.create false
poetry install
poetry run uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger: http://127.0.0.1:8000/docs

## Главная интеграция с frontend

Так как текущий frontend хранит данные в `localStorage`, для вашей идеи обмена всей БД одним файлом добавлены endpoints:

```http
GET  /api/database
PUT  /api/database
POST /api/database/sync-to-sql
```

`GET /api/database` возвращает один JSON-объект, совместимый со структурами frontend: `planes`, `cities`, `flights`, `passengers`, `tickets`, `users`.

`PUT /api/database` принимает такой же JSON-объект и сохраняет его в `data/airport_data.json`. Перед заменой создается backup в `data/backups/`.

`POST /api/database/sync-to-sql` заполняет пустые SQL-таблицы из JSON-файла.

## Авторизация

```http
POST /auth/register
POST /auth/login
POST /auth/login-json
```

Тестовый администратор:

```text
email: admin@paperplane.ru
password: admin
```

Пароли сохраняются md5-хешем, как было указано в ТЗ.

## Основные REST endpoints

```http
GET  /flights/
GET  /flights/{flight_id}
GET  /flights/{flight_id}/seats
GET  /airplanes/
GET  /cities/
POST /tickets/
GET  /tickets/user/{user_id}
GET  /passengers/user/{user_id}
POST /passengers/
```

Защищенные админские endpoints используют Bearer Token после логина администратора.

## Важно про frontend

Frontend в загруженном виде не делает HTTP-запросы к backend: он использует `src/data/storage.ts` и `localStorage`. Backend уже готов к обмену одним JSON-файлом, но для полной онлайн-синхронизации нужно будет подключить frontend к `GET/PUT /api/database` или добавить небольшую API-backed реализацию `airportDataSource`.


## Требования к паролю

Для регистрации пароль должен содержать от 8 до 24 символов. Это совпадает с проверкой на стороне текущего frontend.
