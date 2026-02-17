import pytest

from app.utils.code_sandbox import validate_python_code


class TestBannedImports:
    def test_import_os(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import os")

    def test_from_os_import(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("from os import path")

    def test_from_os_path_import(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("from os.path import join")

    def test_import_subprocess(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import subprocess")

    def test_import_ctypes(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import ctypes")

    def test_import_shutil(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import shutil")

    def test_import_socket(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("import socket")


class TestBannedBuiltins:
    def test_eval_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("eval('1+1')")

    def test_exec_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("exec('x=1')")

    def test_dunder_import(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("__import__('os')")

    def test_compile_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("compile('x=1', '<string>', 'exec')")

    def test_open_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("open('/etc/passwd')")

    def test_getattr_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("getattr(__builtins__, '__import__')")

    def test_setattr_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("setattr(x, 'y', 1)")

    def test_delattr_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("delattr(x, 'y')")

    def test_globals_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("globals()")

    def test_locals_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("locals()")

    def test_vars_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("vars()")

    def test_breakpoint_call(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("breakpoint()")


class TestEscapeVectors:
    def test_builtins_attr_access(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("__builtins__.__import__('os')")

    def test_nested_import_in_exec(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("exec('import os')")

    def test_eval_with_import(self) -> None:
        with pytest.raises(ValueError):
            validate_python_code("eval('__import__(\"os\")')")


class TestSafeCodeAllowed:
    def test_basic_math(self) -> None:
        validate_python_code("x = 1 + 2\nprint(x)")

    def test_list_comprehension(self) -> None:
        validate_python_code("[i**2 for i in range(10)]")

    def test_safe_import(self) -> None:
        validate_python_code("import json\nimport math")
