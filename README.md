# Weather Data Extractor

Extract historical weather data from the Open-Meteo API for any location and time period. No API key required.

## Quick Start

### 1. Install Dependencies

```bash
cd weather_data_extractor
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Edit Configuration

Edit `config.json` with your settings:

```json
{
  "latitude": 49.208,              ← Your location
  "longitude": 10.628,                 ← Your location
  "start_date": "2023-10-03",         ← Start date
  "end_date": "2024-07-30",           ← End date
  "temporal_resolution": "daily",     ← "hourly", "daily", or "monthly"
  "output_file": "weather_data.csv",  ← Output filename
  "variable_groups": {
    "basic_weather": true,             ← Temperature, humidity, precipitation, etc.
    "solar_radiation": true,           ← Solar radiation data
    "soil": false                       ← Soil temperature and moisture
  }
}
```

### 3. Run

```bash
source venv/bin/activate
python weather_extractor.py --config config.json
```

That's it! Your CSV file will be created with all the requested weather data.

## Configuration Options

### Temporal Resolution

Choose one of three options by changing `"temporal_resolution"`:

- **`"hourly"`** - Original hourly data (one row per hour)
- **`"daily"`** - Daily averages with min/max (one row per day)
- **`"monthly"`** - Monthly averages with min/max/sum (one row per month)

### Variable Groups

Enable or disable groups with `true`/`false`:

- **`basic_weather`** (15 variables): Temperature, humidity, precipitation, wind, pressure, cloud cover
- **`solar_radiation`** (3 variables): Shortwave, direct, and diffuse solar radiation
- **`soil`** (3 variables): Soil temperature and moisture at different depths

### Available Variables

**Basic Weather:**
- `temperature_2m` - Air temperature at 2m
- `apparent_temperature` - Feels-like temperature
- `relative_humidity_2m` - Humidity percentage
- `dewpoint_2m` - Dew point temperature
- `precipitation` - Total precipitation (mm)
- `rain` - Rainfall only (mm)
- `snowfall` - Snowfall (mm)
- `wind_speed_10m` - Wind speed at 10m (m/s)
- `wind_direction_10m` - Wind direction (degrees)
- `pressure_msl` - Mean sea level pressure (hPa)
- `surface_pressure` - Surface pressure (hPa)
- `cloud_cover` - Total cloud cover (%)
- `cloud_cover_low` - Low cloud cover (%)
- `cloud_cover_mid` - Mid-level cloud cover (%)
- `cloud_cover_high` - High cloud cover (%)

**Solar Radiation:**
- `shortwave_radiation` - Total shortwave radiation (W/m²)
- `direct_radiation` - Direct solar radiation (W/m²)
- `diffuse_radiation` - Diffuse radiation (W/m²)

**Soil:**
- `soil_temperature_0cm` - Soil temperature at surface (°C)
- `soil_temperature_6cm` - Soil temperature at 6cm depth (°C)
- `soil_moisture_0_1cm` - Soil moisture content (%)

## Usage Examples

### List Available Variables

```bash
python weather_extractor.py --list-groups
```

### Extract Hourly Data for One Year

Edit `config.json`:
```json
{
  "latitude": 49.208,
  "longitude": 10.628,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "temporal_resolution": "hourly",
  "output_file": "weather_2024.csv",
  "variable_groups": {
    "basic_weather": true,
    "solar_radiation": false,
    "soil": false
  }
}
```

### Extract Daily Averages

Edit `config.json`:
```json
{
  "temporal_resolution": "daily"
}
```

### Extract Monthly Averages

Edit `config.json`:
```json
{
  "temporal_resolution": "monthly"
}
```

### Get All Variables

Edit `config.json`:
```json
{
  "variable_groups": {
    "basic_weather": true,
    "solar_radiation": true,
    "soil": true
  }
}
```

### Extract for Different Location

Edit `config.json`:
```json
{
  "latitude": 48.8566,    // Paris, France
  "longitude": 2.3522,
  "start_date": "2024-06-01",
  "end_date": "2024-08-31",
  "temporal_resolution": "daily"
}
```

## Output Format

### Hourly (`"temporal_resolution": "hourly"`)
```
time,temperature_2m,precipitation,...
2024-01-01 00:00:00,5.2,0.0,...
2024-01-01 01:00:00,4.8,0.0,...
```

### Daily (`"temporal_resolution": "daily"`)
```
time,temperature_2m_mean,temperature_2m_min,temperature_2m_max,precipitation_mean,...
2024-01-01,4.5,0.2,8.3,0.0,...
2024-01-02,6.1,2.1,10.5,2.4,...
```

### Monthly (`"temporal_resolution": "monthly"`)
```
time,temperature_2m_mean,temperature_2m_min,temperature_2m_max,temperature_2m_sum,precipitation_sum,...
2024-01-01,3.8,-5.2,12.1,1150.5,45.2,...
2024-02-01,5.2,-2.8,15.3,1650.8,32.1,...
```

## Data Source

**Open-Meteo Historical Weather API**
- Free to use
- No API key required
- Global coverage
- Historical data from 1940 to present
- ~11 km spatial resolution (1-2 km in Europe and US)

More information: https://open-meteo.com/en/docs/historical-weather-api

## Troubleshooting

**Problem**: No data returned  
**Solution**: Check that start_date < end_date and coordinates are valid

**Problem**: Timeout error  
**Solution**: Reduce date range or extract in smaller chunks

**Problem**: File not found  
**Solution**: Make sure virtual environment is activated: `source venv/bin/activate`

## Requirements

- Python 3.7+
- pandas
- requests
- numpy

## License

MIT License - Free to use for any purpose
