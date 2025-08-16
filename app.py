import os
import json
import requests
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
from haversine import haversine
from flask_cors import CORS
import io
import base64

# Load API keys
load_dotenv()
ODSAY_KEY = os.getenv("ODSAY_API_KEY")
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Load station coordinates from JSON
with open("station_coords.json", encoding='utf-8') as f:
    STATIONS = json.load(f)

# 사용자 클릭 위치에서 가장 가까운 역 찾기
def find_nearest_station(user_lat, user_lng):
    user_loc = (user_lat, user_lng)
    nearest = min(
        STATIONS,
        key=lambda station: haversine(user_loc, (float(station["lat"]), float(station["lng"])))
    )
    distance = haversine(user_loc, (float(nearest["lat"]), float(nearest["lng"])))
    return {
        "name": nearest["name"],
        "lat": float(nearest["lat"]),
        "lng": float(nearest["lng"]),
        "distance": round(distance, 2)  # km 단위로 반올림
    }

# 📍 새로 추가: 가장 가까운 지하철역 찾기 API
@app.route("/api/nearest-station", methods=["POST"])
def nearest_station():
    data = request.get_json()
    user_lat = data.get("lat")
    user_lng = data.get("lng")
    
    if not user_lat or not user_lng:
        return jsonify({"error": "Missing coordinates"}), 400
    
    try:
        nearest = find_nearest_station(float(user_lat), float(user_lng))
        return jsonify(nearest)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📍 주소를 좌표로 변환하는 API (카카오 주소검색 우선, 키워드 검색 폴백)
@app.route("/api/geocode", methods=["POST"])
def geocode():
    data = request.get_json() or {}
    keyword = (data.get("address") or "").strip()
    if not keyword:
        return jsonify({"error": "Missing address"}), 400

    if not KAKAO_API_KEY:
        return jsonify({"error": "KAKAO_API_KEY not set"}), 500

    # 1) 카카오 '주소검색' (정확한 도로명/지번 주소용)
    try:
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        params = {"query": keyword}
        r = requests.get(url, headers=headers, params=params, timeout=8)
        j = r.json() if r.content else {}

        docs = j.get("documents", []) if isinstance(j, dict) else []
        if docs:
            first = docs[0]
            # 카카오는 x=lng, y=lat
            lng = first.get("x")
            lat = first.get("y")
            if lng and lat:
                return jsonify({
                    "lat": str(lat),
                    "lng": str(lng),
                    "address_name": first.get("address_name") or keyword
                })
    except Exception as e:
        print("[geocode] kakao address error:", e)

    # 2) 주소검색 결과가 없으면 '키워드검색' 폴백 (장소명/건물명 등)
    try:
        url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        params = {"query": keyword}
        r = requests.get(url, headers=headers, params=params, timeout=8)
        j = r.json() if r.content else {}

        docs = j.get("documents", []) if isinstance(j, dict) else []
        if docs:
            first = docs[0]
            lng = first.get("x")
            lat = first.get("y")
            if lng and lat:
                return jsonify({
                    "lat": str(lat),
                    "lng": str(lng),
                    "address_name": first.get("place_name") or keyword
                })
    except Exception as e:
        print("[geocode] kakao keyword error:", e)

    # 3) 모두 실패
    return jsonify({"error": "Address not found"}), 404

# 출발역에서 모든 지하철역까지의 소요시간 계산
def get_subway_times_from(start_lat, start_lng):
    results = []
    for station in STATIONS:
        url = f"https://api.odsay.com/v1/api/searchPubTransPathT?"
        params = {
            "SX": start_lng,
            "SY": start_lat,
            "EX": station["lng"],
            "EY": station["lat"],
            "OPT": 0,
            "apiKey": ODSAY_KEY
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            continue
        try:
            time = res.json()["result"]["path"][0]["info"]["totalTime"]
            results.append({
                "name": station["name"],
                "lat": station["lat"],
                "lng": station["lng"],
                "time": time
            })
        except (KeyError, IndexError):
            continue
    return results

# 📍 API: 좌표 받아서 소요 시간 반환
@app.route("/api/subway-times", methods=["POST"])
def subway_times():
    data = request.get_json()
    user_lat = data.get("lat")
    user_lng = data.get("lng")
    if not user_lat or not user_lng:
        return jsonify({"error": "Missing coordinates"}), 400

    results = get_subway_times_from(user_lat, user_lng)
    return jsonify(results)

@app.route('/api/accessible', methods=['POST'])
def accessible():
    data = request.json
    user_lat = float(data['lat'])
    user_lng = float(data['lng'])
    user_coord = (user_lat, user_lng)

    reachable_stations = []

    for station in STATIONS:
        try:
            station_lat = float(station['lat'])
            station_lng = float(station['lng'])

            url = f"https://api.odsay.com/v1/api/searchPubTransPathT?SX={user_lng}&SY={user_lat}&EX={station_lng}&EY={station_lat}&OPT=0&apiKey={ODSAY_KEY}"
            res = requests.get(url)
            res_data = res.json()

            # 지하철만 포함된 경로 찾기
            for path in res_data['result']['path']:
                if path['subPath'][0]['trafficType'] == 1:  # 1: subway
                    total_time = path['info']['totalTime']
                    reachable_stations.append({
                        "station": station['name'],
                        "lat": station_lat,
                        "lng": station_lng,
                        "time": total_time
                    })
                    break
        except Exception as e:
            print(f"Error for station {station['name']}: {e}")
            continue

    return jsonify(reachable_stations)

# 역지오코딩 API 엔드포인트 추가
@app.route("/api/reverse-geocode", methods=["POST"])
def reverse_geocode():
    data = request.get_json()
    lat = data.get("lat")
    lng = data.get("lng")
    
    if not lat or not lng:
        return jsonify({"error": "Missing coordinates"}), 400
    
    try:
        # 카카오 지도 API를 사용한 역지오코딩
        url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json"
        headers = {
            "Authorization": f"KakaoAK {KAKAO_API_KEY}"
        }
        params = {
            "x": lng,  # 경도
            "y": lat   # 위도
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to get address"}), 400
            
        result = response.json()
        
        if result.get("documents") and len(result["documents"]) > 0:
            address_info = result["documents"][0]
            
            # 도로명 주소가 있으면 우선 사용, 없으면 지번 주소 사용
            address = ""
            if address_info.get("road_address"):
                address = address_info["road_address"]["address_name"]
            elif address_info.get("address"):
                address = address_info["address"]["address_name"]
            
            if address:
                return jsonify({"address": address})
            else:
                return jsonify({"error": "Address not found"}), 404
        else:
            return jsonify({"error": "Address not found"}), 404
            
    except Exception as e:
        print(f"Reverse geocoding error: {e}")
        return jsonify({"error": "Failed to process reverse geocoding"}), 500

# 🆕 컨투어 라인 생성을 위한 함수
def create_contour_data(center_lat, center_lng, time_data, grid_size=50):
    """
    주어진 중심점과 시간 데이터를 기반으로 컨투어 데이터를 생성합니다.
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

# 🆕 컨투어 이미지 생성 API
@app.route("/api/contour", methods=["POST"])
def generate_contour():
    try:
        data = request.get_json()
        user_lat = float(data.get("lat"))
        user_lng = float(data.get("lng"))
        
        if not user_lat or not user_lng:
            return jsonify({"error": "Missing coordinates"}), 400
        
        # 모든 역까지의 소요시간 계산
        time_data = get_subway_times_from(user_lat, user_lng)
        
        if len(time_data) < 3:
            return jsonify({"error": "Insufficient data for contour generation"}), 400
        
        # 컨투어 데이터 생성
        grid_lat, grid_lng, grid_time = create_contour_data(user_lat, user_lng, time_data)
        
        # matplotlib 설정
        plt.rcParams['font.family'] = ['DejaVu Sans']
        plt.figure(figsize=(10, 8))
        
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
        
        # 컬러바 추가
        cbar = plt.colorbar(contour)
        cbar.set_label('Travel Time (minutes)', rotation=270, labelpad=20)
        
        # 역 위치 표시
        station_lats = [float(item['lat']) for item in time_data]
        station_lngs = [float(item['lng']) for item in time_data]
        plt.scatter(station_lngs, station_lats, c='white', s=20, alpha=0.8, edgecolors='black')
        
        # 사용자 위치 표시
        plt.scatter(user_lng, user_lat, c='red', s=100, marker='*', 
                   edgecolors='white', linewidth=2, label='Starting Point')
        
        # 제목과 라벨
        plt.title('Subway Accessibility Contour Map (Pastel Pink-Purple)', 
                 fontsize=14, pad=20)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 이미지를 메모리에 저장
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # base64로 인코딩
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return jsonify({
            "image": img_str,
            "contour_data": {
                "center_lat": user_lat,
                "center_lng": user_lng,
                "stations_count": len(time_data)
            }
        })
        
    except Exception as e:
        print(f"Contour generation error: {e}")
        return jsonify({"error": f"Failed to generate contour: {str(e)}"}), 500

# 🆕 컨투어 데이터만 반환하는 API (프론트엔드에서 직접 그리기용)
@app.route("/api/contour-data", methods=["POST"])
def get_contour_data():
    try:
        data = request.get_json()
        user_lat = float(data.get("lat"))
        user_lng = float(data.get("lng"))
        
        if not user_lat or not user_lng:
            return jsonify({"error": "Missing coordinates"}), 400
        
        # 모든 역까지의 소요시간 계산
        time_data = get_subway_times_from(user_lat, user_lng)
        
        if len(time_data) < 3:
            return jsonify({"error": "Insufficient data for contour generation"}), 400
        
        # 컨투어 데이터 생성
        grid_lat, grid_lng, grid_time = create_contour_data(user_lat, user_lng, time_data)
        
        # NaN 값을 null로 변환
        grid_time_cleaned = np.where(np.isnan(grid_time), None, grid_time).tolist()
        
        return jsonify({
            "grid_lat": grid_lat.tolist(),
            "grid_lng": grid_lng.tolist(),
            "grid_time": grid_time_cleaned,
            "stations": time_data,
            "center": {
                "lat": user_lat,
                "lng": user_lng
            }
        })
        
    except Exception as e:
        print(f"Contour data generation error: {e}")
        return jsonify({"error": f"Failed to generate contour data: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)