@echo off
setlocal enabledelayedexpansion

:: Имя текущего скрипта (например structure.bat)
set SCRIPT_NAME=%~nx0

:: Файл вывода
set OUTPUT_FILE=Structure.txt

:: Получаем имя текущей папки
for %%* in (.) do set CURRENT_DIR=%%~n*

echo Создаем структуру папки "%CD%" и сохраняем в %OUTPUT_FILE%
echo %CD%> "%OUTPUT_FILE%"
echo.>> "%OUTPUT_FILE%"

:: Используем tree /f для вывода структуры с файлами
:: Фильтруем через findstr, чтобы исключить строку с именем скрипта
tree /f /a | findstr /v /i /c:"%SCRIPT_NAME%" >> "%OUTPUT_FILE%"

echo Готово. Структура сохранена в %OUTPUT_FILE%
pause
