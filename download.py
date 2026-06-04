import urllib.request
import os

tasks = [
    {"name": "All", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv", "ext": "csv"},
    {"name": "Amateur", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=csv", "ext": "csv"},
    {"name": "Brightest", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=csv", "ext": "csv"},
    {"name": "Cubesat", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=cubesat&FORMAT=csv", "ext": "csv"},
    {"name": "Education", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=education&FORMAT=csv", "ext": "csv"},
    {"name": "Engineer", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=engineering&FORMAT=csv", "ext": "csv"},
    {"name": "Geostationary", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=geo&FORMAT=csv", "ext": "csv"},
    {"name": "Globalstar", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=globalstar&FORMAT=csv", "ext": "csv"},
    {"name": "GNSS", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=gnss&FORMAT=csv", "ext": "csv"},
    {"name": "Intelsat", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=intelsat&FORMAT=csv", "ext": "csv"},
    {"name": "Iridium", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=csv", "ext": "csv"},
    {"name": "Military", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=military&FORMAT=csv", "ext": "csv"},
    {"name": "New", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=last-30-days&FORMAT=csv", "ext": "csv"},
    {"name": "OneWeb", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=csv", "ext": "csv"},
    {"name": "Orbcomm", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=orbcomm&FORMAT=csv", "ext": "csv"},
    {"name": "Resource", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=csv", "ext": "csv"},
    {"name": "SatNOGS_Celestrak", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=satnogs&FORMAT=csv", "ext": "csv"},
    {"name": "Science", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=csv", "ext": "csv"},
    {"name": "Spire", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=spire&FORMAT=csv", "ext": "csv"},
    {"name": "Starlink", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=csv", "ext": "csv"},
    {"name": "Swarm", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=swarm&FORMAT=csv", "ext": "csv"},
    {"name": "Weather", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=csv", "ext": "csv"},
    {"name": "X-Comm", "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=x-comm&FORMAT=csv", "ext": "csv"},
    {"name": "Amsat", "url": "https://amsat.org/tle/current/nasabare.txt", "ext": "txt"},
    {"name": "Classified", "url": "https://www.mmccants.org/tles/classfd.zip", "ext": "zip"},
    {"name": "McCants", "url": "https://www.mmccants.org/tles/inttles.zip", "ext": "zip"},
    {"name": "R4UAB", "url": "https://r4uab.ru/satonline.txt", "ext": "txt"},
    {"name": "SatNOGS_API", "url": "https://db.satnogs.org/api/transmitters/?format=json&status=active", "ext": "json"}
]

os.makedirs("data", exist_ok=True)
os.makedirs(".tmp_download", exist_ok=True) # 临时下载目录

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
                print(f"⏭ {name}: Celestrak rate-limit, skip save")
                continue

        # 空内容跳过
        if not content.strip():
            print(f"⏭ {name}: empty response, skip")
            continue

        # 写入临时文件
        with open(tmp_path, "wb") as f:
            f.write(content)

        # 本地文件不存在 → 直接移入正式目录
        if not os.path.exists(target_path):
            os.replace(tmp_path, target_path)
            print(f"✅ {name}: new file saved -> {target_path}")
        else:
            # 对比新旧二进制，一致则不替换
            with open(target_path, "rb") as f:
                old_data = f.read()
            if old_data == content:
                print(f"⏭ {name}: content no change, skip overwrite")
                os.remove(tmp_path)
            else:
                os.replace(tmp_path, target_path)
                print(f"✅ {name}: file updated -> {target_path}")

    except Exception as e:
        print(f"❌ {name} download failed: {str(e)}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# 清理临时文件夹
if os.path.exists(".tmp_download"):
    try:
        os.rmdir(".tmp_download")
    except Exception:
        pass
