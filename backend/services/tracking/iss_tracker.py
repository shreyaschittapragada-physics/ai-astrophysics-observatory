from skyfield.api import load, EarthSatellite
import requests

# ==========================
# FETCH ISS TLE DATA (Updated API URL)
# ==========================
# We explicitly append the query parameters to force the TLE format
url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle"

response = requests.get(url)
lines = response.text.splitlines()

# Find ISS lines
name, line1, line2 = None, None, None
for i, line in enumerate(lines):
    if "ISS (ZARYA)" in line:
        name = lines[i].strip()
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()
        break

if not name:
    raise ValueError("Could not find ISS data in the TLE file.")

# ==========================
# LOAD SATELLITE
# ==========================
ts = load.timescale()

# Build the satellite object directly from the TLE strings
satellite = EarthSatellite(line1, line2, name, ts)

# Current time
t = ts.now()

# Get satellite position
geocentric = satellite.at(t)
subpoint = geocentric.subpoint()

# ==========================
# OUTPUT
# ==========================
print("\n🛰 ISS CURRENT POSITION")
print("------------------------")
print("Latitude :", subpoint.latitude)
print("Longitude:", subpoint.longitude)
print("Altitude :", round(subpoint.elevation.km, 2), "km")