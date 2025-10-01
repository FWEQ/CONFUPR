import shlex
import getpass
import socket
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from typing import List
import argparse # хавает аргументы из команд строки
import os # пути и т.п.

PREFIX = "{user}@{host}:{cwd}$ "


class EmulatorGUI(tk.Tk):
    def __init__(self, config):
        super().__init__()
        user = getpass.getuser()
        host = socket.gethostname()

        self.user = user
        self.host = host
        self.config = config # считываем конфиг лоль

        self.vfs_root = os.path.abspath(config.get("vfs") if config.get("vfs") else os.getcwd())
        if not os.path.isdir(self.vfs_root):
            raise ValueError(f"Ошибка: VFS путь {self.vfs_root} не является директорией")
        self.cwd = self.vfs_root

        self.title(f"Эмулятор - [{user}@{host}]")
        self.geometry("800x480")

        self.output = ScrolledText(
            self,
            state="disabled",
            wrap="word",
            font=("Consolas",11)
        )
        self.output.pack(
            fill="both",
            expand=True
        )

        entry_frame = tk.Frame(self)
        entry_frame.pack(fill="x")
        self.prompt_label = tk.Label(
            entry_frame,
            text=self.make_prompt(),
            font=("Consolas",11),
        )
        self.prompt_label.pack(side="left")
        self.entry = tk.Entry(entry_frame, font=("Consolas", 11))
        self.entry.pack(
            side="left",
            fill="x",
            expand=True)
        self.entry.bind("<Return>", self.on_enter)

        self._write("Добро пожаловать в эмулятор (Вариант 11 — Этап 3).")
        self._write("Поддерживаемые команды: ls, cd, exit, conf-dump. Аргументы в кавычках учитываются.")
        self.entry.focus_set()

        if self.config.get("script"):
            #сделать функцию парс строки из заготовки,вызов команд
            self.run_script(self.config["script"])

    def make_prompt(self):
        rel = os.path.relpath(self.cwd, self.vfs_root)
        if rel == ".":
            cwd_display = "/"
        else:
            cwd_display = "/" + rel.replace("\\", '/')
        return PREFIX.format(user=self.user, host=self.host, cwd=cwd_display)

    def run_script(self, path):
        if not os.path.exists(path):
            self._write(f"ошибкаб скрипт {path} не найден")
            return
        self._write(f"выполенение стартового скрипта {path}")
        try:
            with open(path,"r",encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    self._write(f"{self.make_prompt()}{line}")
                    try:
                        self.execute_line(line)
                    except Exception as e:
                        self._write(f"Ошибка выполнения строки '{line}': {e}")
        except Exception as e:
            self._write(f"Ошибка чтения скрипта: {e}")

    def _write(self, text: str):
        self.output.config(state="normal")
        self.output.insert("end", text + ("\n" if not text.endswith("\n") else ""))
        self.output.see("end")
        self.output.config(state="disabled")

    def on_enter(self, event):
        line = self.entry.get()
        self.entry.delete(0, "end")
        self._write(f"{self.make_prompt()}{line}")
        try:
            self.execute_line(line)
        except Exception as e:
            self._write(f"Ошибка выполнения: {e}")

    def execute_line(self, line: str):
        if not line.strip():
            return
        try:
            parts = shlex.split(line)
        except ValueError as e:
            self._write(f"Error: неверный синтаксис аргументов: {e}")
            return
        if not parts:
            return
        cmd = parts[0]
        args = parts[1:]

        if cmd == "ls":
            self.cmd_ls(args)
        elif cmd == "cd":
            self.cmd_cd(args)
        elif cmd == "exit":
            self.cmd_exit(args)
        elif cmd == "help":
            self.cmd_help(args)
        elif cmd == "conf-dump":
            self.cmd_conf_dump(args)
        else:
            self._write(f"Error: неизвестная команда: '{cmd}'")

    def cmd_conf_dump(self, args: List[str]):
        self._write("Текущая конфигурация:")
        for k, v in self.config.items():
            self._write(f"{k} = {v}")
        self._write(f"cwd = {self.cwd}")

    def cmd_ls(self, args: List[str]):
        start_cwd = self.cwd
        def walk(path, prefix=""):
            try:
                entries = sorted(os.listdir(path))
            except Exception as e:
                self._write(f"Ошибка доступа: {e}")
                return
            for i, name in enumerate(entries):
                full = os.path.join(path, name)
                if i == len(entries)-1:
                    connector = "└── "
                else:
                    connector = "├── "
                self._write(prefix + connector + name + ("/" if os.path.isdir(full) else ""))
                if os.path.isdir(full):
                    extension = "    " if i == len(entries) - 1 else "│   "
                    walk(full, prefix + extension)
        if not args:
            self._write(".")
            walk(self.cwd)
            self.cwd = '.'
        else:
            for i in args:
                self._write(".")
                walk(i)
                self.cwd = '.'

    def cmd_cd(self, args: List[str]):
        if len(args) == 0:
            self.cwd = self.vfs_root
            self._write("Переход в корень VFS")
        elif len(args) == 1:
            target = os.path.join(self.cwd, args[0])
            abs_target = os.path.abspath(target)

            if not abs_target.startswith(self.vfs_root):
                self._write("Ошибка: выход за пределы VFS запрещён")
                return

            if os.path.isdir(abs_target):
                self.cwd = abs_target
                self._write(f"Текущая директория: {self.cwd}")
            else:
                self._write(f"cd: нет такой директории: {args[0]}")
        else:
            self._write("Error: cd принимает не более одного аргумента")

        self.prompt_label.config(text=self.make_prompt())
    def cmd_exit(self, args: List[str]):
        if len(args) == 0:
            self._write("exit")
            self.destroy()
        elif len(args) == 1:
            try:
                code = int(args[0])
                self._write(f"exit {code}")
                self.destroy()
            except ValueError:
                self._write("Error: exit ожидает числовой код возврата")
        else:
            self._write("Error: exit принимает не более одного аргумента")

    def cmd_help(self, args: List[str]):
        self._write("Поддерживаемые команды (этап 1, заглушки): ls, cd, exit, help")
        self._write("Парсер аргументов поддерживает кавычки: например: ls \"file name with spaces\"")

def load_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vfs", help="Путь к виртуальной файловой системе", default="")
    parser.add_argument("--script", help="Путь к стартовому скрипту", default="")
    args = parser.parse_args()

    return {
        "vfs": args.vfs or None,
        "script": args.script
    }

if __name__ == "__main__":
    app = EmulatorGUI(load_config())
    app.mainloop()
