#!/usr/bin/env python3
"""
Weather Data Extractor
Extract historical weather data from Open-Meteo API for any location and time period.
"""

import requests
import pandas as pd
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class WeatherExtractor:
    """Extract weather data from Open-Meteo API with intelligent grouping"""
    
    # Variable groups that work together
    VARIABLE_GROUPS = {
        'basic_weather': [
            'temperature_2m',
            'apparent_temperature',
            'relative_humidity_2m',
            'dewpoint_2m',
            'precipitation',
            'rain',
            'snowfall',
            'wind_speed_10m',
            'wind_direction_10m',
            'pressure_msl',
            'surface_pressure',
            'cloud_cover',
            'cloud_cover_low',
            'cloud_cover_mid',
            'cloud_cover_high'
        ],
        'solar_radiation': [
            'shortwave_radiation',
            'direct_radiation',
            'diffuse_radiation'
        ],
        'soil': [
            'soil_temperature_0cm',
            'soil_temperature_6cm',
            'soil_moisture_0_1cm'
        ]
    }
    
    def __init__(self):
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"
    
    def extract_weather_data_multi(self,
                                  latitude: float,
                                  longitude: float,
                                  start_date: str,
                                  end_date: str,
                                  active_groups: Dict[str, bool],
                                  temporal_resolution: str = 'hourly',
                                  output_file: Optional[str] = None) -> pd.DataFrame:
        """
        Extract weather data by making multiple requests for compatible variable groups.
        
        Parameters:
        -----------
        latitude : float
            Latitude of the location
        longitude : float
            Longitude of the location
        start_date : str
            Start date in format 'YYYY-MM-DD'
        end_date : str
            End date in format 'YYYY-MM-DD'
        active_groups : dict
            Dictionary of group_name: bool indicating which groups to fetch
        temporal_resolution : str
            Resolution of data: 'hourly', 'daily', or 'monthly'
        output_file : str, optional
            Path to save CSV file
        
        Returns:
        --------
        pd.DataFrame
            Weather data with columns for each variable
        """
        # Validate dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start > end:
            raise ValueError("Start date must be before end date")
        
        all_dataframes = []
        
        # Fetch data for each active group
        for group_name, include in active_groups.items():
            if not include or group_name not in self.VARIABLE_GROUPS:
                continue
            
            variables = self.VARIABLE_GROUPS[group_name]
            
            print(f"\nFetching {group_name} variables...")
            print(f"   Variables: {', '.join(variables)}")
            
            try:
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": start_date,
                    "end_date": end_date,
                    "hourly": ",".join(variables),
                    "timezone": "auto"
                }
                
                response = requests.get(self.base_url, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                if 'hourly' not in data:
                    print(f"   WARNING: No data returned for {group_name}")
                    continue
                
                df = pd.DataFrame(data['hourly'])
                if 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'])
                
                all_dataframes.append(df)
                print(f"   Retrieved {len(df)} records")
                
            except Exception as e:
                print(f"   ERROR: Failed to fetch {group_name}: {e}")
                continue
        
        if not all_dataframes:
            raise ValueError("No data was successfully retrieved from any group")
        
        # Merge all dataframes on 'time'
        print("\nMerging data from all groups...")
        
        merged_df = all_dataframes[0]
        for df in all_dataframes[1:]:
            merged_df = pd.merge(merged_df, df, on='time', how='outer', suffixes=('', '_dup'))
            # Remove duplicate columns
            cols_to_drop = [col for col in merged_df.columns if col.endswith('_dup')]
            merged_df = merged_df.drop(columns=cols_to_drop)
        
        merged_df = merged_df.sort_values('time')
        
        # Apply temporal resampling
        if temporal_resolution == 'daily':
            merged_df = self._resample_to_daily(merged_df)
        elif temporal_resolution == 'monthly':
            merged_df = self._resample_to_monthly(merged_df)
        
        print(f"Total merged records: {len(merged_df)}")
        print(f"Total variables: {len(merged_df.columns) - 1}")  # -1 for time column
        print(f"Temporal resolution: {temporal_resolution}")
        
        # Save if output file specified
        if output_file:
            merged_df.to_csv(output_file, index=False)
            print(f"Data saved to: {output_file}")
        
        return merged_df
    
    def _resample_to_daily(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample hourly data to daily averages"""
        print("\nConverting to daily resolution...")
        
        df_resampled = df.copy()
        df_resampled['date'] = pd.to_datetime(df_resampled['time']).dt.date
        
        numeric_cols = [col for col in df_resampled.columns if col not in ['time', 'date']]
        
        # Group by date and aggregate
        df_daily = df_resampled.groupby('date')[numeric_cols].agg({
            col: ['mean', 'min', 'max'] for col in numeric_cols
        }).round(2)
        
        # Flatten column names
        df_daily.columns = [f"{col}_{stat}" for col, stat in df_daily.columns]
        df_daily = df_daily.reset_index()
        df_daily['time'] = pd.to_datetime(df_daily['date'])
        df_daily = df_daily.drop(columns=['date'])
        
        # Reorder columns to have time first
        cols = ['time'] + [c for c in df_daily.columns if c != 'time']
        df_daily = df_daily[cols]
        
        return df_daily
    
    def _resample_to_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample hourly data to monthly averages"""
        print("\nConverting to monthly resolution...")
        
        df_resampled = df.copy()
        df_resampled['date'] = pd.to_datetime(df_resampled['time'])
        df_resampled['year_month'] = df_resampled['date'].dt.to_period('M')
        
        numeric_cols = [col for col in df_resampled.columns if col not in ['time', 'date', 'year_month']]
        
        # Group by month and aggregate
        df_monthly = df_resampled.groupby('year_month')[numeric_cols].agg({
            col: ['mean', 'min', 'max', 'sum'] for col in numeric_cols
        }).round(2)
        
        # Flatten column names
        df_monthly.columns = [f"{col}_{stat}" for col, stat in df_monthly.columns]
        df_monthly = df_monthly.reset_index()
        df_monthly['time'] = pd.to_datetime(df_monthly['year_month'].astype(str))
        df_monthly = df_monthly.drop(columns=['year_month'])
        
        # Reorder columns to have time first
        cols = ['time'] + [c for c in df_monthly.columns if c != 'time']
        df_monthly = df_monthly[cols]
        
        return df_monthly
    
    def get_available_groups(self) -> Dict[str, List[str]]:
        """Get all available variable groups"""
        return self.VARIABLE_GROUPS
    
    def list_groups(self):
        """Print available variable groups"""
        print("\nAvailable Weather Variable Groups:")
        print("=" * 70)
        for group_name, variables in self.VARIABLE_GROUPS.items():
            print(f"\n{group_name.upper().replace('_', ' ')}:")
            for var in variables:
                print(f"  • {var}")
    
    def save_with_options(self,
                         df: pd.DataFrame,
                         output_file: str,
                         daily: bool = False,
                         format: str = 'csv') -> None:
        """
        Save data with various options.
        
        Parameters:
        -----------
        df : pd.DataFrame
            Data to save
        output_file : str
            Output file path
        daily : bool
            Convert to daily summary before saving
        format : str
            Output format: 'csv', 'excel', or 'json'
        """
        if daily:
            df = self.get_daily_summary(df)
        
        if format == 'csv':
            df.to_csv(output_file, index=False)
        elif format == 'excel':
            df.to_excel(output_file, index=False)
        elif format == 'json':
            df.to_json(output_file, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"Data saved to: {output_file}")
    
    def get_daily_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert hourly data to daily summary"""
        if 'time' not in df.columns:
            raise ValueError("Data must have a 'time' column")
        
        df['date'] = pd.to_datetime(df['time']).dt.date
        
        numeric_cols = [col for col in df.columns if col not in ['time', 'date']]
        
        daily_summary = df.groupby('date')[numeric_cols].agg(['mean', 'min', 'max', 'sum']).round(2)
        
        # Flatten column names
        daily_summary.columns = [f"{col}_{stat}" for col, stat in daily_summary.columns]
        daily_summary = daily_summary.reset_index()
        
        return daily_summary


def main():
    parser = argparse.ArgumentParser(
        description="Extract weather data from Open-Meteo API with flexible variable selection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use config file with yes/no switches
  python weather_extractor.py --config config.json
  
  # List available variable groups
  python weather_extractor.py --list-groups
        """
    )
    
    parser.add_argument('--config', type=str, help='Configuration JSON file with yes/no switches')
    parser.add_argument('--list-groups', action='store_true', help='List available variable groups')
    parser.add_argument('--daily', action='store_true', help='Convert to daily summary')
    
    args = parser.parse_args()
    
    extractor = WeatherExtractor()
    
    # List groups
    if args.list_groups:
        extractor.list_groups()
        return
    
    # Extract data using config
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        print("="*70)
        print("WEATHER DATA EXTRACTION")
        print("="*70)
        print(f"Location: ({config['latitude']}, {config['longitude']})")
        print(f"Date Range: {config['start_date']} to {config['end_date']}")
        print()
        
        # Build active_groups dict
        active_groups = {}
        for group in extractor.get_available_groups().keys():
            active_groups[group] = config.get('variable_groups', {}).get(group, False)
        
        # Get temporal resolution
        temporal_resolution = config.get('temporal_resolution', 'hourly')
        
        df = extractor.extract_weather_data_multi(
            latitude=config['latitude'],
            longitude=config['longitude'],
            start_date=config['start_date'],
            end_date=config['end_date'],
            active_groups=active_groups,
            temporal_resolution=temporal_resolution,
            output_file=config.get('output_file')
        )
        
        if args.daily:
            print("\nDaily Summary:")
            daily_df = extractor.get_daily_summary(df)
            print(daily_df.head())
            if config.get('output_file'):
                daily_file = config['output_file'].replace('.csv', '_daily.csv')
                daily_df.to_csv(daily_file, index=False)
                print(f"Daily summary saved to: {daily_file}")
        
        print("\nExtraction complete!")
    else:
        parser.error("Please provide a configuration file with --config")


if __name__ == "__main__":
    main()
