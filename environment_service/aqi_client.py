import os
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv


load_dotenv()


OPENAQ_URL = "https://api.openaq.org/v3"


# ============================================================
# TIME WINDOW
# ============================================================

from datetime import datetime, timedelta


def get_recent_time_window(latest_data_time: str) -> tuple[str, str]:

    latest_time = datetime.fromisoformat(latest_data_time)

    start_time = latest_time - timedelta(hours=24)

    return (
        start_time.isoformat(),
        latest_time.isoformat()
    )


# ============================================================
# STATION DATA
# ============================================================

def get_station_latest(location_id: int) -> dict:
    """
    Get the latest measurements available at a station.
    """

    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        raise ValueError("OPENAQ_API_KEY is not set")

    url = f"{OPENAQ_URL}/locations/{location_id}/latest"

    headers = {
        "X-API-Key": api_key
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_station_sensors(location_id: int) -> dict:
    """
    Get all sensors belonging to an OpenAQ station.
    """

    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        raise ValueError("OPENAQ_API_KEY is not set")

    url = f"{OPENAQ_URL}/locations/{location_id}/sensors"

    headers = {
        "X-API-Key": api_key
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# FIND NEAREST AIR-QUALITY STATION
# ============================================================

def find_nearest_station(
    latitude: float,
    longitude: float
) -> dict:
    """
    Find the nearest OpenAQ air-quality monitoring station.
    """

    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        raise ValueError("OPENAQ_API_KEY is not set")

    url = f"{OPENAQ_URL}/locations"

    headers = {
        "X-API-Key": api_key
    }

    params = {
        "coordinates": f"{latitude},{longitude}",
        "radius": 25000,
        "limit": 100
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data["results"]:
        raise ValueError(
            "No air quality station found nearby"
        )

    # Sort by distance so the closest station is selected.
    stations = sorted(
        data["results"],
        key=lambda station: (
            station["distance"]
            if station["distance"] is not None
            else float("inf")
        )
    )

    station = stations[0]

    distance = station["distance"]

    return {
        "location_id": station["id"],
        "name": station["name"],
        "latitude": station["coordinates"]["latitude"],
        "longitude": station["coordinates"]["longitude"],
        "distance_km": (
            round(distance / 1000, 2)
            if distance is not None
            else None
        )
    }


# ============================================================
# SELECT CLEAN / CURRENT POLLUTANT SENSORS
# ============================================================

def get_clean_air_quality(
    location_id: int
) -> dict:
    """
    Select the most recently updated sensor for each
    pollutant required by the AQI calculation.
    """

    sensor_data = get_station_sensors(location_id)

    air_quality = {}

    required_pollutants = {
        "pm10",
        "pm25",
        "no2",
        "so2",
        "o3",
        "co"
    }

    for sensor in sensor_data["results"]:

        parameter = sensor["parameter"]["name"]

        if parameter not in required_pollutants:
            continue

        last_updated = sensor["datetimeLast"]["local"]

        # Keep the most recently updated sensor
        # for each pollutant.
        if (
            parameter not in air_quality
            or last_updated
            > air_quality[parameter]["last_updated"]
        ):

            air_quality[parameter] = {
                "sensor_id": sensor["id"],
                "unit": sensor["parameter"]["units"],
                "last_updated": last_updated
            }

    return air_quality


# ============================================================
# HOURLY SENSOR DATA
# ============================================================

def get_hourly_data(
    sensor_id: int,
    datetime_from: str,
    datetime_to: str
) -> dict:
    """
    Get hourly average measurements for one sensor.
    """

    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        raise ValueError("OPENAQ_API_KEY is not set")

    url = f"{OPENAQ_URL}/sensors/{sensor_id}/hours"

    headers = {
        "X-API-Key": api_key
    }

    params = {
        "datetime_from": datetime_from,
        "datetime_to": datetime_to,
        "limit": 100
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    cleaned_results = []

    for item in data["results"]:

        cleaned_results.append({
            "value": item["value"],
            "unit": item["parameter"]["units"],
            "parameter": item["parameter"]["name"],
            "datetime_from": item["period"]["datetimeFrom"]["local"],
            "datetime_to": item["period"]["datetimeTo"]["local"],
            "coverage": item["coverage"]["percentCoverage"]
        })

    return {
        "sensor_id": sensor_id,
        "records_found": data["meta"]["found"],
        "data": cleaned_results
    }


# ============================================================
# GET HOURLY DATA FOR ALL POLLUTANTS
# ============================================================

def get_all_hourly_air_quality(
    location_id: int,
    datetime_from: str,
    datetime_to: str
) -> dict:
    """
    Get hourly data for all available AQI pollutants
    at a monitoring station.
    """

    sensors = get_clean_air_quality(location_id)

    air_quality = {}

    for parameter, sensor_info in sensors.items():

        hourly_data = get_hourly_data(
            sensor_info["sensor_id"],
            datetime_from,
            datetime_to
        )

        air_quality[parameter] = {
            "sensor_id": sensor_info["sensor_id"],
            "unit": sensor_info["unit"],
            "records_found": hourly_data["records_found"],
            "data": hourly_data["data"]
        }

    return air_quality


# ============================================================
# DATA QUALITY
# ============================================================

def check_data_quality(
    air_quality: dict
) -> dict:
    """
    Check whether enough hourly records exist for each pollutant.
    """

    required_hours = {
        "pm10": 24,
        "pm25": 24,
        "no2": 24,
        "so2": 24,
        "o3": 8,
        "co": 8
    }

    quality = {}

    for pollutant, info in air_quality.items():

        records = info["records_found"]

        expected = required_hours.get(
            pollutant,
            24
        )

        if records >= expected:
            status = "complete"

        elif records >= 16:
            status = "partial"

        elif records > 0:
            status = "insufficient_data"

        else:
            status = "missing"

        quality[pollutant] = {
            "records_found": records,
            "expected_records": expected,
            "status": status,
            "usable": records >= 16
        }

    return quality


# ============================================================
# AVERAGE
# ============================================================

def calculate_average(
    records: list
) -> float | None:

    values = []

    for record in records:

        if record["value"] is not None:
            values.append(record["value"])

    if not values:
        return None

    return sum(values) / len(values)


# ============================================================
# POLLUTANT AVERAGE
# ============================================================

def calculate_pollutant_average(
    pollutant: str,
    records: list
) -> dict:

    averaging_periods = {
        "pm10": 24,
        "pm25": 24,
        "no2": 24,
        "so2": 24,
        "o3": 8,
        "co": 8
    }

    if pollutant not in averaging_periods:
        raise ValueError(
            f"Unsupported pollutant: {pollutant}"
        )

    required_hours = averaging_periods[pollutant]

    valid_records = [
        record
        for record in records
        if record["value"] is not None
    ]

    records_found = len(valid_records)

    # CPCB requires at least 16 hours
    # for calculating a pollutant sub-index.
    if records_found < 16:

        return {
            "pollutant": pollutant,
            "required_hours": required_hours,
            "records_found": records_found,
            "status": "insufficient_data",
            "average": None
        }

    # Use the most recent required number
    # of records.
    values = [
        record["value"]
        for record in valid_records[-required_hours:]
    ]

    average = sum(values) / len(values)

    if records_found < required_hours:
        status = "partial"
    else:
        status = "complete"

    return {
        "pollutant": pollutant,
        "required_hours": required_hours,
        "records_found": records_found,
        "status": status,
        "average": round(average, 4)
    }


# ============================================================
# CPCB AQI BREAKPOINTS
# ============================================================

AQI_BREAKPOINTS = {

    "pm25": {
        "concentration": [
            0,
            30,
            60,
            90,
            120,
            250
        ],
        "aqi": [
            0,
            50,
            100,
            200,
            300,
            400
        ]
    },

    "pm10": {
        "concentration": [
            0,
            50,
            100,
            250,
            350,
            430
        ],
        "aqi": [
            0,
            50,
            100,
            200,
            300,
            400
        ]
    },

    "no2": {
        "concentration": [
            0,
            40,
            80,
            180,
            280,
            400
        ],
        "aqi": [
            0,
            50,
            100,
            200,
            300,
            400
        ]
    },

    "so2": {
        "concentration": [
            0,
            40,
            80,
            380,
            800,
            1600
        ],
        "aqi": [
            0,
            50,
            100,
            200,
            300,
            400
        ]
    },

    "o3": {
        "concentration": [
            0,
            50,
            100,
            168,
            208,
            748
        ],
        "aqi": [
            0,
            50,
            100,
            200,
            300,
            400
        ]
    },

    "co": {
        "concentration": [
            0,
            1.0,
            2.0,
            10,
            17,
            34
        ],
        "aqi": [
            0,
            50,
            100,
            200,
            300,
            400
        ]
    }
}


# ============================================================
# CALCULATE POLLUTANT SUB-INDEX
# ============================================================

def calculate_sub_index(
    pollutant: str,
    concentration: float
) -> int:

    if pollutant not in AQI_BREAKPOINTS:
        raise ValueError(
            f"Unsupported pollutant: {pollutant}"
        )

    breakpoints = AQI_BREAKPOINTS[pollutant]

    concentration_breakpoints = (
        breakpoints["concentration"]
    )

    aqi_breakpoints = breakpoints["aqi"]

    for i in range(
        len(concentration_breakpoints) - 1
    ):

        c_low = concentration_breakpoints[i]
        c_high = concentration_breakpoints[i + 1]

        if c_low <= concentration <= c_high:

            i_low = aqi_breakpoints[i]
            i_high = aqi_breakpoints[i + 1]

            sub_index = (
                (
                    (i_high - i_low)
                    / (c_high - c_low)
                )
                * (concentration - c_low)
                + i_low
            )

            return round(sub_index)

    # Above the highest defined breakpoint.
    if concentration > concentration_breakpoints[-1]:
        return 500

    return 0


# ============================================================
# UNIT CONVERSION
# ============================================================

def convert_to_cpcb_unit(
    pollutant: str,
    value: float,
    unit: str
) -> float:

    if pollutant == "pm10":

        if unit == "µg/m³":
            return value

    elif pollutant == "pm25":

        if unit == "µg/m³":
            return value

    elif pollutant == "no2":

        if unit == "µg/m³":
            return value

        elif unit == "ppb":
            return value * 1.88

    elif pollutant == "so2":

        if unit == "µg/m³":
            return value

        elif unit == "ppb":
            return value * 2.62

    elif pollutant == "o3":

        if unit == "µg/m³":
            return value

        elif unit == "ppb":
            return value * 1.96

    elif pollutant == "co":

        if unit == "mg/m³":
            return value

        elif unit == "µg/m³":
            return value / 1000

        elif unit == "ppb":
            return (value * 1.145) / 1000

    raise ValueError(
        f"Unsupported unit '{unit}' "
        f"for pollutant '{pollutant}'"
    )


# ============================================================
# CONVERT HOURLY RECORDS
# ============================================================

def convert_hourly_records_to_cpcb_unit(
    pollutant: str,
    records: list
) -> list:

    converted_records = []

    for record in records:

        if record["value"] is None:
            continue

        converted_value = convert_to_cpcb_unit(
            pollutant,
            record["value"],
            record["unit"]
        )

        converted_records.append({
            "value": converted_value,
            "unit": (
                "mg/m³"
                if pollutant == "co"
                else "µg/m³"
            ),
            "parameter": pollutant,
            "datetime_from": record["datetime_from"],
            "datetime_to": record["datetime_to"],
            "coverage": record["coverage"]
        })

    return converted_records


# ============================================================
# CALCULATE ALL POLLUTANT SUB-INDICES
# ============================================================

def calculate_all_sub_indices(
    air_quality_data: dict
) -> dict:

    results = {}

    for pollutant, info in air_quality_data.items():

        converted_records = (
            convert_hourly_records_to_cpcb_unit(
                pollutant,
                info["data"]
            )
        )

        average_result = (
            calculate_pollutant_average(
                pollutant,
                converted_records
            )
        )

        # Not enough data for this pollutant.
        if average_result["average"] is None:

            results[pollutant] = {
                "status": average_result["status"],
                "records_found": average_result["records_found"],
                "required_hours": average_result["required_hours"],
                "average": None,
                "sub_index": None
            }

            continue

        sub_index = calculate_sub_index(
            pollutant,
            average_result["average"]
        )

        results[pollutant] = {
            "average": average_result["average"],
            "unit": converted_records[0]["unit"],
            "records_found": average_result["records_found"],
            "required_hours": average_result["required_hours"],
            "status": average_result["status"],
            "sub_index": sub_index
        }

    return results


# ============================================================
# OVERALL AQI
# ============================================================

def calculate_overall_aqi(
    sub_indices: dict
) -> dict:

    valid_indices = {}

    for pollutant, data in sub_indices.items():

        if data["sub_index"] is not None:
            valid_indices[pollutant] = data["sub_index"]

    # CPCB requires:
    # 1. At least 3 pollutants
    # 2. At least one of PM2.5 or PM10

    has_required_pm = (
        "pm25" in valid_indices
        or "pm10" in valid_indices
    )

    if (
        len(valid_indices) < 3
        or not has_required_pm
    ):

        return {
            "aqi": None,
            "category": "insufficient_data",
            "dominant_pollutant": None
        }

    # The highest pollutant sub-index
    # becomes the overall AQI.
    dominant_pollutant = max(
        valid_indices,
        key=valid_indices.get
    )

    aqi = valid_indices[dominant_pollutant]

    if aqi <= 50:
        category = "Good"

    elif aqi <= 100:
        category = "Satisfactory"

    elif aqi <= 200:
        category = "Moderately Polluted"

    elif aqi <= 300:
        category = "Poor"

    elif aqi <= 400:
        category = "Very Poor"

    else:
        category = "Severe"

    return {
        "aqi": aqi,
        "category": category,
        "dominant_pollutant": dominant_pollutant
    }


# ============================================================
# COMPLETE AQI PIPELINE
# ============================================================
def get_aqi_by_coordinates(
    latitude: float,
    longitude: float
) -> dict:

    # 1. Find nearest station
    station = find_nearest_station(
        latitude,
        longitude
    )

    # 2. Get the station's sensors
    sensors = get_clean_air_quality(
        station["location_id"]
    )

    # 3. Find the latest timestamp available
    latest_data_time = get_station_data_time(
        sensors
    )

    if latest_data_time is None:
        return {
            "location": {
                "latitude": latitude,
                "longitude": longitude
            },
            "station": station,
            "aqi": {
                "aqi": None,
                "category": "insufficient_data",
                "dominant_pollutant": None
            },
            "message": "No air quality data available"
        }

    # 4. Build a 24-hour window around the
    #    station's actual latest available data
    datetime_from, datetime_to = get_recent_time_window(
        latest_data_time
    )

    # 5. Get hourly pollutant data
    air_quality_data = get_all_hourly_air_quality(
        station["location_id"],
        datetime_from,
        datetime_to
    )

    # 6. Calculate pollutant sub-indices
    sub_indices = calculate_all_sub_indices(
        air_quality_data
    )

    # 7. Calculate overall AQI
    overall_aqi = calculate_overall_aqi(
        sub_indices
    )

    return {
        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "time_window": {
            "from": datetime_from,
            "to": datetime_to
        },

        "station": station,

        "aqi": overall_aqi,

        "pollutants": sub_indices
    }

from datetime import datetime, timezone


def get_station_data_time(sensors: dict) -> str | None:

    timestamps = []

    for sensor in sensors.values():

        last_updated = sensor.get("last_updated")

        if last_updated:
            timestamps.append(last_updated)

    if not timestamps:
        return None

    return max(timestamps)