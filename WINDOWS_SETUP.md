# Установка и запуск на судовом ПК (Windows)

## 1. Установить Python

Скачать и установить Python 3.10+ с https://www.python.org/downloads/windows/
При установке обязательно поставить галочку **"Add python.exe to PATH"**.

Проверить в PowerShell:
```powershell
python --version
```

## 2. Установить Git (если ещё не установлен)

https://git-scm.com/download/win

## 3. Получить код

Если репозиторий уже создан на GitHub:
```powershell
git clone https://github.com/<ваш-аккаунт>/dualog-mail-agent.git
cd dualog-mail-agent
```

Для последующих обновлений (когда код изменится на Mac и будет запушен):
```powershell
git pull
```

## 4. Установить зависимости

```powershell
pip install -r requirements.txt
```

## 5. Настроить конфигурацию

```powershell
copy .env.example .env
notepad .env
```

Заполнить (см. подробности в `README.md`):
- `DUALOG_IMAP_HOST/PORT/USER/PASSWORD` — из Thunderbird (Настройки учётной записи → Сервер входящей почты)
- `GMAIL_SMTP_USER` и `GMAIL_SMTP_APP_PASSWORD` — Gmail App Password
- `GMAIL_FORWARD_TO`

Отредактировать `rules.yaml` под критерии важности при необходимости.

## 6. Тестовый запуск

```powershell
python main.py
```

Смотрите вывод в консоли и файл `logs\agent.log`. Остановка — `Ctrl+C`.

## 7. Автозапуск при старте Windows (Планировщик заданий)

1. Открыть **Планировщик заданий** (Task Scheduler).
2. **Создать задачу** (Create Task):
   - **General**: имя `DualogMailAgent`, "Run whether user is logged on or not" (по желанию).
   - **Triggers**: New → "At startup" (при загрузке системы).
   - **Actions**: New →
     - Program/script: `pythonw.exe` (полный путь, например `C:\Users\<user>\AppData\Local\Programs\Python\Python312\pythonw.exe`)
     - Add arguments: `main.py`
     - Start in: путь до папки проекта, например `C:\Users\<user>\dualog-mail-agent`
   - **Settings**: включить "If the task fails, restart every 1 minute", "Restart up to 3 times".
3. Сохранить, при необходимости ввести пароль учётной записи Windows.

`pythonw.exe` запускает без консольного окна (фоновый режим). Логи всё равно пишутся в `logs\agent.log`.

## 8. Обновление кода в будущем

На Mac: внести изменения → `git push`.
На судовом ПК (при наличии интернета):
```powershell
cd dualog-mail-agent
git pull
```
Затем перезапустить задачу в Планировщике (или просто дождаться следующего старта Windows).

## Важно

- `.env` и папки `state/`, `logs/` не должны попадать в Git (уже в `.gitignore`) — 
  там хранятся пароли и локальное состояние, разное для каждой машины.
- После `git pull` на новой машине `.env` нужно создавать заново из `.env.example`.
