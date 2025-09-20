@echo off
python bot.py 2> error.log
if %errorlevel% neq 0 (
    echo ОШИБКА: Смотрите error.log
    type error.log
)
pause