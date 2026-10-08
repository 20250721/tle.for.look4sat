import urllib.request
import os
import json
import csv

# ===================== 可自定义配置 =====================
BASE_URL = "https://tle2.486520.xyz"  # 修改这里为你的实际域名
# =======================================================

tasks = [
    {"name": "Amsat", "url": "https://amsat.org/tle/current/nasabare.txt", "ext": "txt"},
    {"name": "Mmccants", "url": "https://www.mmccants.org/tles/classfd.zip", "ext": "zip"},
    {"name": "R4UAB", "url": "https://r4uab.ru/satonline.txt", "ext": "txt"},
    {"name": "ARISS", "url": "https://live.ariss.org/iss.txt", "ext": "txt"},
    {"name": "Satnogs", "url": "https://db.satnogs.org/api/tle/?format=3le", "ext": "txt"},

    {"name": "SatNOGS-transmitters", "url": "https://db.satnogs.org/api/transmitters/?format=json&status=active", "ext": "json"},
    {"name": "R4UAB-transmitters", "url": "https://r4uab.ru/transmitters.json", "ext": "json"},
    {"name": "Celestrak-json", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json", "ext": "json"}
]

os.makedirs("data", exist_ok=True)
os.makedirs(".tmp_download", exist_ok=True)  # 临时下载目录


def json_to_csv(json_bytes, csv_target_path):
    """把 Celestrak GP 的 JSON 内容(字节)转换为 CSV 并写入 csv_target_path。
    - 列名取自首条记录的键顺序(与官方 CSV 表头一致)。
    - 若某条记录缺少某键则留空;若出现新键则追加到列末尾。
    返回写入的记录条数;解析失败返回 -1。"""
    try:
        records = json.loads(json_bytes.decode("utf-8", errors="ignore"))
    except Exception as e:
        print(f"    [json_to_csv] parse failed: {str(e)}")
        return -1

    if not isinstance(records, list) or len(records) == 0:
        print("    [json_to_csv] empty or unexpected json structure")
        return 0

    # 按首条记录顺序建立列名，并补充后续记录中出现的新键
    columns = list(records[0].keys())
    seen = set(columns)
    for rec in records:
        for k in rec.keys():
            if k not in seen:
                columns.append(k)
                seen.add(k)

    tmp_csv = csv_target_path + ".tmp"
    with open(tmp_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow({c: rec.get(c, "") for c in columns})

    os.replace(tmp_csv, csv_target_path)
    return len(records)


for task in tasks:
    name = task["name"]
    url = task["url"]
    ext = task["ext"]
    target_path = f"data/{name}.{ext}"
    tmp_path = f".tmp_download/{name}.{ext}"

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
                print(f"[skip] {name}: Celestrak rate-limit, skip save")
                continue

        # 空内容跳过
        if not content.strip():
            print(f"[skip] {name}: empty response, skip")
            continue

        # 写入临时文件
        with open(tmp_path, "wb") as f:
            f.write(content)

        # 本地文件不存在 -> 直接移入正式目录
        if not os.path.exists(target_path):
            os.replace(tmp_path, target_path)
            print(f"[new] {name}: new file saved -> {target_path}")
        else:
            # 对比新旧二进制，一致则不替换
            with open(target_path, "rb") as f:
                old_data = f.read()
            if old_data == content:
                print(f"[skip] {name}: content no change, skip overwrite")
                os.remove(tmp_path)
            else:
                os.replace(tmp_path, target_path)
                print(f"[upd] {name}: file updated -> {target_path}")

        # ===== 新增：Celestrak JSON -> CSV =====
        # 只要 Celestrak 的 JSON 正式文件存在，就同步生成一份 Celestrak.csv
        if name == "Celestrak-json" and os.path.exists(target_path):
            with open(target_path, "rb") as f:
                json_bytes = f.read()
            csv_target = "data/Celestrak.csv"
            n = json_to_csv(json_bytes, csv_target)
            if n >= 0:
                print(f"[csv] Celestrak.csv generated from json, {n} records -> {csv_target}")

    except Exception as e:
        print(f"[err] {name} download failed: {str(e)}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# 清理临时文件夹
if os.path.exists(".tmp_download"):
    try:
        os.rmdir(".tmp_download")
    except Exception:
        pass


# 输出完整URL列表
print("\n" + "=" * 60)
print("[Generated file urls]")
for _, _, filenames in os.walk("data"):
    for fn in filenames:
        print(f"{BASE_URL}/data/{fn}")
print("=" * 60)
