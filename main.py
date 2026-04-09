# main.py
# Plant Care Chatbot
# API  : OpenWeatherMap (weather only)
# Plants: fetched from database.py
# Logs : saved to plants.json

import requests, json, os
from datetime import datetime
from database import PLANTS, CLIMATE_PLANTS

WEATHER_KEY = "30dfcfed30b505375c93aac831910d15"  
DB_FILE     = "plants.json"

# -- JSON FILE -----------------------------------------------------------------

def load_db():
    if not os.path.exists(DB_FILE):
        print(f"  Error: '{DB_FILE}' not found.")
        print(f"  Please create it manually with this content:")
        print(f'  {{"searches": [], "plants": {{}}}}')
        exit()
    try:
        db = json.load(open(DB_FILE))
        if "plants" not in db or "searches" not in db:
            print("  Error: plants.json is missing required keys.")
            print('  Make sure it looks like: {"searches": [], "plants": {}}')
            exit()
        return db
    except json.JSONDecodeError:
        print("  Error: plants.json contains invalid JSON. Please fix or recreate it.")
        exit()

def save_db(db):
    json.dump(db, open(DB_FILE, "w"), indent=4)

def log_search(db, weather, search_type, query=""):
    db["searches"].append({
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "city":        weather["city"],
        "country":     weather["country"],
        "temp":        weather["temp"],
        "humidity":    weather["humidity"],
        "condition":   weather["condition"],
        "search_type": search_type,
        "query":       query
    })
    save_db(db)

def save_plant(db, key, plant):
    if key not in db["plants"]:
        db["plants"][key] = plant
        save_db(db)
        print("  [Saved to plants.json]")
    else:
        print("  [Loaded from plants.json]")

# -- WEATHER -------------------------------------------------------------------

def get_weather(city):
    r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                     params={"q": city, "appid": WEATHER_KEY, "units": "metric"})
    if r.status_code == 404:
        print(f"  City '{city}' not found. Please check the spelling."); return None
    if r.status_code != 200:
        print(f"  Weather error: {r.status_code}"); return None
    d = r.json()
    return {"city": d["name"], "country": d["sys"]["country"],
            "temp": d["main"]["temp"], "humidity": d["main"]["humidity"],
            "condition": d["weather"][0]["description"].capitalize()}

def show_weather(w):
    print(f"\n{'='*40}")
    print(f"  Live Weather: {w['city']}, {w['country']}")
    print(f"{'='*40}")
    print(f"  Temperature : {w['temp']}C")
    print(f"  Humidity    : {w['humidity']}%")
    print(f"  Condition   : {w['condition']}")
    print(f"{'='*40}")

# -- CLIMATE -------------------------------------------------------------------

def get_climate(w):
    t, h = w["temp"], w["humidity"]
    if t >= 30 and h >= 70: return "tropical"
    if t >= 20 and h >= 50: return "subtropical"
    if t >= 10:             return "temperate"
    if t < 10:              return "cold"
    return "dry"

# -- SUGGEST PLANTS ------------------------------------------------------------

def suggest_plants(weather, db):
    climate = get_climate(weather)
    print(f"\n  Climate: {climate.upper()}\n")

    for i, key in enumerate(CLIMATE_PLANTS[climate], 1):
        plant = PLANTS[key]
        save_plant(db, key, plant)
        print(f"  {i}. {plant['common_name']}  ({plant['category']})")
        print(f"     Watering : {plant['watering']}")
        print(f"     Sunlight : {plant['sunlight']}\n")

    log_search(db, weather, "suggestion", climate)

# -- CARE SCHEDULE -------------------------------------------------------------

def care_schedule(user_input, db):
    key = user_input.strip().lower()

    # Check plants.json first
    if key in db["plants"]:
        print(f"\n  Loaded '{user_input}' from plants.json.\n")
        show_care(db["plants"][key]); return

    # Check database.py
    if key in PLANTS:
        plant = PLANTS[key]
        save_plant(db, key, plant)
        log_search(db, {"city":"N/A","country":"N/A","temp":0,"humidity":0,"condition":"N/A"},
                   "care_schedule", key)
        show_care(plant); return

    # Not found
    print(f"\n  '{user_input}' not found in the database.")
    print(f"  Available plants: {', '.join(sorted(PLANTS.keys()))}")

def show_care(p):
    print(f"\n{'='*40}")
    print(f"  Care Guide: {p['common_name']}  ({p['category']})")
    print(f"{'='*40}")
    print(f"  Scientific  : {p['scientific_name']}")
    print(f"\n  About       : {p['description']}")
    print(f"\n  Watering    : {p['watering']}")
    print(f"  How often   : {p['watering_every']}")
    print(f"  Sunlight    : {p['sunlight']}")
    print(f"  Soil        : {p['soil']}")
    print(f"  Pruning     : {p['pruning']}")
    print(f"  Temperature : {p['temperature']}")
    print(f"  Maintenance : {p['maintenance']}")
    print(f"  Growth rate : {p['growth_rate']}")
    print(f"  Indoor      : {'Yes' if p['indoor'] else 'Indoors or outdoors'}")
    print("=" * 40)

# -- MAIN ----------------------------------------------------------------------

def main():
    print("\n" + "=" * 40)
    print("   PLANT CARE CHATBOT")
    print("=" * 40)

    db = load_db()
    print(f"\n  Database : {len(PLANTS)} plants available")
    print(f"  Saved    : {len(db['plants'])} plant(s) | {len(db['searches'])} search(es) logged")

    while True:
        city = input("\nEnter your city: ").strip()
        if not city: continue
        weather = get_weather(city)
        if weather: break

    show_weather(weather)

    while True:
        print("\n  1. Suggest plants for my weather")
        print("  2. Care schedule for a plant")
        print("  3. Exit")
        choice = input("\n  Enter 1, 2, or 3: ").strip()

        if choice == "1":
            suggest_plants(weather, db)
        elif choice == "2":
            plant = input("\n  Enter plant name (e.g. rose, tulsi, cactus): ").strip()
            if plant: care_schedule(plant, db)
        elif choice == "3":
            print("\n  Goodbye!\n"); break
        else:
            print("  Please enter 1, 2, or 3.")

main()