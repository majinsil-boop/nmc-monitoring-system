"""
run_all.py — 모니터링 전체 프로세스 원클릭 실행

실행 순서:
  1. 오늘 날짜 JSON 파일 확인 → 없을 때만 수집 스크립트 실행
  2. Flask 서버 시작 (report_server.py)
  3. 브라우저에서 체크박스 검토 페이지 오픈
  4. 사용자가 항목 선택 후 '보고서 생성' 버튼 클릭 → HTML+PDF 생성
"""

import glob
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime

BASE = os.path.expanduser("~")


# ── 1. 오늘 날짜 파일 확인 → 없을 때만 수집 스크립트 실행 ────────────────────

today_str = datetime.now().strftime("%Y%m%d")

SCRIPTS = [
    ("assembly_search.py", "assembly_results_*.json"),
    ("schedule_search.py", "schedule_results_*.json"),
    ("news_monitor.py",    "news_results_*.json"),
]


def today_file_exists(pattern: str) -> bool:
    """오늘 날짜(YYYYMMDD)가 포함된 파일 중 데이터가 1건 이상인 파일이 있으면 True."""
    files = glob.glob(os.path.join(BASE, pattern.replace("*", f"*{today_str}*")))
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list) and len(data) > 0:
                return True
        except Exception:
            pass
    return False


def run_script(name: str) -> bool:
    path = os.path.join(BASE, name)
    print(f"\n{'='*60}")
    print(f"▶  {name} 실행 중...")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, path], cwd=BASE)
    ok = result.returncode == 0
    print(f"[{'완료' if ok else f'오류 (종료코드 {result.returncode})'}] {name}")
    return ok


print(f"\n{'='*60}")
print(f"수집 파일 확인 (기준일: {today_str})")
print(f"{'='*60}")

if all(today_file_exists(pat) for _, pat in SCRIPTS):
    print("  -> 오늘 날짜 파일 모두 존재 - 수집 스킵")
else:
    for script, pattern in SCRIPTS:
        if today_file_exists(pattern):
            print(f"  [건너뜀] {script} - 오늘 파일 이미 존재")
        else:
            run_script(script)


# ── 2. Flask 서버 시작 → 브라우저 오픈 ──────────────────────────────────────

SERVER_PORT   = 5000
SERVER_URL    = f"http://127.0.0.1:{SERVER_PORT}"
SERVER_SCRIPT = os.path.join(BASE, "report_server.py")


def _server_ready(timeout: int = 2) -> bool:
    """서버가 응답할 때까지 최대 timeout초 대기. 응답하면 True."""
    for _ in range(timeout * 4):
        try:
            urllib.request.urlopen(SERVER_URL + "/", timeout=1)
            return True
        except Exception:
            time.sleep(0.25)
    return False


print(f"\n{'='*60}")
print("Flask 서버 시작")
print(f"{'='*60}")


def _kill_port(port: int):
    """해당 포트를 점유 중인 프로세스를 모두 강제 종료."""
    try:
        out = subprocess.check_output("netstat -ano", shell=True).decode("cp949", errors="ignore")
        pids = set()
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pids.add(line.strip().split()[-1])
        for pid in pids:
            subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True)
        if pids:
            print(f"  기존 서버 종료 (PID: {', '.join(pids)})")
            time.sleep(1)
    except Exception:
        pass


# 기존 서버 모두 정리 후 새로 시작
_kill_port(SERVER_PORT)

kw = {"creationflags": subprocess.CREATE_NEW_CONSOLE} if sys.platform == "win32" else {}
subprocess.Popen([sys.executable, SERVER_SCRIPT], cwd=BASE, **kw)
print("  서버 시작 중...")
if _server_ready(timeout=15):
    print(f"  → 준비 완료: {SERVER_URL}")
else:
    print("  [경고] 서버 응답 없음.")
    print(f"  직접 실행: python report_server.py")
    print("\n완료.")
    sys.exit(1)

print(f"\n{'='*60}")
print("브라우저 오픈")
print(f"{'='*60}")
if sys.platform == "win32":
    subprocess.Popen(["cmd", "/c", "start", "", SERVER_URL])
else:
    webbrowser.open(SERVER_URL)
print(f"  → {SERVER_URL}")
print("\n체크박스에서 항목을 선택한 후 '보고서 생성' 버튼을 누르세요.")
print("완료.")
