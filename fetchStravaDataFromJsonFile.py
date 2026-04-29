import json
import os


def generate_splits_from_streams(json_file_path):
    if not os.path.exists(json_file_path):
        print(f"Error: {json_file_path} not found.")
        return

    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract arrays
    dist_arr = data.get('distance', [])
    time_arr = data.get('time', [])
    alt_arr = data.get('altitude', [])
    hr_arr = data.get('heartrate', [])

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

    for i, current_dist in enumerate(dist_arr):
        # Trigger a split calculation every full 1000m
        if current_dist >= target_km:
            segment_time = time_arr[i] - time_arr[last_idx]
            segment_alt_diff = round(alt_arr[i] - alt_arr[last_idx])

            # HR for this specific segment
            segment_hrs = hr_arr[last_idx:i + 1]
            avg_hr_segment = round(sum(segment_hrs) / len(segment_hrs)) if segment_hrs else 0

            # Update global trackers
            total_time_seconds += segment_time
            all_hr_readings.extend(segment_hrs)

            summary.append({
                "km": len(summary) + 1,
                "tempo": format_pace(segment_time),
                "elevation_gain_mt": str(segment_alt_diff),
                "heart_rate_bpm": avg_hr_segment
            })

            # Update indices for the next kilometer
            last_idx = i
            target_km += 1000

    # Calculate dynamic header values
    total_km = len(summary)
    dynamic_pace = format_pace(total_time_seconds / total_km) if total_km > 0 else "0:00"
    dynamic_hr_avg = str(round(sum(all_hr_readings) / len(all_hr_readings))) if all_hr_readings else "0"

    # Final combined JSON output
    output_json = {
        "Date": "2026-03-21",
        "Type": "Interval",
        "Workout": f"{total_km}km Run",  # Filled dynamically
        "Pace": f"{dynamic_pace} / km",  # Filled dynamically
        "HR avg": dynamic_hr_avg,  # Filled dynamically
        "Feeling": "7/10",
        "Notes": "son 2 interval zorladı",
        "Summary": summary
    }

    output_filename = 'strava_dynamic_summary.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=4, ensure_ascii=False)

    print(f"✅ Created '{output_filename}'")
    print(f"Stats: {total_km}km | Avg Pace: {dynamic_pace} | Avg HR: {dynamic_hr_avg}")


# Execute using your provided file
generate_splits_from_streams('theLatestRunData.json')