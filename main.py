import shlex
import getpass
import socket
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from typing import List

PREFIX = "{user}@{host}:~$ "

class EmulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        user = getpass.getuser()
        host = socket.gethostname()

        self.user = user
        self.host = host

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
            text=PREFIX.format(user=user,host=host),
            font=("Consolas",11),
        )
        self.prompt_label.pack(side="left")
        self.entry = tk.Entry(entry_frame, font=("Consolas", 11))
        self.entry.pack(
            side="left",
            fill="x",
            expand=True)
        self.entry.bind("<Return>", self.on_enter)

        self._write("Добро пожаловать в эмулятор (Вариант 11 — Этап 1).")
        self._write("Поддерживаемые (заглушки): ls, cd, exit. Аргументы в кавычках учитываются.")
        self.entry.focus_set()

    def _write(self, text: str):
        self.output.config(state="normal")
        self.output.insert("end", text + ("\n" if not text.endswith("\n") else ""))
        self.output.see("end")
        self.output.config(state="disabled")

    def on_enter(self, event):
        line = self.entry.get()
        self.entry.delete(0, "end")
        prompt = PREFIX.format(user=self.user, host=self.host)
        self._write(f"{prompt}{line}")
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
        else:
            self._write(f"Error: неизвестная команда: '{cmd}'")


    def cmd_ls(self, args: List[str]):
        if args:
            self._write(f"ls called with args: {args}")
        else:
            self._write("ls called with no args")

    def cmd_cd(self, args: List[str]):
        if len(args) == 0:
            self._write("cd called with no args (go to home) — (заглушка)")
        elif len(args) == 1:
            self._write(f"cd called with arg: {args[0]}")
        else:
            self._write("Error: cd принимает не более одного аргумента")

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

if __name__ == "__main__":
    app = EmulatorGUI()
    app.mainloop()
