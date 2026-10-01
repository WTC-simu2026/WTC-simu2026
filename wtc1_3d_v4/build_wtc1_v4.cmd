@echo off
setlocal
set "WTC1_BLENDER=C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
if not exist "%WTC1_BLENDER%" (
  echo Blender 5.2 est introuvable a l'emplacement attendu.
  exit /b 1
)
"%WTC1_BLENDER%" --background --python "%~dp0scripts\build_wtc1_v4.py"
if errorlevel 1 exit /b %errorlevel%
echo.
echo Construction terminee. Le fichier se trouve dans output\WTC1_V4_MASTER.blend
pause
