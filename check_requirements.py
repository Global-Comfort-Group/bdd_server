#!/usr/bin/env python3
"""
Script to check if all imported packages are in requirements.txt
Run this before deploying to catch missing dependencies
"""
import ast
import os
import re
from pathlib import Path
from typing import Set

# Map import names to package names (when they differ)
IMPORT_TO_PACKAGE = {
    'jose': 'python-jose',
    'passlib': 'passlib',
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'pydantic_settings': 'pydantic-settings',
}

# Standard library modules (don't need to be in requirements.txt)
STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
    'atexit', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
    'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
    'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
    'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
    'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
    'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno',
    'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter',
    'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext',
    'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http',
    'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress',
    'itertools', 'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging',
    'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap',
    'modulefinder', 'msilib', 'msvcrt', 'multiprocessing', 'netrc', 'nis',
    'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'parser',
    'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform',
    'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile', 'pstats',
    'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random',
    're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched',
    'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
    'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
    'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
    'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog',
    'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
    'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace',
    'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing',
    'typing_extensions', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv',
    'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref',
    'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib',
    '__future__', '__main__',
}

def get_imports_from_file(filepath: Path) -> Set[str]:
    """Extract all top-level import names from a Python file"""
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Get the top-level package name
                    package = alias.name.split('.')[0]
                    imports.add(package)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level package name
                    package = node.module.split('.')[0]
                    imports.add(package)
    except Exception as e:
        print(f"⚠️  Could not parse {filepath}: {e}")
    
    return imports

def get_all_imports(directory: Path) -> Set[str]:
    """Get all imports from all Python files in directory"""
    all_imports = set()
    
    for filepath in directory.rglob('*.py'):
        # Skip __pycache__ and venv
        if '__pycache__' in str(filepath) or 'venv' in str(filepath):
            continue
        
        imports = get_imports_from_file(filepath)
        all_imports.update(imports)
    
    return all_imports

def get_requirements_packages(requirements_file: Path) -> Set[str]:
    """Get package names from requirements.txt"""
    packages = set()
    
    if not requirements_file.exists():
        return packages
    
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Extract package name (before ==, >=, etc.)
            match = re.match(r'^([a-zA-Z0-9_\-\[\]]+)', line)
            if match:
                package = match.group(1)
                # Handle extras like uvicorn[standard]
                package = package.split('[')[0]
                packages.add(package.lower())
    
    return packages

def main():
    """Check if all imports have corresponding packages in requirements.txt"""
    project_dir = Path(__file__).parent
    app_dir = project_dir / 'app'
    requirements_file = project_dir / 'requirements.txt'
    
    print("🔍 Checking for missing dependencies...")
    print(f"📁 Scanning: {app_dir}")
    print(f"📄 Requirements: {requirements_file}\n")
    
    # Get all imports
    all_imports = get_all_imports(app_dir)
    
    # Filter out local app imports and stdlib
    external_imports = {
        imp for imp in all_imports 
        if imp != 'app' and imp not in STDLIB_MODULES
    }
    
    print(f"✅ Found {len(external_imports)} external package imports\n")
    
    # Get requirements
    requirements = get_requirements_packages(requirements_file)
    
    # Check for missing packages
    missing = set()
    for imp in sorted(external_imports):
        # Map import name to package name if different
        package_name = IMPORT_TO_PACKAGE.get(imp, imp)
        
        # Check if package is in requirements (case-insensitive)
        if package_name.lower() not in requirements:
            missing.add((imp, package_name))
    
    if missing:
        print("❌ MISSING DEPENDENCIES:")
        print("=" * 60)
        for imp, pkg in sorted(missing):
            if imp == pkg:
                print(f"  import {imp:20} → ADD: {pkg}")
            else:
                print(f"  import {imp:20} → ADD: {pkg} (package name differs)")
        print("\n💡 Add these to requirements.txt:")
        for imp, pkg in sorted(missing):
            print(f"  {pkg}==<version>")
        print()
        return False
    else:
        print("✅ All dependencies are in requirements.txt!")
        print("\n📦 External packages used:")
        for imp in sorted(external_imports):
            package_name = IMPORT_TO_PACKAGE.get(imp, imp)
            print(f"  ✓ {imp:20} ({package_name})")
        return True

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)

