import datetime
import os
from skyfield.api import Loader
import astropy.units as u
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time

class SpaceTrackerEngine(object):
    def __init__(self, cache_hours: int = 3):
        self.data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.loader = Loader(self.data_dir, verbose=False)
        self.ts = self.loader.timescale()
        self.cache_hours = cache_hours
        
        self.satellite_mappings = {
            "iss": "ISS (ZARYA)",
            "hubble": "HST",
            "noaa": "NOAA 19",
            "starlink": "STARLINK"
        }
        
        self.satellites_cache = {}
        self._initialize_database()

    def _initialize_database(self):
        urls = {
            "stations": "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
            "science": "https://celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle",
            "weather": "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
            "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"
        }

        for group, url in urls.items():
            try:
                filename = f"{group}.tle"
                filepath = os.path.join(self.data_dir, filename)
                
                force_reload = True
                if os.path.exists(filepath):
                    days_limit = float(self.cache_hours) / 24.0
                    if self.loader.days_old(filename) < days_limit:
                        force_reload = False
                
                sats_list = self.loader.tle_file(url, filename=filename, reload=force_reload)
                
                for sat in list(sats_list):
                    if sat and hasattr(sat, 'name') and sat.name:
                        self.satellites_cache[str(sat.name).strip()] = sat
                        
            except Exception as e:
                print(f"?? Error parsing group '{group}': {str(e)}")

    def get_satellite_position(self, satellite_slug: str, obs_lat: float = None, obs_lon: float = None, obs_alt_m: float = 0.0):
        slug = str(satellite_slug).lower()
        if slug not in self.satellite_mappings:
            raise ValueError(f"Satellite '{satellite_slug}' not supported.")
            
        target_name = self.satellite_mappings[slug]
        satellite = None
        
        for name in list(self.satellites_cache.keys()):
            if target_name in name:
                satellite = self.satellites_cache[name]
                target_name = name
                break
                
        if not satellite:
            raise ValueError(f"TLE data for '{target_name}' not found in cache.")

        now = self.ts.now()
        geocentric = satellite.at(now)
        subpoint = geocentric.subpoint()
        
        velocity_vector = geocentric.velocity.km_per_s
        speed_km_s = (velocity_vector[0]**2 + velocity_vector[1]**2 + velocity_vector[2]**2)**0.5
        speed_km_h = speed_km_s * 3600

        # Base telemetry response
        sat_lat = subpoint.latitude.degrees
        sat_lon = subpoint.longitude.degrees
        sat_alt = subpoint.elevation.km

        response = {
            "satellite_name": str(target_name),
            "latitude": round(sat_lat, 4),
            "longitude": round(sat_lon, 4),
            "altitude_km": round(sat_alt, 2),
            "velocity_km_h": round(speed_km_h, 2),
            "timestamp": datetime.datetime.now().isoformat(),
            "astronomy_data": None
        }

        # If observer coordinates are provided, perform advanced Astropy computations
        if obs_lat is not None and obs_lon is not None:
            # 1. Define time context for Astropy
            astro_time = Time(datetime.datetime.utcnow())
            
            # 2. Establish ground observer frame
            observer_location = EarthLocation(lat=obs_lat*u.deg, lon=obs_lon*u.deg, height=obs_alt_m*u.m)
            altaz_frame = AltAz(obstime=astro_time, location=observer_location)
            
            # 3. Establish satellite sky position point coordinate
            sat_coord = SkyCoord(
                lon=sat_lon*u.deg, 
                lat=sat_lat*u.deg, 
                distance=(6371.0 + sat_alt)*u.km, 
                frame='geocentrictrueecliptic'
            )
            
            # 4. Transform coordinate frames to find local horizon look angles
            local_look_angles = sat_coord.transform_to(altaz_frame)
            icrs_sky_coordinates = sat_coord.transform_to('icrs')

            response["astronomy_data"] = {
                "observer_latitude": obs_lat,
                "observer_longitude": obs_lon,
                "local_altitude_deg": round(float(local_look_angles.alt.degree), 2),
                "local_azimuth_deg": round(float(local_look_angles.az.degree), 2),
                "right_ascension_hours": round(float(icrs_sky_coordinates.ra.hour), 4),
                "declination_degrees": round(float(icrs_sky_coordinates.dec.degree), 4)
            }

        return response

class ISSTracker(SpaceTrackerEngine):
    def get_current_position(self):
        return self.get_satellite_position("iss")
