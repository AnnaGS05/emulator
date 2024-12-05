import os
import tarfile
import argparse
import xml.etree.ElementTree as ET
import shutil
import sys
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime


class ShellEmulator:
    def __init__(self, username, fs_archive, log_file):
        self.username = username
        self.current_directory = '/'
        self.fs_root = '/tmp/shell_emulator_fs'
        self.log_file = log_file

        # Распаковка виртуальной файловой системы
        self.extract_fs(fs_archive)

        # Инициализация XML лог-файла
        self.init_log()

    def extract_fs(self, fs_archive):
        """Распаковывает виртуальную файловую систему в заданную папку."""
        if os.path.exists(self.fs_root):
            shutil.rmtree(self.fs_root)
        os.makedirs(self.fs_root)

        with tarfile.open(fs_archive, 'r') as tar_ref:
            tar_ref.extractall(self.fs_root)

    def init_log(self):
        """Инициализирует XML лог-файл."""
        self.log_root = ET.Element("session")
        self.log_root.set("username", self.username)

    def save_log(self):
        """Сохраняет XML лог в файл."""
        tree = ET.ElementTree(self.log_root)
        with open(self.log_file, "wb") as log:
            tree.write(log, encoding="utf-8", xml_declaration=True)

    def log_action(self, command, result=None):
        """Логирует команды и результаты в XML."""
        log_entry = ET.SubElement(self.log_root, "action")
        log_entry.set("timestamp", datetime.now().isoformat())
        log_entry.set("command", command)
        log_entry.text = result if result else "None"

    def prompt(self):
        """Возвращает приглашение к вводу."""
        return f"{self.username}:{self.current_directory}$ "

    def run_command(self, command):
        """Обрабатывает ввод пользователя."""
        try:
            if command.startswith('ls'):
                return self.ls()
            elif command.startswith('cd'):
                return self.cd(command.split(' ')[1] if len(command.split()) > 1 else '/')
            elif command == 'exit':
                return self.exit()
            elif command.startswith('cat'):
                return self.cat(command.split(' ')[1])
            elif command.startswith('tac'):
                return self.tac(command.split(' ')[1])
            elif command.startswith('head'):
                parts = command.split(' ')
                n = int(parts[1]) if len(parts) > 2 else 10
                file = parts[-1]
                return self.head(file, n)
            else:
                return f"Команда '{command}' не поддерживается."
        except Exception as e:
            return f"Ошибка: {str(e)}"

    def ls(self):
        """Команда ls."""
        path = os.path.join(self.fs_root, self.current_directory.strip('/'))
        if os.path.exists(path):
            files = os.listdir(path)
            result = '  '.join(files)
            return result
        else:
            return f"Путь '{self.current_directory}' не существует."

    def cd(self, path):
        """Команда cd."""
        if path.startswith('/'):
            new_dir = os.path.join(self.fs_root, path.strip('/'))
        else:
            new_dir = os.path.join(self.fs_root, self.current_directory.strip('/'), path.strip('/'))

        if path == '..':
            self.current_directory = os.path.dirname(self.current_directory.rstrip('/'))
            if not self.current_directory:
                self.current_directory = '/'
            return f"Перешли в директорию: {self.current_directory}"

        if os.path.isdir(new_dir):
            if path.startswith('/'):
                self.current_directory = '/' + path.strip('/')
            else:
                self.current_directory = os.path.join(self.current_directory, path).replace('\\', '/')
            return f"Перешли в директорию: {self.current_directory}"
        else:
            return f"Директория '{path}' не существует."

    def cat(self, file):
        """Команда cat."""
        file_path = os.path.join(self.fs_root, self.current_directory.strip('/'), file)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        else:
            return f"Файл '{file}' не существует."

    def tac(self, file):
        file_path = os.path.join(self.fs_root, self.current_directory.strip('/'), file)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
                return ''.join(lines[::-1])
        else:
            return f"Файл '{file}' не существует."

    def head(self, file, n=10):
        parts = file.split(' ')
        if len(parts) > 1:
            n = int(parts[0])
            file = parts[1]
        file_path = os.path.join(self.fs_root, self.current_directory.strip('/'), file)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                return ''.join(f.readlines()[:n])
        else:
            return f"Файл '{file}' не существует."

    def exit(self):
        self.save_log()
        sys.exit("Выход из эмулятора.")


class ShellGUI:
    def __init__(self, shell):
        self.shell = shell
        self.root = tk.Tk()
        self.root.title("Shell Emulator")

        # Поле ввода команды
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.command_label = tk.Label(self.input_frame, text="Команда:")
        self.command_label.pack(side=tk.LEFT, padx=5)

        self.command_entry = tk.Entry(self.input_frame, width=50)
        self.command_entry.pack(side=tk.LEFT, padx=5)

        self.run_button = tk.Button(self.input_frame, text="Выполнить", command=self.run_command)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = tk.Button(self.input_frame, text="Очистить", command=self.clear_output)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # Поле вывода результатов
        self.output_frame = tk.Frame(self.root)
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.output_text = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Запуск GUI
        self.root.mainloop()

    def run_command(self):
        """Обрабатывает выполнение команды через GUI."""
        command = self.command_entry.get()
        if not command:
            return

        result = self.shell.run_command(command)
        self.shell.log_action(command, result)
        self.display_output(f"{self.shell.prompt()}{command}\n{result}\n")

    def display_output(self, text):
        """Выводит текст в окно вывода."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def clear_output(self):
        """Очищает окно вывода."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)


def generate_files():
    """Функция для генерации всех нужных файлов в директории."""
    virtual_fs_dir = 'virtual_fs'
    if not os.path.exists(virtual_fs_dir):
        os.makedirs(virtual_fs_dir)
        with open(os.path.join(virtual_fs_dir, 'file1.txt'), 'w') as f:
            f.write("Это содержимое файла 1.\n")
        with open(os.path.join(virtual_fs_dir, 'file2.txt'), 'w') as f:
            f.write("Это содержимое файла 2.\nЭто содержимое файла 2.\n")

        os.makedirs(os.path.join(virtual_fs_dir, 'subdir'))
        with open(os.path.join(virtual_fs_dir, 'subdir', 'file3.txt'), 'w') as f:
            f.write("Это содержимое файла в поддиректории.\n")

    fs_tar = 'virtual_fs.tar'
    with tarfile.open(fs_tar, 'w') as tar_ref:
        tar_ref.add(virtual_fs_dir, arcname='.')

    print(f"Создан архив виртуальной файловой системы: {fs_tar}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Эмулятор shell для UNIX-подобных систем.")
    parser.add_argument("--username", required=True, help="Имя пользователя для показа в приглашении к вводу.")
    parser.add_argument("--filesystem", required=True, help="Путь к архиву виртуальной файловой системы.")
    parser.add_argument("--logfile", required=True, help="Путь к лог-файлу (XML).")
    parser.add_argument("--generate_files", action="store_true", help="Сгенерировать все необходимые файлы в текущей директории.")

    args = parser.parse_args()

    if args.generate_files:
        generate_files()
        print("Файлы сгенерированы. Теперь можно запустить скрипт без опции --generate_files")
        sys.exit(0)

    if not os.path.exists(args.filesystem):
        print(f"Файл {args.filesystem} не существует. Пожалуйста, создайте его или запустите скрипт с опцией --generate_files")
        sys.exit(1)

    shell = ShellEmulator(args.username, args.filesystem, args.logfile)
    ShellGUI(shell)
