# Astra Teleop Calibration & ArUco Pose Estimation

이 저장소는 **Charuco 보드** 기반 카메라 캘리브레이션부터 **실시간 ArUco 포즈 추정**까지의 전체 파이프라인을 자동화합니다.

---

## 프로젝트 구조

```
├── calibration_board.py        # Charuco 보드 이미지 생성
├── calibration_collect.py      # 보드 스냅샷 자동 수집
├── calibration_process.py      # Charuco 보드 캘리브레이션 수행
├── calibration_calculator.py   # (선택) FoV 계산 & 내부 파라미터 역생성
├── cam.py                      # cross-platform 카메라 오픈 함수
└── process.py                  # 실시간 ArUco 포즈 추정
```

---

## 사전 준비

1. **Python 3.8+**
2. 가상환경 생성 및 활성화

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. 필수 패키지 설치

   ```bash
   pip install opencv-python pyyaml pytransform3d numpy
   ```
4. **macOS 사용자**: 시스템 환경설정 ▶ 보안 및 개인 정보 보호 ▶ 카메라 ▶ 터미널(또는 IDE)에 권한 부여

---

## 1. Charuco 보드 이미지 생성

```bash
python calibration_board.py
```

* 출력: `calibration_board.png`
* 보드 사양: 5×7 격자, 체스보드 칸 4 cm, ArUco 마커 2 cm
* 용지 600 DPI 기준(5100×6600 px)
* **프린트**하거나 **전체 화면**으로 띄워 사용

---

## 2. 보드 스냅샷 자동 수집

```bash
python calibration_collect.py \
  -d 0 \
  -c calibration_images \
  -n 60
```

* `-d`: 카메라 인덱스(Windows/macOS) 또는 `/dev/videoX`(Linux)
* `-c`: 저장 폴더(`calibration_images/`)
* `-n`: 수집할 이미지 개수
* 결과:

  ```
  calibration_images/
  ├── 0001.png
  ├── 0002.png
  └── … (총 60장)
  ```

---

## 3. Charuco 보드 캘리브레이션 수행

```bash
python calibration_process.py \
  -c calibration_images
```

* 입력: `calibration_images/*.png`
* Charuco 코너 검출 → `cv2.calibrateCamera()` 실행
* 출력:

  ```
  calibration_images/calibration_results_<timestamp>.yaml
  ```

  내부 파라미터(`camera_matrix`, `distortion_coefficients`) 및 재투영 오차 저장

---

## 4. FoV 확인 & 내부 파라미터 역생성 (선택)

```bash
python calibration_calculator.py \
  -c calibration_images
```

* YAML 로드 → 수평·수직·대각선 시야각(FoV) 계산
* FoV & 해상도로부터 내부 파라미터 행렬(`K`) 재생성
* 결과를 터미널에 출력하여 검증

---

## 5. 실시간 ArUco 포즈 추정

```bash
python process.py \
  -d 0 \
  -c calibration_images
```

1. `open_cam()`으로 카메라 오픈 및 해상도·FPS 설정
2. `calibration_load()`로 `camera_matrix`, `distortion_coefficients` 로드
3. `get_detect()` & `get_solve()`로 검출기·포즈 계산기 초기화
4. **무한 루프**

   * `cam.read()` → 프레임 획득
   * `detect()` → ArUco 코너 검출
   * `solve()` → 6DoF 변환 행렬 계산
   * `cv2.imshow()` → 디버그 화면에 좌표축 시각화
   * 터미널에 변환 행렬 & 처리 시간 출력
   * ESC 키 누르면 종료

---

## 전체 워크플로우

```text
calibration_board.py
    ↓ (프린트/화면 표시)
calibration_collect.py
    ↓ (자동 이미지 수집)
calibration_process.py
    ↓ (YAML 내부 파라미터)
[ calibration_calculator.py ] ← (FoV 검증/역파라미터, 선택)
    ↓
process.py
    → 실시간 ArUco 6DoF 포즈 추정
```

---


