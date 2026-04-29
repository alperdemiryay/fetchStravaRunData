# AI Running Coach & Strava Data Fetcher

This project automates the process of extracting detailed running data from Strava and preparing it for an AI-powered running coach. It pulls raw activity streams, processes them into standardized summaries (like 1km splits or interval laps), and combines them with your personal athlete profile, goals, and training availability to get dynamic, personalized training plans from AI (like ChatGPT or Claude).

## 🏃‍♂️ Features

*   **Automated Data Extraction:** Logs into Strava (via session cookie) to fetch the latest activity directly from your dashboard.
*   **Detailed Split Generation:**
    *   **Normal Runs:** Extracts `distance`, `time`, `altitude`, and `heartrate` streams, calculating precise 1km splits, average paces, elevation gain, and average HR per kilometer.
    *   **Intervals:** Extracts lap efforts, automatically filtering out short recoveries/jogs (under 200m), and calculates speed and HR per interval lap.
*   **Structured JSON Output:** Saves the raw Strava data and generates a clean, standardized `summary.json` file for every workout (e.g., `2026-04-18_Race_21km_18167535516_summary.json`).
*   **AI Coach Integration:** Uses a set of configuration files and a predefined prompt (`prompt.txt`) to feed the run summary to an AI, asking it to analyze fatigue and update a 2-month training plan.

## 📁 Project Structure

### Data Fetching Scripts
*   **`fetchStravaDataFromDynamicUrl.py`**: The core scripts that connect to Strava using your session cookie, find the latest (or a specific) activity ID, fetch the streams/laps, and generate the summary JSON.
*   **`fetchStravaDataFromJsonFile.py`**: Alternative scripts to process already saved JSON/HTML data instead of hitting the live Strava servers.

### AI Coach Configuration Files
These files define you as an athlete and instruct the AI on how to coach you:
*   **`coach_config.txt`**: System instructions for the AI (e.g., "You are an elite endurance running coach... Athlete does kickboxing...").
*   **`profile.json`**: Your athlete profile (age, weight, height, max HR, etc.).
*   **`goals.json`**: Your running goals (e.g., target times for a marathon or 10k).
*   **`races.json`**: Your upcoming race calendar.
*   **`availability.json`**: Which days you can run and how much time you have.
*   **`prompt.txt`**: The actual prompt to copy/paste into ChatGPT/Claude along with the run summary and config files.


## 🚀 How to Use

1. **Update Strava Cookie:** 
   Open `fetchStravaDataFromDynamicUrl.py` (or your script of choice) and update the `COOKIE_STRING` variable with your current active `_strava4_session` cookie from your browser.
2. **Configure Run Variables:**
   Update the script variables to match your current run context (if doing it manually):
   ```python
   fetchTheLatestActivity = True # Set to False and provide an ID if you want a specific past run
   feeling = "6/10"              # Your RPE (Rate of Perceived Exertion)
   comments = "Elevation changes made the race a little bit hard..." 
   runType = "Race"              # "Interval", "Easy", "Tempo", "Race", etc.
   ```
3. **Run the Script:**
   ```bash
   python fetchStravaDataFromDynamicUrl.py
   ```
   This will output a raw data JSON (`theLatestRun_{ID}_Data.json`) and a summary JSON (e.g., `2026-04-18_Race_21km...summary.json`).
4. **Get AI Coaching:**
   Take the newly generated `summary.json` file, along with the contents of your config files (`profile.json`, `goals.json`, `coach_config.txt`), and paste them into your AI of choice using the text from `prompt.txt`.

## ⚠️ Requirements

*   `requests`
*   `beautifulsoup4`

```bash
pip install requests beautifulsoup4
```
