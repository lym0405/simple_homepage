# 🚇 지하철 접근성 컨투어 맵

이 프로젝트는 사용자가 지정한 위치에서 모든 지하철역까지의 소요시간을 기반으로 **컨투어 맵(등고선 지도)**을 생성하는 Flask 웹 애플리케이션입니다. 컨투어 라인은 파스텔 핑크-퍼플 색상으로 표현되며, 지하철 접근성을 시각적으로 분석할 수 있습니다.

## ✨ 주요 기능

### 🗺️ 컨투어 맵 생성
- **실시간 소요시간 계산**: ODsay API를 통해 정확한 대중교통 소요시간 계산
- **부드러운 보간**: scipy의 griddata를 사용한 cubic/linear 보간
- **파스텔 색상**: RdPu 컬러맵을 사용한 아름다운 핑크-퍼플 그라데이션
- **시각적 요소**: 지하철역 위치, 출발지 표시, 컨투어 라인 라벨

### 🌐 API 엔드포인트
- `/api/contour` - 컨투어 이미지 생성 (base64 인코딩)
- `/api/contour-data` - 컨투어 데이터만 반환 (프론트엔드 활용)
- `/api/subway-times` - 모든 역까지의 소요시간 데이터
- `/api/geocode` - 주소 → 좌표 변환
- `/api/reverse-geocode` - 좌표 → 주소 변환
- `/api/nearest-station` - 가장 가까운 지하철역 찾기

## 📦 설치 및 설정

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
`.env` 파일을 생성하고 API 키를 설정하세요:
```bash
cp .env.example .env
```

`.env` 파일 편집:
```
ODSAY_API_KEY=your_odsay_api_key_here
KAKAO_API_KEY=your_kakao_api_key_here
```

### 3. 서버 실행
```bash
python app.py
```

## 🚀 사용 방법

### 웹 인터페이스
1. `contour_demo.html` 파일을 브라우저에서 열기
2. 위도/경도 입력 또는 샘플 위치 버튼 클릭
3. "컨투어 맵 생성" 버튼 클릭
4. 생성된 컨투어 맵 확인

### API 직접 호출
```python
import requests

# 컨투어 이미지 생성
response = requests.post('http://localhost:5000/api/contour', 
                        json={'lat': 37.498095, 'lng': 127.027610})
data = response.json()

if response.ok:
    image_base64 = data['image']
    # base64 이미지를 파일로 저장하거나 웹에서 표시
```

### 테스트 스크립트 실행
실제 API 없이 모의 데이터로 테스트:
```bash
python test_contour.py
```

## 🎨 컨투어 맵 특징

### 색상 의미
- **연한 핑크**: 짧은 소요시간 (접근성 좋음)
- **진한 퍼플**: 긴 소요시간 (접근성 나쁨)
- **흰색 점**: 지하철역 위치
- **빨간 별**: 출발지 위치

### 시간 범위
- 0분 ~ 100분까지 5분 간격으로 표시
- 컨투어 라인은 10분 간격으로 표시
- 각 라인에 시간 라벨 표시

## 📁 파일 구조

```
/workspace/
├── app.py                 # Flask 애플리케이션 (컨투어 기능 포함)
├── station_coords.json    # 지하철역 좌표 데이터
├── requirements.txt       # Python 의존성
├── .env.example          # 환경변수 예시
├── contour_demo.html     # 웹 데모 페이지
├── test_contour.py       # 테스트 스크립트
└── README.md             # 프로젝트 문서
```

## 🔧 기술 스택

### Backend
- **Flask**: 웹 프레임워크
- **NumPy**: 수치 계산
- **SciPy**: 보간 및 과학 계산
- **Matplotlib**: 그래프 및 이미지 생성
- **Requests**: HTTP 요청

### APIs
- **ODsay API**: 대중교통 소요시간 계산
- **Kakao Map API**: 주소/좌표 변환

### Frontend
- **HTML5/CSS3**: 웹 인터페이스
- **JavaScript (ES6)**: 동적 기능
- **Fetch API**: 비동기 통신

## 📊 API 응답 예시

### 컨투어 이미지 생성 (`/api/contour`)
```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAAA...",
  "contour_data": {
    "center_lat": 37.498095,
    "center_lng": 127.027610,
    "stations_count": 30
  }
}
```

### 컨투어 데이터 (`/api/contour-data`)
```json
{
  "grid_lat": [37.398095, 37.399095, ...],
  "grid_lng": [126.927610, 126.928610, ...],
  "grid_time": [[20, 25, 30, ...], [15, 20, 25, ...], ...],
  "stations": [
    {"name": "강남역", "lat": 37.498095, "lng": 127.027610, "time": 5},
    ...
  ],
  "center": {"lat": 37.498095, "lng": 127.027610}
}
```

## ⚠️ 주의사항

1. **API 키 필수**: ODsay와 Kakao API 키가 필요합니다
2. **서울 지역 제한**: 현재 서울 지하철역 데이터만 포함
3. **응답 시간**: 실제 API 호출 시 30초~1분 소요 가능
4. **CORS 설정**: 프론트엔드는 localhost:3000에서만 접근 가능

## 🔮 향후 계획

- [ ] 실시간 지하철 운행 정보 반영
- [ ] 다른 도시 지하철 데이터 추가
- [ ] 웹 지도 연동 (Leaflet, Google Maps)
- [ ] 시간대별 소요시간 차이 분석
- [ ] 모바일 최적화

## 🤝 기여하기

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

**🎯 목표**: 지하철 접근성을 직관적으로 시각화하여 부동산, 교통 계획, 도시 개발 등 다양한 분야에서 활용할 수 있는 도구 제공
