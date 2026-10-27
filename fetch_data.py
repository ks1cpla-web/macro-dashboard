import datetime
import json
import os
import urllib.request

# 1. API 키 설정 (GitHub Secret 환경변수에서 불러옴)
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")


# 2. FRED API에서 데이터 가져오는 헬퍼 함수 예시
def get_fred_latest(series_id):
    if not FRED_API_KEY:
        return None
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1"
    try:
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode("utf-8"))
        obs = data["observations"][0]
        return {"date": obs["date"], "value": float(obs["value"])}
    except Exception as e:
        print(f"Error fetching {series_id}: {e}")
        return None


# 3. 메인 수집 로직
def main():
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # FRED 데이터 예시 (TGA: WTREGEN, RRP: RPTCW)
    tga_data = get_fred_latest("WTREGEN")
    rrp_data = get_fred_latest("RPTCW")

    # 기존 지표 및 산출 로직 적용 예시
    tga_val = tga_data["value"] if tga_data else 0
    rrp_val = rrp_data["value"] if rrp_data else 0

    # 종합 데이터 구조화 (질문자님의 엑셀 행 구조 형태)
    result_data = {
        "updated_at": today_str,
        "daily_records": [
            {
                "date": today_str,
                "TGA": tga_val,
                "RRP": rrp_val,
                # 필요시 QQQ, Reserves_Adj, Z10 등 지표 추가 계산
            }
        ],
    }

    # 4. JSON 파일로 저장 (웹 대시보드가 읽어갈 데이터)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print("Data collection completed successfully!")


if __name__ == "__main__":
    main()
