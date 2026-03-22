"""
main.py — Pipeline Entry Point

Run order:
  1. data_storage.py fetches and stores weather data into SQLite (run separately or before this)
  2. poem_generator.py reads the database and generates a bilingual poem via Groq API
  3. Poem is printed to stdout and saved to poem_output.txt
"""

from poem_gen import run_poem_pipeline


def main():
    print("=" * 60)
    print("Weather Poem Pipeline — Starting")
    print("=" * 60)

    run_poem_pipeline()

    print("Pipeline complete.")


if __name__ == "__main__":
    main()