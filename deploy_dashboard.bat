@echo off
chcp 65001 >nul
setlocal

rem 전체 빌드, Vercel 운영 배포, 고정 주소 검증을 한 번에 실행한다.
rem cmd는 rem 줄에서도 리다이렉션 기호를 해석하므로 주석에 부등호를 쓰지 않는다.
rem
rem   deploy_dashboard.bat                빌드 + 배포 + 검증 (더블클릭 가능)
rem   deploy_dashboard.bat --verify-only  배포 없이 현재 운영 주소만 검증
rem
rem 다른 스크립트에서 부를 때는 set NOPAUSE=1 을 두면 끝에서 멈추지 않는다.

cd /d "%~dp0"
set "PYTHONUTF8=1"

set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if defined PY goto :run
where python >nul 2>nul
if not errorlevel 1 set "PY=python"

:run
if not defined PY (
    echo [실패] Python을 찾을 수 없습니다. python.org 에서 설치한 뒤 PATH를 확인하세요.
    set "RC=9009"
    goto :done
)

echo === 투자 아이디어 샘터 배포 시작 ===
%PY% "%~dp0tools\deploy_dashboard.py" %*
set "RC=%ERRORLEVEL%"

:done
echo.
if "%RC%"=="0" (
    echo === 완료: https://investment-spring.vercel.app ===
) else (
    echo === 실패: 종료 코드 %RC% · 위 오류 메시지를 확인하세요 ===
)
if not defined NOPAUSE pause
exit /b %RC%
