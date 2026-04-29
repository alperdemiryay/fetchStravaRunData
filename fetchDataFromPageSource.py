from bs4 import BeautifulSoup
import requests
import json
import re
import time
import os

fetchTheLatestActivity = False
ifNoLatestActivityId = 18104321635
activityDate = "2026-04-14"
feeling = "7/10"
comments = "Tried to run 1.75km warmup @6:00 + 5x1km @5:00 pace with 90s joggings @7:30 + 1km cooldown @6:30"
runType = "Interval"

COOKIE_STRING = '_strava4_session=vt6o8aghbjcfl9ag74a0en73ovf5ia6f;'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-GB;q=0.8,en;q=0.7',
    'Cookie': COOKIE_STRING,
    'Referer': 'https://www.strava.com/dashboard',
    'X-Requested-With': 'XMLHttpRequest'
}

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def fetch_strava_data():
    session = requests.Session()
    session.headers.update(HEADERS)

    # STEP 1: DASHBOARD
    log("Step 1: Requesting Dashboard...")
    try:
        resp = session.get("https://www.strava.com/dashboard", timeout=10)
        log(f"Status: {resp.status_code}")
    except Exception as e:
        log(f"Failed to connect: {e}")
        return

    activity_ids = re.findall(r'/activities/(\d+)', resp.text)
    print('activity_ids:',activity_ids)
    if not activity_ids:
        log("❌ No activity ID found. Check if Cookie string is still valid.")
        return
    if fetchTheLatestActivity:
        latest_id = activity_ids[0]
    else:
        latest_id = ifNoLatestActivityId
    if runType == "Interval":
        pace_url = f"https://www.strava.com/activities/{latest_id}/lap_efforts"
    else:
        pace_url = f"https://www.strava.com/activities/{latest_id}/streams?stream_types%5B%5D=altitude&stream_types%5B%5D=heartrate&stream_types%5B%5D=distance&stream_types%5B%5D=time"

    log(f"✅ Target Activity: {latest_id}")

    # STEP 2: PACE ANALYSIS PAGE
    log(f"Step 2: Requesting Pace Analysis Page: {pace_url}")
    resp = session.get(pace_url)
    log(f"Status: {resp.status_code}")

    log(f"Step 3: Saving run raw data as: theLatestRun_{latest_id}_Data.json")
    with open(f'theLatestRun_{latest_id}_Data.json', 'w') as f:
        json.dump(resp.json(), f, indent=2)
    log(f"Status: {resp.status_code}")

    log(f"Step 4: Creating summary run data and json file")
    if runType == "Interval":
        generate_interval_summary(f'theLatestRun_{latest_id}_Data.json')
    else:
        generate_splits_from_streams(f'theLatestRun_{latest_id}_Data.json')

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
        "Date": activityDate,
        "Type": runType,
        "Workout": f"{total_km}km Run",
        "Pace": f"{dynamic_pace} / km",
        "HR avg": dynamic_hr_avg,
        "Feeling": feeling,
        "Strava No":json_file_path.split('_')[1],
        "Notes": comments,
        "Summary": summary
    }

    output_filename = f'{output_json["Date"]}_{output_json["Type"]}_{total_km}km_{output_json["Strava No"]}_summary.json'
    log(f"Step 6: Saving final JSON to '{output_filename}'...")

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False)

    log(f"🎉 SUCCESS: Processing complete.")
    log(f"Final Stats: Total Distance: {total_km}km | Avg Pace: {dynamic_pace} | Avg HR: {dynamic_hr_avg}")

def generate_interval_summary(json_file_path):
    """
    Processes lap-based JSON data, filtering out short transitions and
    calculating the total workout distance accurately (e.g., 8.8km).
    """
    if not os.path.exists(json_file_path):
        print(f"❌ Error: {json_file_path} not found.")
        return

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            laps = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load JSON: {str(e)}")
        return

    def format_pace_from_speed(speed_mps):
        if speed_mps <= 0: return "0:00"
        seconds_per_km = 1000 / speed_mps
        minutes = int(seconds_per_km // 60)
        seconds = int(seconds_per_km % 60)
        return f"{minutes}:{seconds:02d}"

    summary = []
    total_dist_m = 0
    total_time_s = 0
    hr_accumulator = 0

    for lap in laps:
        dist_m = lap.get('distance', 0)

        # Ignore splits lower than 200 meters
        if dist_m < 200:
            continue

        time_s = lap.get('moving_time', 0)
        avg_hr = lap.get('avg_hr', 0)
        avg_grade = lap.get('avg_grade', 0)
        avg_speed = lap.get('avg_speed', 0)

        # Calculate split km display (e.g., 0.8 or 2)
        km_val = round(dist_m / 1000, 1)
        km_display = int(km_val) if km_val == int(km_val) else km_val

        # Elevation calculation
        elev_gain = round(dist_m * (avg_grade / 100))

        # Accumulate metrics for header
        total_dist_m += dist_m
        total_time_s += time_s
        hr_accumulator += (avg_hr * time_s)

        summary.append({
            "km": km_display,
            "tempo": format_pace_from_speed(avg_speed),
            "elevation_gain_mt": str(elev_gain),
            "heart_rate_bpm": round(avg_hr)
        })

    # Corrected Header calculations for precise distance
    total_km_val = round(total_dist_m / 1000, 1)
    total_km_display = int(total_km_val) if total_km_val == int(total_km_val) else total_km_val

    avg_pace_raw = total_time_s / (total_dist_m / 1000) if total_dist_m > 0 else 0
    avg_pace_fmt = f"{int(avg_pace_raw // 60)}:{int(avg_pace_raw % 60):02d}"
    avg_hr_total = str(round(hr_accumulator / total_time_s)) if total_time_s > 0 else "0"

    # Construct final output JSON
    output_json = {
        "Date": activityDate,
        "Type": runType,
        "Workout": f"{total_km_display}km Run",
        "Pace": f"{avg_pace_fmt} / km",
        "HR avg": avg_hr_total,
        "Feeling": feeling,
        "Strava No": json_file_path.split('_')[1].split('.')[0],
        "Notes": comments,
        "Summary": summary
    }

    # Generate filename with precise distance
    out_name = f"{activityDate}_{runType}_{total_km_display}km_{output_json['Strava No']}_summary.json"

    with open(out_name, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False)

    print(f"🎉 SUCCESS: Generated {out_name} with Workout: {total_km_display}km Run")

if __name__ == "__main__":
    fetch_strava_data()