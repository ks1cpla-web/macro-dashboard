import datetime
import json
import os
import urllib.parse
import urllib.request

# 1. FRED API 키 설정 (GitHub Secret에서 가져옴)
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")


def get_fred_series(series_id, limit=30):
  """FRED API에서 특정 시리즈의 최근 데이터를 가져오는 함수"""
  if not FRED_API_KEY:
    print("FRED_API_KEY가 설정되지 않았습니다.")
    return {}

  url = (
      "https://api.stlouisfed.org/fred/series/observations?"
      f"series_id={series_id}&api_key={FRED_API_KEY}&file_type=json"
      f"&sort_order=desc&limit={limit}"
  )

  try:
    req = urllib.request.urlopen(url)
    data = json.loads(req.read().decode("utf-8"))
    observations = data.get("observations", [])

    # 날짜를 키로, 값을 숫자로 하는 딕셔너리 생성 ('.' 값 등 에러 방어)
    result = {}
    for obs in obs_item := observations:
      date_str = obs["date"]
      val_str = obs["value"]
      try:
        result[date_str] = float(val_str)
      except ValueError:
        continue  # 데이터가 '.' 이거나 없으면 스킵
    return result
  except Exception as e:
    print(f"Error fetching {series_id}: {e}")
    return {}


def main():
  # 2. 수집할 FRED 시리즈 ID 매핑
  # WALCL: 연준 총자산 (Fed Assets)
  # WTREGEN: 재무부 일반계정 (TGA)
  # RPTCW: 역레포 잔고 (RRP)
  series_map = {
      "Fed_Assets": "WALCL",
      "TGA": "WTREGEN",
      "RRP": "RPTCW",
  }

  raw_data = {}
  all_dates = set()

  for key, s_id in series_map.items():
    print(f"Fetching {key} ({s_id})...")
    data_dict = get_fred_series(s_id, limit=60)
    raw_data[key] = data_dict
    all_dates.update(data_dict.keys())

  # 날짜 기준 내림차순 정렬
  sorted_dates = sorted(list(all_dates), reverse=True)

  daily_records = []

  for d in sorted_dates:
    fed_assets = raw_data["Fed_Assets"].get(d)
    tga = raw_data["TGA"].get(d)
    rrp = raw_data["RRP"].get(d)

    # 데이터가 하나라도 있으면 처리 (혹은 모두 있는 날만 모을 수도 있음)
    if fed_assets is not None and tga is not None and rrp is not None:
      # Net Liquidity 계산 공식: 연준 총자산 - TGA - RRP (단위 백만 달러 등 원본 기준)
      net_liquidity = fed_assets - tga - rrp

      record = {
          "date": d,
          "Fed_Assets": fed_assets,
          "TGA": tga,
          "RRP": rrp,
          "Net_Liquidity": round(net_liquidity, 2),
      }
      daily_records.append(record)

  # 3. 최종 JSON 구조 생성
  output_data = {
      "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      "daily_records": daily_records,
  }

  # 4. data.json으로 저장
  with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

  print(
      f"Success! Saved {len(daily_records)} records with Net Liquidity into"
      " data.json."
  )


if __name__ == "__main__":
  main()
