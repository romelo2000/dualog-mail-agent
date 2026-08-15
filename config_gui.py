"""
Простое графическое окно настроек агента (Tkinter, без внешних зависимостей).

Позволяет создавать/редактировать .env без ручного редактирования текстового
файла — удобно, если пароль от Dualog или Gmail App Password меняется.

Запуск: python config_gui.py  (или собранный DualogAgentSettings.exe)
"""
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

ENV_PATH = BASE_DIR / ".env"
ENV_EXAMPLE_PATH = BASE_DIR / ".env.example"

# (env_key, label, is_secret, default)
FIELDS = [
    ("DUALOG_IMAP_HOST", "Dualog IMAP хост", False, "192.168.2.254"),
    ("DUALOG_IMAP_PORT", "Dualog IMAP порт", False, "143"),
    ("DUALOG_IMAP_USER", "Dualog логин (email)", False, ""),
    ("DUALOG_IMAP_PASSWORD", "Dualog пароль", True, ""),
    ("DUALOG_IMAP_FOLDER", "Dualog папка", False, "INBOX"),
    ("DUALOG_IMAP_USE_SSL", "Dualog SSL (true/false)", False, "false"),
    ("GMAIL_SMTP_USER", "Gmail адрес", False, ""),
    ("GMAIL_SMTP_APP_PASSWORD", "Gmail App Password", True, ""),
    ("GMAIL_FORWARD_TO", "Куда пересылать (Gmail)", False, ""),
    ("POLL_INTERVAL_SECONDS", "Интервал опроса, сек", False, "300"),
]


def parse_env_file(path: Path) -> dict:
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()
    return values


def write_env_file(path: Path, values: dict) -> None:
    lines = [
        "# Сгенерировано DualogAgentSettings — можно редактировать вручную при желании.",
        "",
        "# ---- Dualog IMAP (источник) ----",
        f"DUALOG_IMAP_HOST={values.get('DUALOG_IMAP_HOST', '')}",
        f"DUALOG_IMAP_PORT={values.get('DUALOG_IMAP_PORT', '143')}",
        f"DUALOG_IMAP_USER={values.get('DUALOG_IMAP_USER', '')}",
        f"DUALOG_IMAP_PASSWORD={values.get('DUALOG_IMAP_PASSWORD', '')}",
        f"DUALOG_IMAP_FOLDER={values.get('DUALOG_IMAP_FOLDER', 'INBOX')}",
        f"DUALOG_IMAP_USE_SSL={values.get('DUALOG_IMAP_USE_SSL', 'false')}",
        "",
        "# ---- Gmail SMTP (назначение) ----",
        "GMAIL_SMTP_HOST=smtp.gmail.com",
        "GMAIL_SMTP_PORT=465",
        f"GMAIL_SMTP_USER={values.get('GMAIL_SMTP_USER', '')}",
        f"GMAIL_SMTP_APP_PASSWORD={values.get('GMAIL_SMTP_APP_PASSWORD', '')}",
        f"GMAIL_FORWARD_TO={values.get('GMAIL_FORWARD_TO', '')}",
        "",
        "# ---- Поведение агента ----",
        f"POLL_INTERVAL_SECONDS={values.get('POLL_INTERVAL_SECONDS', '300')}",
        "IMAP_TIMEOUT_SECONDS=25",
        "SMTP_TIMEOUT_SECONDS=20",
        "MAX_RETRIES=3",
        "RETRY_DELAY_SECONDS=2",
        "CYCLE_WATCHDOG_SECONDS=120",
        "STATE_FILE=state/seen_uids.json",
        "LOG_FILE=logs/agent.log",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


class SettingsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dualog -> Gmail Agent — Настройки")
        self.geometry("480x480")
        self.resizable(False, False)

        existing = parse_env_file(ENV_PATH)
        self.entries: dict[str, tk.Entry] = {}
        self.show_secret_vars: dict[str, tk.BooleanVar] = {}

        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Настройки Dualog → Gmail Agent",
            font=("TkDefaultFont", 13, "bold"),
        ).grid(row=0, column=0, columnspan=3, pady=(0, 12), sticky="w")

        row = 1
        for key, label, is_secret, default in FIELDS:
            ttk.Label(container, text=label + ":").grid(
                row=row, column=0, sticky="w", pady=4
            )
            var_show = tk.BooleanVar(value=False)
            entry = ttk.Entry(
                container,
                width=32,
                show="*" if is_secret else "",
            )
            entry.insert(0, existing.get(key, default))
            entry.grid(row=row, column=1, pady=4, padx=(8, 4))
            self.entries[key] = entry

            if is_secret:
                self.show_secret_vars[key] = var_show

                def toggle(entry=entry, var=var_show):
                    entry.config(show="" if var.get() else "*")

                ttk.Checkbutton(
                    container, text="показать", variable=var_show, command=toggle
                ).grid(row=row, column=2, sticky="w")

            row += 1

        btn_frame = ttk.Frame(container)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(16, 0), sticky="ew")

        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(btn_frame, text="Закрыть", command=self.destroy).pack(side="left")

        self.status_var = tk.StringVar(value="")
        ttk.Label(container, textvariable=self.status_var, foreground="green").grid(
            row=row + 1, column=0, columnspan=3, pady=(8, 0), sticky="w"
        )

    def save(self):
        values = {key: entry.get().strip() for key, entry in self.entries.items()}

        missing = [
            label
            for key, label, _, _ in FIELDS
            if key
            in (
                "DUALOG_IMAP_HOST",
                "DUALOG_IMAP_USER",
                "DUALOG_IMAP_PASSWORD",
                "GMAIL_SMTP_USER",
                "GMAIL_SMTP_APP_PASSWORD",
                "GMAIL_FORWARD_TO",
            )
            and not values.get(key)
        ]
        if missing:
            messagebox.showwarning(
                "Не все поля заполнены",
                "Заполните обязательные поля:\n- " + "\n- ".join(missing),
            )
            return

        try:
            write_env_file(ENV_PATH, values)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))
            return

        self.status_var.set(f"Сохранено в {ENV_PATH.name}")
        messagebox.showinfo(
            "Готово",
            "Настройки сохранены.\nПерезапустите DualogMailAgent.exe, чтобы изменения вступили в силу.",
        )


def main():
    app = SettingsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
