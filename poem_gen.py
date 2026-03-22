import os
import sqlite3
from datetime import datetime, timedelta
from groq import Groq

# ── City config (must match data_storage.py) ─────────────────────────────────
CITY_CONFIG = {
    "aalborg": {"latitude": 57.048, "longitude": 9.9187},
    "beijing": {"latitude": 39.9042, "longitude": 116.4074},
    "nanning": {"latitude": 22.817, "longitude": 108.315},
}

CITY_DISPLAY = {
    "aalborg": "Aalborg 🇩🇰",
    "beijing": "Beijing 🇨🇳",
    "nanning": "Nanning 🇨🇳",
}


def get_table_name(city: str) -> str:
    return f"weather_{city.lower()}"


# ── Read tomorrow's weather from the database ─────────────────────────────────
def fetch_tomorrow_weather(db_path: str = "weather_data.db") -> dict:
    """
    Reads the next day's forecast for each city from SQLite.
    Falls back to the most recent record if tomorrow's data is unavailable.
    Returns: { city: { field: value, ... } }
    """
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    weather = {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    for city in CITY_CONFIG:
        table = get_table_name(city)
        try:
            row = conn.execute(
                f"SELECT * FROM {table} WHERE date LIKE ? ORDER BY date ASC LIMIT 1",
                (f"{tomorrow}%",),
            ).fetchone()

            if row is None:
                # Fallback: use the most recent available record
                row = conn.execute(
                    f"SELECT * FROM {table} ORDER BY date DESC LIMIT 1"
                ).fetchone()

            if row:
                weather[city] = dict(row)
            else:
                print(f"[WARNING] No data found for city: {city}")

        except sqlite3.OperationalError as e:
            print(f"[ERROR] Could not read table for {city}: {e}")

    conn.close()
    return weather


# ── Build the prompt for Groq ─────────────────────────────────────────────────
def build_prompt(weather: dict) -> str:
    if not weather:
        raise ValueError("No weather data available to build prompt.")

    lines = []
    best_city = None
    best_score = float("-inf")

    for city, data in weather.items():
        temp      = data.get("temperature_2m", "N/A")
        rain_prob = data.get("precipitation_probability", "N/A")
        rain      = data.get("precipitation", "N/A")
        wind      = data.get("wind_speed_10m", "N/A")
        cloud     = data.get("cloud_cover", "N/A")
        humidity  = data.get("relative_humidity_2m", "N/A")

        lines.append(
            f"- {CITY_DISPLAY.get(city, city)}: "
            f"temp={temp}°C, rain_prob={rain_prob}%, precipitation={rain}mm, "
            f"wind={wind}km/h, cloud={cloud}%, humidity={humidity}%"
        )

        # Simple liveability score: warm + dry + calm wind = higher score
        try:
            score = float(temp) - float(rain_prob) * 0.3 - float(wind) * 0.5
            if score > best_score:
                best_score = score
                best_city = CITY_DISPLAY.get(city, city)
        except (TypeError, ValueError):
            pass

    weather_block = "\n".join(lines)

    prompt = f"""
You are a creative bilingual poet. Below is tomorrow's weather forecast for three cities:

{weather_block}

Please write a short poem (8–16 lines) that:
1. Compares the weather in all three cities (Aalborg, Beijing, Nanning).
2. Describes the key differences vividly.
3. Suggests where it would be the nicest to be tomorrow (based on the data, the best city appears to be: {best_city}).
4. Is written FIRST in English, THEN in Chinese (Mandarin).

Format your response exactly like this:

🌍 English
<English poem here>

🌏 中文
<Chinese poem here>

Keep each version 8–12 lines. Be poetic, not just descriptive.
""".strip()

    return prompt


# ── Call the Groq API ─────────────────────────────────────────────────────────
def generate_poem(weather: dict, model: str = "llama-3.3-70b-versatile") -> str:
    """
    Generates a bilingual weather poem via the Groq API.
    Requires the GROQ_API_KEY environment variable.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is not set.")

    client = Groq(api_key=api_key)
    prompt = build_prompt(weather)

    print("[INFO] Calling Groq API to generate poem...")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()


# ── Save poem to file ─────────────────────────────────────────────────────────
def save_poem(poem: str, output_path: str = "poem_output.txt") -> None:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    header = f"{'='*60}\nWeather Poem — Generated at {timestamp}\n{'='*60}\n\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + poem + "\n")

    print(f"[INFO] Poem saved to: {output_path}")


# ── Pipeline entry point ──────────────────────────────────────────────────────
def run_poem_pipeline(db_path: str = "weather_data.db", output_path: str = "poem_output.txt") -> str:
    print("[INFO] Reading tomorrow's weather data from database...")
    weather = fetch_tomorrow_weather(db_path)

    if not weather:
        print("[WARNING] No weather data retrieved. Poem generation aborted.")
        return ""

    poem = generate_poem(weather)

    print("\n" + "=" * 60)
    print(poem)
    print("=" * 60 + "\n")

    save_poem(poem, output_path)
    return poem


if __name__ == "__main__":
    run_poem_pipeline()