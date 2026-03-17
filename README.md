# Tescord

Tescord - это Discord-подобное приложение для небольших сообществ на `FastAPI`, `Angular` и `PostgreSQL`.

## Что уже есть

- `backend/` - API, авторизация, модели БД, миграции, development seed
- `frontend/` - Angular-клиент
- `infra/` - инфраструктурные файлы, включая `compose.yml` для PostgreSQL

## Что нужно для запуска

- `Python 3.12+`
- `Node.js 20+` и `npm`
- `PostgreSQL`

## Быстрый запуск

Ниже самый простой сценарий для локального запуска на Windows.

### 1. Подготовить PostgreSQL

Убедись, что сервер PostgreSQL запущен и доступен на `localhost:5432`.

Проверка:

```powershell
pg_isready
```

Если базы `tescord` еще нет, создай ее:

```powershell
$env:PGPASSWORD='ВАШ_ПАРОЛЬ'
psql -h localhost -U postgres -d postgres -w -c "CREATE DATABASE tescord;"
```

### 2. Настроить backend

Перейди в папку `backend`:

```powershell
cd backend
```

Создай виртуальное окружение:

```powershell
python -m venv .venv
```

Активируй его:

```powershell
.venv\Scripts\activate
```

Установи зависимости:

```powershell
python -m pip install -e .[dev]
```

Создай локальный `.env`:

```powershell
Copy-Item .env.example .env
```

Открой `backend/.env` и укажи свою строку подключения к PostgreSQL.

Пример:

```env
TESCORD_DATABASE_URL=postgresql+psycopg://postgres:ВАШ_ПАРОЛЬ@localhost:5432/tescord
TESCORD_SECRET_KEY=tescord-local-dev-secret
TESCORD_SEED_DEMO_DATA=true
```

### 3. Применить миграции

Из папки `backend` выполни:

```powershell
alembic upgrade head
```

### 4. Запустить backend

Из папки `backend`:

```powershell
uvicorn app.main:app --reload
```

После запуска backend будет доступен здесь:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health-check: `http://127.0.0.1:8000/api/health`

### 5. Запустить frontend

Открой второй терминал и перейди в папку `frontend`:

```powershell
cd frontend
```

Установи зависимости:

```powershell
npm install
```

Запусти dev-сервер:

```powershell
npm start
```

Frontend будет доступен здесь:

- `http://localhost:4200`

## Полный порядок запуска

Если кратко, то рабочий порядок такой:

1. Запустить PostgreSQL
2. Перейти в `backend`
3. Активировать `.venv`
4. Выполнить `alembic upgrade head`
5. Выполнить `uvicorn app.main:app --reload`
6. Перейти в `frontend`
7. Выполнить `npm start`
8. Открыть `http://localhost:4200`

## Development seed

В development-режиме backend автоматически создает демо-пользователя, сервер и каналы, если их еще нет.

Демо-данные:

- Email: `demo@tescord.local`
- Password: `tescord-demo`
- Server: `Forgehold Collective`

Сейчас Angular-клиент использует этот демо-аккаунт автоматически при старте.

## Полезные команды

### Backend

```powershell
cd backend
.venv\Scripts\activate
pytest
alembic upgrade head
```

### Frontend

```powershell
cd frontend
npm run build
```

## Запуск PostgreSQL через Docker

Если захочешь запускать PostgreSQL через Docker, можно использовать:

```powershell
docker compose -f infra/compose.yml up -d postgres
```

Но в текущей локальной настройке можно спокойно работать и с установленным локально PostgreSQL.
