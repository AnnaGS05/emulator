import unittest
import os
import shutil
import tarfile
from shellp import ShellEmulator


class TestShellEmulator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Создание виртуальной файловой системы перед тестами."""
        cls.fs_tar = 'test_virtual_fs.tar'
        cls.fs_root = '/tmp/shell_emulator_fs'
        os.makedirs('test_virtual_fs', exist_ok=True)

        # Создаем файлы
        with open('test_virtual_fs/file1.txt', 'w') as f:
            f.write("строка1\nстрока2\nстрока1\n")
        with open('test_virtual_fs/file2.txt', 'w') as f:
            f.write("строка3\nстрока4\n")
        os.makedirs('test_virtual_fs/subdir', exist_ok=True)
        with open('test_virtual_fs/subdir/file3.txt', 'w') as f:
            f.write("строка5\nстрока6\n")

        # Архивируем
        with tarfile.open(cls.fs_tar, 'w') as tarf:
            tarf.add('test_virtual_fs', arcname='.')

    @classmethod
    def tearDownClass(cls):
        """Очистка после тестов."""
        shutil.rmtree('test_virtual_fs')
        os.remove(cls.fs_tar)

    def setUp(self):
        """Инициализация эмулятора перед каждым тестом."""
        self.shell = ShellEmulator("test-user", self.fs_tar, "test_log.xml")

    def tearDown(self):
        """Очистка директории после каждого теста."""
        shutil.rmtree(self.shell.fs_root, ignore_errors=True)

    # Тесты для команды `ls`
    def test_ls_root(self):
        """Проверка команды ls в корне."""
        result = self.shell.run_command("ls")
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)
        self.assertIn("subdir", result)

    def test_ls_subdir(self):
        """Проверка команды ls в поддиректории."""
        self.shell.run_command("cd subdir")
        result = self.shell.run_command("ls")
        self.assertIn("file3.txt", result)

    def test_ls_invalid_dir(self):
        """Проверка команды ls в несуществующей директории."""
        self.shell.current_directory = "/nonexistent"
        result = self.shell.run_command("ls")
        self.assertIn("Путь '/nonexistent' не существует", result)

    # Тесты для команды `cd`
    def test_cd_to_subdir(self):
        """Проверка команды cd в поддиректорию."""
        result = self.shell.run_command("cd subdir")
        self.assertEqual(result, "Перешли в директорию: /subdir")

    def test_cd_to_parent_dir(self):
        """Проверка команды cd .. для возврата на уровень выше."""
        self.shell.run_command("cd subdir")
        result = self.shell.run_command("cd ..")
        self.assertEqual(result, "Перешли в директорию: /")

    def test_cd_invalid_dir(self):
        """Проверка команды cd в несуществующую директорию."""
        result = self.shell.run_command("cd invalid_dir")
        self.assertEqual(result, "Директория 'invalid_dir' не существует.")

    # Тесты для команды `cat`
    def test_cat_existing_file(self):
        """Проверка команды cat для существующего файла."""
        result = self.shell.run_command("cat file1.txt")
        self.assertEqual(result.strip(), "строка1\nстрока2\nстрока1")

    def test_cat_nonexistent_file(self):
        """Проверка команды cat для несуществующего файла."""
        result = self.shell.run_command("cat nonexistent.txt")
        self.assertIn("Файл 'nonexistent.txt' не существует.", result)

    # Тесты для команды `tac`
    def test_tac_existing_file(self):
        """Проверка команды tac для существующего файла."""
        result = self.shell.run_command("tac file1.txt")
        expected_output = "строка1\nстрока2\nстрока1"
        self.assertEqual(result.strip(), "\n".join(expected_output.split("\n")[::-1]))

    def test_tac_nonexistent_file(self):
        """Проверка команды tac для несуществующего файла."""
        result = self.shell.run_command("tac nonexistent.txt")
        self.assertIn("Файл 'nonexistent.txt' не существует.", result)

    # Тесты для команды `head`
    def test_head_existing_file(self):
        """Проверка команды head для существующего файла."""
        result = self.shell.run_command("head 2 file1.txt")
        self.assertEqual(result.strip(), "строка1\nстрока2")

    def test_head_nonexistent_file(self):
        """Проверка команды head для несуществующего файла."""
        result = self.shell.run_command("head nonexistent.txt")
        self.assertIn("Файл 'nonexistent.txt' не существует.", result)

    # Тест для команды `exit`
    def test_exit(self):
        """Проверка команды exit."""
        with self.assertRaises(SystemExit):
            self.shell.run_command("exit")


if __name__ == "__main__":
    unittest.main()
