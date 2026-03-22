"""
generate_page.py — GitHub Pages Site Generator

Reads poem_output.txt and the latest weather data from SQLite,
then writes docs/index.html for GitHub Pages.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# ── Config (must match data_storage.py) ──────────────────────────────────────
CITY_CONFIG = {
    "aalborg": {"latitude": 57.048, "longitude": 9.9187},
    "beijing": {"latitude": 39.9042, "longitude": 116.4074},
    "nanning": {"latitude": 22.817, "longitude": 108.315},
}

CITY_DISPLAY = {
    "aalborg": "Aalborg 🇩🇰",
    "beijing": "Beijing 🇨🇳",
    "nanning":  "Nanning 🇨🇳",
}

CITY_FLAG = {
    "aalborg": "🇩🇰",
    "beijing": "🇨🇳",
    "nanning": "🇨🇳",
}


def get_table_name(city: str) -> str:
    return f"weather_{city.lower()}"


# ── Read poem ─────────────────────────────────────────────────────────────────
def read_poem(path: str = "poem_output.txt") -> str:
    if not os.path.exists(path):
        return "No poem generated yet."
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── Read latest weather from DB ───────────────────────────────────────────────
def fetch_weather_summary(db_path: str = "weather_data.db") -> list[dict]:
    """Returns a list of dicts, one per city, with display-ready values."""
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    rows = []

    if not os.path.exists(db_path):
        print(f"[WARNING] Database not found at {db_path}, skipping weather table.")
        return rows

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
                row = conn.execute(
                    f"SELECT * FROM {table} ORDER BY date DESC LIMIT 1"
                ).fetchone()
            if row:
                d = dict(row)
                rows.append({
                    "city":        CITY_DISPLAY[city],
                    "flag":        CITY_FLAG[city],
                    "date":        d.get("date", "—"),
                    "temp":        f"{d.get('temperature_2m', '—')} °C",
                    "rain_prob":   f"{d.get('precipitation_probability', '—')} %",
                    "rain":        f"{d.get('precipitation', '—')} mm",
                    "wind":        f"{d.get('wind_speed_10m', '—')} km/h",
                    "cloud":       f"{d.get('cloud_cover', '—')} %",
                    "humidity":    f"{d.get('relative_humidity_2m', '—')} %",
                })
        except sqlite3.OperationalError as e:
            print(f"[WARNING] Could not read {table}: {e}")

    conn.close()
    return rows


# ── Build weather cards HTML ──────────────────────────────────────────────────
def build_weather_cards(rows: list[dict]) -> str:
    if not rows:
        return "<p class='no-data'>No weather data available yet.</p>"

    cards = []
    for r in rows:
        cards.append(f"""
        <div class="card">
          <h3>{r['city']}</h3>
          <p class="date">{r['date']}</p>
          <table>
            <tr><td>🌡️ Temperature</td><td>{r['temp']}</td></tr>
            <tr><td>🌧️ Rain probability</td><td>{r['rain_prob']}</td></tr>
            <tr><td>💧 Precipitation</td><td>{r['rain']}</td></tr>
            <tr><td>💨 Wind speed</td><td>{r['wind']}</td></tr>
            <tr><td>☁️ Cloud cover</td><td>{r['cloud']}</td></tr>
            <tr><td>💦 Humidity</td><td>{r['humidity']}</td></tr>
          </table>
        </div>""")

    return "\n".join(cards)


# ── Build full HTML page ──────────────────────────────────────────────────────
def build_html(poem: str, weather_cards: str) -> str:
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Strip the header line that data_storage adds (====... lines) for cleaner display
    poem_lines = poem.splitlines()
    clean_lines = [l for l in poem_lines if not l.startswith("=") and "Generated at" not in l]
    poem_html = "\n".join(clean_lines).strip()
    # Preserve line breaks and split English / Chinese sections
    poem_html = poem_html.replace("\n\n", "</p><p>").replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Daily Weather Poem</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: "Segoe UI", system-ui, sans-serif;
      background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      color: #e8f4f8;
      min-height: 100vh;
      padding: 2rem 1rem;
    }}

    header {{
      text-align: center;
      margin-bottom: 3rem;
    }}

    header h1 {{
      font-size: 2.4rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }}

    header p.subtitle {{
      margin-top: 0.4rem;
      color: #90caf9;
      font-size: 0.95rem;
    }}

    /* ── Weather cards ─────────────────────────────────────────────────────── */
    .section-title {{
      text-align: center;
      font-size: 1.3rem;
      font-weight: 600;
      margin-bottom: 1.2rem;
      color: #90caf9;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}

    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1.2rem;
      max-width: 960px;
      margin: 0 auto 3.5rem;
    }}

    .card {{
      background: rgba(255,255,255,0.07);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 14px;
      padding: 1.4rem 1.6rem;
      backdrop-filter: blur(6px);
    }}

    .card h3 {{
      font-size: 1.25rem;
      margin-bottom: 0.3rem;
    }}

    .card .date {{
      font-size: 0.78rem;
      color: #90caf9;
      margin-bottom: 1rem;
    }}

    .card table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}

    .card table tr td {{
      padding: 0.3rem 0;
    }}

    .card table tr td:first-child {{
      color: #b0bec5;
      width: 60%;
    }}

    .card table tr td:last-child {{
      font-weight: 600;
      text-align: right;
    }}

    /* ── Poem block ────────────────────────────────────────────────────────── */
    .poem-wrapper {{
      max-width: 700px;
      margin: 0 auto 3rem;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 16px;
      padding: 2.2rem 2.4rem;
      backdrop-filter: blur(6px);
      line-height: 1.9;
      font-size: 1.05rem;
    }}

    .poem-wrapper p {{
      margin-bottom: 1.2rem;
    }}

    .poem-wrapper p:last-child {{
      margin-bottom: 0;
    }}

    footer {{
      text-align: center;
      font-size: 0.78rem;
      color: #78909c;
      margin-top: 2rem;
    }}

    .no-data {{
      text-align: center;
      color: #78909c;
      font-style: italic;
    }}
  </style>
</head>
<body>

  <header>
    <h1>🌦️ Daily Weather Poem</h1>
    <p class="subtitle">Aalborg · Beijing · Nanning — updated automatically every day</p>
  </header>

  <!-- Weather summary cards -->
  <p class="section-title">Tomorrow's Forecast</p>
  <div class="cards-grid">
    {weather_cards}
  </div>

  <!-- Bilingual poem -->
  <p class="section-title">Today's Poem</p>
  <div class="poem-wrapper">
    <p>{poem_html}</p>
  </div>

  <footer>
    Last generated: {generated_at} &nbsp;·&nbsp;
    Powered by <a href="https://open-meteo.com" style="color:#90caf9">Open-Meteo</a>
    &amp; <a href="https://groq.com" style="color:#90caf9">Groq</a>
  </footer>

</body>
</html>
"""


# ── Entry point ───────────────────────────────────────────────────────────────
def run_generate_page(
    poem_path: str = "poem_output.txt",
    db_path: str = "weather_data.db",
    output_path: str = "docs/index.html",
) -> None:
    print("[INFO] Reading poem...")
    poem = read_poem(poem_path)

    print("[INFO] Reading weather data from database...")
    rows = fetch_weather_summary(db_path)
    weather_cards = build_weather_cards(rows)

    print("[INFO] Building HTML page...")
    html = build_html(poem, weather_cards)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[INFO] GitHub Pages site written to: {output_path}")


if __name__ == "__main__":
    run_generate_page()