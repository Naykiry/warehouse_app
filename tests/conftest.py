import os
import sys

# Добавляем корень проекта в sys.path, чтобы тесты могли импортировать модули из корневой папки
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
