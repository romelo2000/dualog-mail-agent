# Установка и запуск на судовом ПК (Windows)

## Вариант А (проще): готовый .exe из GitHub Releases

Не нужен Python на судовом ПК — только сам исполняемый файл.

1. Открыть https://github.com/romelo2000/dualog-mail-agent/releases
2. Скачать `DualogMailAgent-windows.zip` из последнего релиза, распаковать в отдельную папку
   (например `C:\DualogAgent\`).
3. В этой папке будут: `DualogMailAgent.exe`, `DualogAgentSettings.exe`, `.env.example`, `rules.yaml`.
4. Запустить `DualogAgentSettings.exe` — откроется окно настроек, где нужно заполнить:
   хост/порт/логин/пароль Dualog IMAP, Gmail-адрес и App Password, куда пересылать.
   Нажать **Сохранить** — файл `.env` создастся/обновится автоматически.
   Если пароль (Dualog или Gmail) поменяется в будущем — просто снова открыть
   `DualogAgentSettings.exe`, изменить поле и сохранить, редактировать текстовый файл вручную не нужно.
5. Отредактировать `rules.yaml` под критерии важности (обычный текстовый файл, блокнотом).
6. Запустить `DualogMailAgent.exe` двойным кликом (работает без консольного окна,
   логи пишутся в `logs\agent.log` рядом с exe).
7. Для автозапуска при старте Windows — см. раздел 7 ниже, только вместо
   `pythonw.exe main.py` указать путь к `DualogMailAgent.exe` напрямую (Program/script),
   без аргументов.

Новые версии `.exe` собираются автоматически в GitHub Actions при выпуске тега
(`.github/workflows/build-windows-exe.yml`) — просто скачивайте новый релиз при обновлении.

**Важно**: `.exe` не подписан цифровой подписью (нужен платный сертификат), поэтому
Windows SmartScreen/антивирус может показать предупреждение "Неизвестный издатель"
при первом запуске. Это нормально для самостоятельно собранных программ — нужно
нажать "Подробнее" → "Выполнить в любом случае".

## Вариант Б: запуск из исходников через Python

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
