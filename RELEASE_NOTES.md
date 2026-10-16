osu!stable 전체화면용 pp 오버레이의 첫 공개 배포입니다.

- 곡 선택 시 모드를 반영한 95/97/99/100% FC 예상 pp
- 로컬 개인 최고 pp, 플레이 중 현재 pp 및 완주 예상 pp
- osu!standard / mania 지원
- 게임 해상도에 따른 배율·위치 조정
- Python/Node.js/tosu를 포함한 오프라인 설치 패키지
- Windows 로그인 시 자동 실행

설치: 아래 ZIP을 다운로드해 압축을 모두 풀고 Install.cmd를 실행하세요.
GitHub의 Source code ZIP은 런타임을 포함하지 않습니다.
Windows 10/11 x64 및 osu!stable용입니다.
위치 조정: Ctrl + Shift + Space.

공개 패키지에는 개인 플레이 기록, 로그, 기존 위치 설정, 사용자별 닉네임 목록이 포함되지 않습니다.
pp 계산 버전은 동봉된 tosu 4.26.2에 고정되어 있습니다.
완주 예상은 현재 정확도를 유지하고 추가 미스가 없다고 가정한 추정값입니다.

검증: Python 테스트 19개, JavaScript 화면 로직 테스트 통과.
새 PC에서 실제 전체화면 플레이와 Windows 로그인 재현은 추가 확인이 필요합니다.
