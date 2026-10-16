# osu! PP Overlay

osu!stable 전체화면에서 곡 선택 시 FC 예상 pp와 개인 최고 기록을 표시하고, 플레이 중 현재 pp와 완주 예상 pp를 보여주는 Windows 오버레이입니다.

- osu!standard / osu!mania 지원
- 선택한 모드를 반영한 95 · 97 · 99 · 100% FC 예상 pp
- 현재 PC의 로컬 기록을 다시 계산한 내 최고 pp
- 플레이 중 현재 pp 및 현재 정확도를 유지하며 추가 미스 없이 완주할 때의 예상 pp
- 게임 해상도에 따른 위치·크기 조정 및 수동 위치 저장
- Windows 로그인 시 자동 실행

## 설치

[Releases](https://github.com/bws96/osu-pp-overlay/releases)에서 `osu-pp-overlay-oneclick-v5.zip`을 다운로드해 **압축을 모두 푼 뒤 `Install.cmd`를 실행**하세요. GitHub의 **Code → Download ZIP**은 소스 코드이며 런타임을 포함하지 않습니다.

설치 패키지에는 Python, Node.js, tosu 및 전체화면 오버레이가 들어 있습니다. Windows 10/11 x64용이며, 설치 후에는 osu!stable만 실행하면 됩니다. 실행 중인 osu!의 설치 경로는 tosu가 감지합니다.

실제 설치 위치는 `%LOCALAPPDATA%\osuPPOverlay\v5-...`입니다. 설치 후에는 원본 ZIP이나 USB가 필요하지 않습니다. 다른 tosu/PP 프로그램이 실행 중이면 먼저 종료하세요.

## 위치와 해상도

게임 해상도를 읽어 배율과 위치를 조정합니다. 같은 해상도에서는 직접 조정한 위치를 유지합니다. 스킨과 화면 비율에 따라 곡 정보와의 간격은 다를 수 있습니다.

`Ctrl + Shift + Space`로 게임 안에서 위치·크기를 조절하고, 같은 단축키로 편집을 종료합니다.

FHD/QHD/4K/4:3/울트라와이드 배치 계산을 테스트했습니다. 다양한 모니터·DPI 및 다른 PC의 실제 전체화면 플레이는 추가 확인이 필요합니다.

## 계산과 개인 기록

계산은 tosu 4.26.2가 제공하는 네이티브 계산기를 사용합니다. 이전 rosu 계산 엔드포인트는 사용하지 않습니다. 포함된 버전은 2026년 7월 pp 계산 변경을 반영한 버전이며 이후 pp 변경은 자동 반영하지 않습니다.

완주 예상은 현재 정확도를 유지하고 남은 구간에 추가 미스·콤보 끊김이 없다고 가정합니다. 이미 발생한 판정·미스·콤보 손실은 유지합니다. 남은 노트 수에 따라 판정 반올림 오차가 생길 수 있습니다.

내 최고 pp는 현재 PC의 `scores.db`와 실행 중 수집한 완주 결과를 기준으로 합니다. 온라인 기록 전체 조회나 PC 간 기록 동기화 기능은 없습니다. 게임 기록은 읽기만 합니다.

이전 닉네임의 기록까지 포함하려면 실제 설치 폴더에 `account_aliases.local.json`을 만들 수 있습니다. 계정 ID를 키로 사용합니다. 이 파일은 Git에서 제외됩니다.

```json
{"123456": ["CurrentName", "PreviousName"]}
```

## 자동 실행 해제

실제 설치 폴더의 `DisableAutoStart.cmd`를 실행하거나, `Win + R` → `shell:startup`에서 `osu PP Overlay.vbs`를 삭제하세요. 현재 실행 중인 프로그램은 로그아웃 시 종료됩니다. PC방에서 재부팅 시 사용자 파일이 초기화되면 방문할 때마다 다시 설치해야 합니다.

## 개발과 테스트

Python 3.11+, Node.js 24가 필요합니다. 아래 테스트는 게임 실행이나 번들 런타임 없이 수행할 수 있습니다.

```powershell
python -m unittest -q test_distribution.py test_live_service.py test_local_scores.py test_core.py
node test_counter.cjs
node test_live_counter.cjs
```

실제 실행에는 배포 패키지의 `runtime/`가 필요합니다. 소스 저장소에는 실행 파일, 플레이 기록, 로그, 개인별 위치 설정을 넣지 않습니다.

```powershell
# 준비된 배포 패키지의 runtime 폴더로 빌드
python build_package.py --runtime-dir "C:\path\to\osu-pp-overlay\runtime"
```

`dist/`에 ZIP, SHA256, 파일별 무결성 목록이 생성됩니다. 전체 Python 설치 폴더를 runtime으로 지정하지 마세요. 전용 Python `._pth`와 앱 경로 설정이 필요하므로 기존 배포 패키지의 런타임 구조를 사용합니다.

## 구성

| 파일 | 역할 |
| --- | --- |
| `launcher.py` | 사용자별 설치, 자동 실행 등록, 백그라운드 실행 관리 |
| `bootstrap.py` | tosu 및 로컬 서비스 실행 |
| `configure_ingame.py`, `layout.py` | 네이티브 오버레이 설정과 해상도별 배치 |
| `counter/`, `live_counter/` | 곡 선택·플레이 화면 표시 |
| `personal_service.py`, `local_scores.py` | 로컬 개인 기록 조회 |
| `live_service.py`, `live_calculator.cjs` | 실시간 완주 예상 계산 |
| `record_calculator.cjs` | 개인 기록 재계산 |

로컬 포트는 `127.0.0.1:24050`, `127.0.0.1:24051`입니다. 오류 확인은 설치 폴더의 `startup.log`, `launcher-output.log`, `personal.log`, `runtime/tosu-4.26.2/logs`를 참고하세요.

## 오픈소스 구성요소

이 프로젝트는 tosu, Python, Node.js 및 Electron을 사용합니다. 동봉된 라이선스와 [THIRD-PARTY.txt](THIRD-PARTY.txt)에 출처를 정리했습니다. 해당 프로젝트나 osu!의 공식 제품은 아닙니다.
