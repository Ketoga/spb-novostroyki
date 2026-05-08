import requests
import json
import os
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://xn--80az8a.xn--d1aqf.xn--p1ai/",
}

BASE = "https://xn--80az8a.xn--d1aqf.xn--p1ai"
PLACE = "78"  # Санкт-Петербург

os.makedirs("data", exist_ok=True)

def fetch(url, params=None):
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Ошибка при запросе {url}: {e}")
        return None

def parse_domrf():
    print("📡 Загружаем данные с наш.дом.рф...")
    result = {}

    # Мета-статистика
    meta = fetch(f"{BASE}/сервисы/api/kn/meta", {"place": PLACE, "objStatus": 0})
    if meta:
        result["meta"] = meta
        print(f"  ✅ Мета: {json.dumps(meta)[:100]}")

    # Застройщики
    devs = fetch(f"{BASE}/сервисы/api/kn/developers", {
        "place": PLACE, "objStatus": 0,
        "offset": 0, "limit": 999999,
        "sortType": "asc", "sortField": "devShortCleanNm"
    })
    if devs:
        result["developers"] = devs
        count = len(devs.get("data", devs if isinstance(devs, list) else []))
        print(f"  ✅ Застройщики: {count} шт.")

    # ЖК (группы)
    gk = fetch(f"{BASE}/сервисы/api/kn/devGk", {
        "place": PLACE, "objStatus": 0,
        "offset": 0, "limit": 999999,
        "sortType": "asc"
    })
    if gk:
        result["complexes"] = gk
        count = len(gk.get("data", gk if isinstance(gk, list) else []))
        print(f"  ✅ ЖК: {count} шт.")

    # Метро
    metro = fetch(f"{BASE}/сервисы/api/kn/metro", {
        "place": PLACE, "objStatus": 0,
        "offset": 0, "limit": 999999
    })
    if metro:
        result["metro"] = metro
        print(f"  ✅ Метро загружено")

    # Сроки сдачи
    comm = fetch(f"{BASE}/сервисы/api/kn/commissioning", {
        "place": PLACE, "objStatus": 0
    })
    if comm:
        result["commissioning"] = comm
        print(f"  ✅ Сроки сдачи загружены")

    # Районы
    places = fetch(f"{BASE}/сервисы/api/kn/places", {
        "place": PLACE, "objStatus": 0,
        "offset": 0, "limit": 999999
    })
    if places:
        result["districts"] = places
        print(f"  ✅ Районы загружены")

    result["updated_at"] = datetime.now().isoformat()

    with open("data/domrf_spb.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ наш.дом.рф сохранён в data/domrf_spb.json")
    return result


def parse_trendrealty():
    print("\n📡 Загружаем данные с trendrealty.ru...")

    # Session нужно обновлять вручную — берётся из браузера
    SESSION = os.environ.get("TREND_SESSION", "")
    CITY = "58c665588b6aa52311afa01b"

    if not SESSION:
        print("  ⚠️  TREND_SESSION не задан — пропускаем trendrealty")
        return

    all_blocks = []
    offset = 0
    total = None

    while True:
        url = f"https://api.trendrealty.ru/blocks/search"
        params = {
            "show_type": "list",
            "city": CITY,
            "count": 100,
            "include_count": "true",
            "offset": offset,
            "sort": "rating",
            "sort_order": "desc",
            "session": SESSION
        }
        data = fetch(url, params)
        if not data or not data.get("data"):
            break

        results = data["data"].get("results", [])
        if total is None:
            total = data["data"].get("blocksCount", 0)
            print(f"  Всего ЖК: {total}")

        all_blocks.extend(results)
        print(f"  Загружено: {len(all_blocks)}/{total}")

        if len(results) < 100 or len(all_blocks) >= total:
            break
        offset += 100

    result = {
        "total": total,
        "complexes": all_blocks,
        "updated_at": datetime.now().isoformat()
    }

    with open("data/trendrealty_spb.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ trendrealty.ru сохранён: {len(all_blocks)} ЖК")


if __name__ == "__main__":
    parse_domrf()
    parse_trendrealty()
    print("\n🎉 Парсинг завершён!")
