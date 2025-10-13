import os, requests
from PIL import Image
from io import BytesIO

# 🔑 Get a free API key from https://www.pexels.com/api/
PEXELS_API_KEY = "YTYdzNnRc5A5BKwpsvojanYMMGlldGBXWrGi9zm6sHugKIwyfIoIzCtkI
cities = {
    "austria": "Vienna",
    "belgium": "Brussels",
    "croatia": "Dubrovnik",
    "czech": "Prague",
    "denmark": "Copenhagen",
    "estonia": "Tallinn",
    "finland": "Helsinki",
    "france": "Paris",
    "germany": "Berlin",
    "greece": "Athens",
    "hungary": "Budapest",
    "iceland": "Reykjavik",
    "italy": "Rome",
    "latvia": "Riga",
    "lithuania": "Vilnius",
    "luxembourg": "Luxembourg City",
    "malta": "Valletta",
    "netherlands": "Amsterdam",
    "norway": "Oslo",
    "poland": "Warsaw",
    "portugal": "Lisbon",
    "slovakia": "Bratislava",
    "slovenia": "Ljubljana",
    "spain": "Madrid",
    "sweden": "Stockholm",
    "switzerland": "Zurich",
    "uk": "London",
    "ireland": "Dublin"
}

os.makedirs("static/images/cityscapes", exist_ok=True)
headers = {"Authorization": PEXELS_API_KEY}

for country, city in cities.items():
    query = f"{city} skyline dusk"
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    print(f"🔍 Searching: {query}")
    r = requests.get(url, headers=headers).json()

    if not r.get("photos"):
        print(f"⚠️ No results for {city}, skipping...")
        continue

    photo = r["photos"][0]["src"]["large2x"]
    img_data = requests.get(photo).content
    img = Image.open(BytesIO(img_data)).convert("RGB")
    img = img.resize((1200, 800))
    output_path = f"static/images/cityscapes/{country}_{city.lower().replace(' ', '')}.webp"
    img.save(output_path, "WEBP", quality=80)
    print(f"✅ Saved {output_path}")