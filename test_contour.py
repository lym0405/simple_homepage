#!/usr/bin/env python3
"""
지하철 접근성 컨투어 맵 테스트 스크립트
실제 API 없이 샘플 데이터로 컨투어 생성을 테스트합니다.
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import random

# 샘플 역 데이터 로드
with open("station_coords.json", encoding='utf-8') as f:
    STATIONS = json.load(f)

def generate_mock_travel_times(user_lat, user_lng):
    """
    실제 API 대신 모의 이동시간 데이터를 생성합니다.
    거리에 따라 대략적인 이동시간을 계산합니다.
    """
    results = []
    
    for station in STATIONS:
        station_lat = float(station["lat"])
        station_lng = float(station["lng"])
        
        # 거리 계산 (대략적)
        lat_diff = abs(user_lat - station_lat)
        lng_diff = abs(user_lng - station_lng)
        distance = np.sqrt(lat_diff**2 + lng_diff**2)
        
        # 거리에 따른 대략적인 이동시간 (분)
        # 랜덤 요소 추가로 현실적인 데이터 생성
        base_time = distance * 1000  # 거리에 비례한 기본 시간
        random_factor = random.uniform(0.8, 1.5)  # 80% ~ 150% 변동
        travel_time = int(base_time * random_factor)
        
        # 5분에서 120분 사이로 제한
        travel_time = max(5, min(120, travel_time))
        
        results.append({
            "name": station["name"],
            "lat": station_lat,
            "lng": station_lng,
            "time": travel_time
        })
    
    return results

def create_contour_data(center_lat, center_lng, time_data, grid_size=50):
    """
    컨투어 데이터를 생성합니다.
    """
    # 시간 데이터에서 좌표와 시간 추출
    lats = [float(item['lat']) for item in time_data]
    lngs = [float(item['lng']) for item in time_data]
    times = [float(item['time']) for item in time_data]
    
    if len(lats) < 3:
        raise ValueError("최소 3개의 데이터 포인트가 필요합니다.")
    
    # 경계 설정 (중심점 기준 ±0.1도)
    lat_min, lat_max = center_lat - 0.1, center_lat + 0.1
    lng_min, lng_max = center_lng - 0.1, center_lng + 0.1
    
    # 그리드 생성
    grid_lat = np.linspace(lat_min, lat_max, grid_size)
    grid_lng = np.linspace(lng_min, lng_max, grid_size)
    grid_lng_mesh, grid_lat_mesh = np.meshgrid(grid_lng, grid_lat)
    
    # 보간을 통해 그리드에 시간 값 매핑
    try:
        grid_time = griddata(
            (lngs, lats), times, 
            (grid_lng_mesh, grid_lat_mesh), 
            method='cubic', 
            fill_value=np.nan
        )
    except:
        # cubic이 실패하면 linear 사용
        grid_time = griddata(
            (lngs, lats), times, 
            (grid_lng_mesh, grid_lat_mesh), 
            method='linear', 
            fill_value=np.nan
        )
    
    return grid_lat, grid_lng, grid_time

def generate_contour_image(user_lat, user_lng, save_path="contour_test.png"):
    """
    컨투어 이미지를 생성하고 저장합니다.
    """
    print(f"컨투어 맵을 생성 중... 중심점: ({user_lat}, {user_lng})")
    
    # 모의 이동시간 데이터 생성
    time_data = generate_mock_travel_times(user_lat, user_lng)
    print(f"생성된 역 데이터: {len(time_data)}개")
    
    # 컨투어 데이터 생성
    grid_lat, grid_lng, grid_time = create_contour_data(user_lat, user_lng, time_data)
    
    # matplotlib 설정 (한글 폰트)
    plt.rcParams['font.family'] = ['DejaVu Sans']
    plt.figure(figsize=(12, 10))
    
    # 컨투어 플롯 생성 (파스텔 핑크-퍼플 컬러맵)
    levels = np.arange(0, 101, 5)  # 0분부터 100분까지 5분 간격
    contour = plt.contourf(grid_lng, grid_lat, grid_time, 
                          levels=levels, 
                          cmap='RdPu', 
                          alpha=0.8)
    
    # 컨투어 라인 추가
    contour_lines = plt.contour(grid_lng, grid_lat, grid_time, 
                               levels=levels[::2],  # 10분 간격으로 라인
                               colors='white', 
                               alpha=0.6, 
                               linewidths=0.8)
    
    # 라벨 추가
    plt.clabel(contour_lines, inline=True, fontsize=8, fmt='%d min')
    
    # 컬러바 추가
    cbar = plt.colorbar(contour, shrink=0.8)
    cbar.set_label('Travel Time (minutes)', rotation=270, labelpad=20, fontsize=12)
    
    # 역 위치 표시
    station_lats = [float(item['lat']) for item in time_data]
    station_lngs = [float(item['lng']) for item in time_data]
    plt.scatter(station_lngs, station_lats, c='white', s=30, alpha=0.9, 
               edgecolors='black', linewidth=1, label='Subway Stations')
    
    # 사용자 위치 표시
    plt.scatter(user_lng, user_lat, c='red', s=200, marker='*', 
               edgecolors='white', linewidth=3, label='Starting Point', zorder=5)
    
    # 제목과 라벨
    plt.title('Subway Accessibility Contour Map (Pastel Pink-Purple)', 
             fontsize=16, pad=20, fontweight='bold')
    plt.xlabel('Longitude', fontsize=12)
    plt.ylabel('Latitude', fontsize=12)
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # 축 범위 설정
    plt.xlim(user_lng - 0.1, user_lng + 0.1)
    plt.ylim(user_lat - 0.1, user_lat + 0.1)
    
    # 이미지 저장
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print(f"컨투어 맵이 '{save_path}'에 저장되었습니다.")
    
    return time_data

def main():
    """
    메인 함수 - 여러 지점에서 컨투어 맵을 생성합니다.
    """
    print("🚇 지하철 접근성 컨투어 맵 테스트")
    print("=" * 50)
    
    # 테스트할 위치들
    test_locations = [
        {"name": "강남역", "lat": 37.498095, "lng": 127.027610},
        {"name": "홍대입구역", "lat": 37.557192, "lng": 126.925381},
        {"name": "명동역", "lat": 37.563424, "lng": 126.986023},
        {"name": "서울역", "lat": 37.554648, "lng": 126.970731}
    ]
    
    for i, location in enumerate(test_locations, 1):
        print(f"\n{i}. {location['name']} 중심 컨투어 맵 생성")
        
        save_path = f"contour_{location['name']}.png"
        time_data = generate_contour_image(
            location['lat'], 
            location['lng'], 
            save_path
        )
        
        # 통계 정보 출력
        times = [item['time'] for item in time_data]
        print(f"   평균 소요시간: {np.mean(times):.1f}분")
        print(f"   최소 소요시간: {min(times)}분")
        print(f"   최대 소요시간: {max(times)}분")
    
    print("\n✅ 모든 테스트 완료!")
    print("\n💡 생성된 이미지 파일들:")
    for location in test_locations:
        print(f"   - contour_{location['name']}.png")

if __name__ == "__main__":
    main()