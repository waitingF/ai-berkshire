@echo off
setlocal

for %%I in ("%~dp0..") do set "ROOT=%%~fI"
set "SCOPE=project"

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
echo Usage: .\scripts\install-dsh-skills.bat [--project^|--user]
echo.
echo Install AI Berkshire DeepSeek Harness skills generated from skills/*.md.
echo.
echo Options:
echo   --project   Install to ^<repo^>\.dsh\skills for this repository only ^(default^)
echo   --user      Install to %%DSH_HOME%%\skills ^(default %%USERPROFILE%%\.dsh\skills^)
exit /b 0

:args_done
if /I "%SCOPE%"=="project" (
  set "DEST=%ROOT%\.dsh\skills"
) else if defined DSH_SKILLS_DIR (
  set "DEST=%DSH_SKILLS_DIR%"
) else if defined DSH_HOME (
  set "DEST=%DSH_HOME%\skills"
) else (
  set "DEST=%USERPROFILE%\.dsh\skills"
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  set "PY=python"
)

%PY% "%ROOT%\scripts\generate-dsh-skills.py"
if errorlevel 1 exit /b %ERRORLEVEL%

if not exist "%DEST%" mkdir "%DEST%"
if errorlevel 1 exit /b %ERRORLEVEL%

for /d %%D in ("%ROOT%\dsh-skills\*") do (
  if exist "%DEST%\%%~nxD" rmdir /s /q "%DEST%\%%~nxD"
  if errorlevel 1 exit /b 1
  xcopy "%%~fD" "%DEST%\%%~nxD\" /E /I /Y >nul
  if errorlevel 1 exit /b 1
)

echo Installed DeepSeek Harness skills to %DEST%
if /I "%SCOPE%"=="user" (
  echo Skills are available across all projects. DSH watches this root; new sessions pick them up automatically.
) else (
  echo Skills are scoped to this repository only ^(DSH project-dsh root, rank 100^).
)
