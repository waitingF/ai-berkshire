@echo off
setlocal

for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "SCOPE=user"

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="--project" (
  set "SCOPE=project"
  shift
  goto parse_args
)
if /I "%~1"=="--user" (
  set "SCOPE=user"
  shift
  goto parse_args
)
if /I "%~1"=="-h" goto show_help
if /I "%~1"=="--help" goto show_help
echo Unknown option: %~1
exit /b 1

:show_help
echo Usage: .\scripts\install-cursor-skills.bat [--user^|--project]
echo.
echo Install AI Berkshire Cursor skills generated from skills/*.md.
echo.
echo Options:
echo   --user      Install to %%USERPROFILE%%\.cursor\skills ^(default^)
echo   --project   Install to ^<repo^>\.cursor\skills for this repository only
exit /b 0

:args_done
if /I "%SCOPE%"=="project" (
  set "DEST=%ROOT%\.cursor\skills"
) else if defined CURSOR_SKILLS_DIR (
  set "DEST=%CURSOR_SKILLS_DIR%"
) else (
  set "DEST=%USERPROFILE%\.cursor\skills"
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

%PY% "%ROOT%\scripts\sync-cursor-skills.py"
if errorlevel 1 exit /b %ERRORLEVEL%

if not exist "%DEST%" mkdir "%DEST%"
if errorlevel 1 exit /b %ERRORLEVEL%

for /d %%D in ("%ROOT%\cursor-skills\*") do (
  if exist "%DEST%\%%~nxD" rmdir /s /q "%DEST%\%%~nxD"
  if errorlevel 1 exit /b 1
  xcopy "%%~fD" "%DEST%\%%~nxD\" /E /I /Y >nul
  if errorlevel 1 exit /b 1
)

echo Installed Cursor skills to %DEST%
echo Do not install into %%USERPROFILE%%\.cursor\skills-cursor; that directory is reserved by Cursor.
if /I "%SCOPE%"=="user" (
  echo Skills are available across all projects. Restart Cursor or start a new chat if needed.
) else (
  echo Skills are scoped to this repository only.
)
