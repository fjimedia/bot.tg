import os
from pathlib import Path

print("Текущая папка:", Path.cwd())
print("Файлы в папке:", os.listdir())
print(".env существует:", Path('.env').exists())
