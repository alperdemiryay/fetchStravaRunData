import json
from bs4 import BeautifulSoup

# The HTML content provided
html_content = """
<table class="dense hoverable labs marginless run">
    <thead>
      <tr>
        <th>KM</th>
        <th>Tempo</th>
        <th>GAP</th>
        <th>İrtifa</th>
        <th>Nabız</th>
      </tr>
    </thead>
    <tbody>
        <tr class=""><td>1</td><td>5:56 /km</td><td>5:46 /km</td><td>3 mt</td><td>145 bpm</td></tr>
        <tr class=""><td>2</td><td>6:07 /km</td><td>5:54 /km</td><td>7 mt</td><td>147 bpm</td></tr>
        <tr class=""><td>3</td><td>5:50 /km</td><td>5:50 /km</td><td>-7 mt</td><td>151 bpm</td></tr>
        <tr class=""><td>4</td><td>6:07 /km</td><td>5:55 /km</td><td>5 mt</td><td>150 bpm</td></tr>
        <tr class=""><td>5</td><td>6:03 /km</td><td>5:59 /km</td><td>-1 mt</td><td>154 bpm</td></tr>
        <tr class=""><td>6</td><td>5:57 /km</td><td>5:57 /km</td><td>-6 mt</td><td>154 bpm</td></tr>
        <tr class=""><td>7</td><td>6:01 /km</td><td>5:47 /km</td><td>8 mt</td><td>156 bpm</td></tr>
        <tr class=""><td>8</td><td>5:57 /km</td><td>5:57 /km</td><td>-6 mt</td><td>156 bpm</td></tr>
        <tr class=""><td>9</td><td>5:56 /km</td><td>5:47 /km</td><td>3 mt</td><td>159 bpm</td></tr>
        <tr class=""><td>10</td><td>5:49 /km</td><td>5:44 /km</td><td>-1 mt</td><td>163 bpm</td></tr>
    </tbody>
</table>
"""


def parse_strava_table(html):
    soup = BeautifulSoup(html, 'html.parser')
    run_data = []

    # Locate the table body rows
    rows = soup.find('tbody').find_all('tr')

    for row in rows:
        cols = row.find_all('td')
        # We strip extra whitespace and units for a cleaner JSON
        split_info = {
            "km": int(cols[0].get_text(strip=True)),
            "tempo": cols[1].get_text(strip=True).replace(' /km', ''),
            "gap": cols[2].get_text(strip=True).replace(' /km', ''),
            "elevation_gain_mt": cols[3].get_text(strip=True).replace(' mt', ''),
            "heart_rate_bpm": int(cols[4].get_text(strip=True).replace(' bpm', ''))
        }
        run_data.append(split_info)

    return run_data


# Execute Parsing
data = parse_strava_table(html_content)

# Save to JSON file
with open('strava_run_summary.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print("Successfully saved run data to 'strava_run_summary.json'")