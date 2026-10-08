import urllib.request
import os
import json
import csv

# ===================== 可自定义配置 =====================
BASE_URL = "https://tle2.486520.xyz"  # 修改这里为你的实际域名
DATA_DIR = "data"
TMP_DIR = ".tmp_download"
# =======================================================

tasks = [
    {"name": "Amsat", "url": "https://amsat.org/tle/current/nasabare.txt", "ext": "txt"},
    {"name": "Mmccants", "url": "https://www.mmccants.org/tles/classfd.zip", "ext": "zip"},
    {"name": "R4UAB", "url": "https://r4uab.ru/satonline.txt", "ext": "txt"},
    {"name": "ARISS", "url": "https://live.ariss.org/iss.txt", "ext": "txt"},
    {"name": "Satnogs", "url": "https://db.satnogs.org/api/tle/?format=3le", "ext": "txt"},
    {"name": "SatNOGS-transmitters", "url": "https://db.satnogs.org/api/transmitters/?format=json&status=active", "ext": "json"},
    {"name": "R4UAB-transmitters", "url": "https://r4uab.ru/transmitters.json", "ext": "json"},
    {"name": "Celestrak-json", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json", "ext": "json"},
]


def json_to_csv(json_path, csv_path, tag=""):
    """把 JSON 数组转成 CSV。返回 (状态字符串, 记录数)"""
    try:
        with open(json_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception as e:
        return ("parse-fail: %s" % e, 0)

    if not isinstance(data, list) or not data:
        return ("not-a-nonempty-list", 0)

    # 以首次出现顺序收集所有键，兼容个别记录缺键/多键
    fieldnames = []
    for rec in data:
        if isinstance(rec, dict):
            for k in rec.keys():
                if k not in fieldnames:
                    fieldnames.append(k)

    rows = [{k: rec.get(k, "") for k in fieldnames}
            for rec in data if isinstance(rec, dict)]

    tmp = csv_path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    # 内容一致就不覆盖，避免 mtime 无意义变化
    if os.path.exists(csv_path):
        with open(csv_path, "rb") as f:
            old = f.read()
        with open(tmp, "rb") as f:
            new = f.read()
        if old == new:
            os.remove(tmp)
            return ("no-change", len(rows))

    os.replace(tmp, csv_path)
    return ("updated", len(rows))


os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

for task in tasks:
    name, url, ext = task["name"], task["url"], task["ext"]
    target_path = f"{DATA_DIR}/{name}.{ext}"
    tmp_path = f"{TMP_DIR}/{name}.{ext}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()

        # Celestrak 限速/未更新校验
        if "celestrak.org" in url:
            text = content.decode("utf-8", errors="ignore")
            if "GP data has not updated" in text or "Data is updated once" in text:
                print(f"[skip] {name}: Celestrak rate-limit, keep old file")
                continue

        if not content.strip():
            print(f"[skip] {name}: empty response, skip")
            continue

        with open(tmp_path, "wb") as f:
            f.write(content)

        if not os.path.exists(target_path):
            os.replace(tmp_path, target_path)
            print(f"[new]  {name}: saved -> {target_path}")
        else:
            with open(target_path, "rb") as f:
                old_data = f.read()
            if old_data == content:
                print(f"[skip] {name}: content no change")
                os.remove(tmp_path)
            else:
                os.replace(tmp_path, target_path)
                print(f"[upd]  {name}: updated -> {target_path}")

    except Exception as e:
        print(f"[err]  {name} download failed: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# ============ 关键改动：转换与下载解耦，每次运行都执行 ============
cele_json = f"{DATA_DIR}/Celestrak-json.json"
cele_csv = f"{DATA_DIR}/Celestrak.csv"

if os.path.exists(cele_json):
    status, n = json_to_csv(cele_json, cele_csv, tag="Celestrak")
    if status == "updated":
        print(f"[csv]  Celestrak.csv regenerated from JSON ({n} records)")
    elif status == "no-change":
        print(f"[csv]  Celestrak.csv already up to date ({n} records)")
    else:
        print(f"[csv]  convert failed: {status}")
else:
    print("[csv]  Celestrak-json.json not found, skip csv conversion")

# 清理临时文件夹
if os.path.exists(TMP_DIR):
    try:
        os.rmdir(TMP_DIR)
    except Exception:
        pass

# 输出完整URL列表
print("\n" + "=" * 60)
print("[Generated file urls]")
for _, _, filenames in os.walk(DATA_DIR):
    for fn in filenames:
        print(f"{BASE_URL}/{DATA_DIR}/{fn}")
print("=" * 60)
