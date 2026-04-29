import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import re
import time
import os


COOKIE_STRING = '_strava4_session=u4ubh7s78jvm3gjq6mvcgk2hr0jmj2ok;'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-GB;q=0.8,en;q=0.7',
    'Cookie': COOKIE_STRING,
    'Referer': 'https://www.strava.com/dashboard',
    'X-Requested-With': 'XMLHttpRequest'
}

URL = 'https://www.strava.com/athlete/training_activities?keywords=&sport_type=&tags=&commute=&private_activities=&trainer=&gear=&search_session_id=ed3e3324-58d6-4ebf-8209-b3397bbbcbdc&new_activity_only=false'

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def generate_splits_from_streams(json_file_path):
    log(f"Step 1: Starting split generation for file: {json_file_path}")

    if not os.path.exists(json_file_path):
        log(f"❌ Error: {json_file_path} not found.")
        return

    log("Step 2: Loading JSON data from file...")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        log("✅ JSON data loaded successfully.")
    except Exception as e:
        log(f"❌ Failed to load JSON: {str(e)}")
        return

    # Extract arrays
    log("Step 3: Extracting data streams (distance, time, altitude, heartrate)...")
    dist_arr = data.get('distance', [])
    time_arr = data.get('time', [])
    alt_arr = data.get('altitude', [])
    hr_arr = data.get('heartrate', [])
    log(f"📊 Stream lengths: Distance={len(dist_arr)}, Time={len(time_arr)}, HR={len(hr_arr)}")

    def format_pace(total_seconds):
        if total_seconds <= 0: return "0:00"
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    summary = []
    last_idx = 0
    target_km = 1000

    # Tracking for dynamic header fields
    total_time_seconds = 0
    all_hr_readings = []

    log("Step 4: Iterating through streams to calculate 1KM splits...")
    for i, current_dist in enumerate(dist_arr):
        # Trigger a split calculation every full 1000m
        if current_dist >= target_km:
            current_km = len(summary) + 1
            log(f"🔍 Calculating metrics for KM {current_km} (Distance reached: {current_dist:.2f}m)...")

            segment_time = time_arr[i] - time_arr[last_idx]
            segment_alt_diff = round(alt_arr[i] - alt_arr[last_idx])

            # HR for this specific segment
            segment_hrs = hr_arr[last_idx:i + 1]
            avg_hr_segment = round(sum(segment_hrs) / len(segment_hrs)) if segment_hrs else 0

            # Update global trackers
            total_time_seconds += segment_time
            all_hr_readings.extend(segment_hrs)

            summary.append({
                "km": current_km,
                "tempo": format_pace(segment_time),
                "elevation_gain_mt": str(segment_alt_diff),
                "heart_rate_bpm": avg_hr_segment
            })

            log(f"   ✨ KM {current_km} Complete: Pace={format_pace(segment_time)}, HR={avg_hr_segment}, Elev={segment_alt_diff}m")

            # Update indices for the next kilometer
            last_idx = i
            target_km += 1000

    log(f"Step 5: Processing final dynamic header values for {len(summary)} total kilometers...")
    total_km = len(summary)

    if total_km > 0:
        dynamic_pace = format_pace(total_time_seconds / total_km)
        dynamic_hr_avg = str(round(sum(all_hr_readings) / len(all_hr_readings))) if all_hr_readings else "0"
    else:
        log("⚠️ No full kilometers were completed in this run.")
        dynamic_pace = "0:00"
        dynamic_hr_avg = "0"

    # Final combined JSON output
    output_json = {
        "Date": "2026-03-21",
        "Type": "Interval",
        "Workout": f"{total_km}km Run",
        "Pace": f"{dynamic_pace} / km",
        "HR avg": dynamic_hr_avg,
        "Feeling": "7/10",
        "Notes": "son 2 interval zorladı",
        "Summary": summary
    }

    output_filename = 'strava_dynamic_summary.json'
    log(f"Step 6: Saving final JSON to '{output_filename}'...")

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False)

    log(f"🎉 SUCCESS: Processing complete.")
    log(f"Final Stats: Total Distance: {total_km}km | Avg Pace: {dynamic_pace} | Avg HR: {dynamic_hr_avg}")

def fetch_strava_data():
    session = requests.Session()
    session.headers.update(HEADERS)

    # STEP 1: DASHBOARD
    log("Step 1: Requesting Dashboard...")
    try:
        resp = session.get("https://www.strava.com/dashboard", timeout=10, verify=False)
        log(f"Status: {resp.status_code}")
    except Exception as e:
        log(f"Failed to connect: {e}")
        return

    activity_ids = re.findall(r'/activities/(\d+)', resp.text)
    print('activity_ids:',activity_ids)
    if not activity_ids:
        log("❌ No activity ID found. Check if Cookie string is still valid.")
        return

    latest_id = activity_ids[0]
    pace_url = f"https://www.strava.com/activities/{latest_id}/streams?stream_types%5B%5D=altitude&stream_types%5B%5D=heartrate&stream_types%5B%5D=distance&stream_types%5B%5D=time"

    log(f"✅ Target Activity: {latest_id}")

    # STEP 2: PACE ANALYSIS PAGE
    log(f"Step 2: Requesting Pace Analysis Page: {pace_url}")
    resp = session.get(pace_url, verify=False)
    log(f"Status: {resp.status_code}")

    log(f"Step 3: Saving run raw data as: theLatestRun_{latest_id}_Data.json")
    with open(f'theLatestRun_{latest_id}_Data.json', 'w') as f:
        json.dump(resp.json(), f, indent=2)
    log(f"Status: {resp.status_code}")

    log(f"Step 4: Creating summary run data and json file")
    generate_splits_from_streams(f'theLatestRun_{latest_id}_Data.json')

if __name__ == "__main__":
    session = requests.Session()
    session.headers.update(HEADERS)

    log("Step 1: Requesting Dashboard...")
    try:
        resp = session.get(URL, timeout=10, verify=False)
        log(f"Status: {resp.status_code}")
        try:
            data = resp.json()
            log("✅ JSON data loaded successfully.")
            if isinstance(data, list):
                print(json.dumps(data[:10], indent=4))
            elif isinstance(data, dict) and 'models' in data and isinstance(data['models'], list):
                print(json.dumps(data['models'][:10], indent=4))
            else:
                print(json.dumps(data, indent=4))
        except Exception as e:
            log(f"❌ Failed to load JSON: {str(e)}")

    except Exception as e:
        log(f"Failed to connect: {e}")
