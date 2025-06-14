import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt

def solar_position(latitude, longitude, dt, tz):
    """
    Calculate solar elevation and azimuth angles for given location and time
    Returns: (elevation, azimuth) in degrees
    """
    # Convert to UTC
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    
    local_tz = pytz.timezone(tz)
    if dt.tzinfo is None:
        dt = local_tz.localize(dt)
    utc_dt = dt.astimezone(pytz.UTC)
    
    # Day of year
    day_of_year = utc_dt.timetuple().tm_yday
    
    # Solar declination angle (degrees)
    declination = 23.45 * np.sin(np.radians(360 * (284 + day_of_year) / 365))
    
    # Hour angle
    hour_of_day = utc_dt.hour + utc_dt.minute/60 + utc_dt.second/3600
    solar_time = hour_of_day + longitude/15  # Rough solar time approximation
    hour_angle = 15 * (solar_time - 12)
    
    # Convert to radians
    lat_rad = np.radians(latitude)
    dec_rad = np.radians(declination)
    hour_rad = np.radians(hour_angle)
    
    # Solar elevation angle
    elevation = np.arcsin(
        np.sin(lat_rad) * np.sin(dec_rad) + 
        np.cos(lat_rad) * np.cos(dec_rad) * np.cos(hour_rad)
    )
    
    # Solar azimuth angle
    azimuth = np.arccos(
        (np.sin(dec_rad) * np.cos(lat_rad) - 
         np.cos(dec_rad) * np.sin(lat_rad) * np.cos(hour_rad)) / 
        np.cos(elevation)
    )
    
    # Adjust azimuth for afternoon (solar time > 12)
    if solar_time > 12:
        azimuth = 2 * np.pi - azimuth
    
    return np.degrees(elevation), np.degrees(azimuth)

def calculate_irradiance_factor(panel_tilt_from_vertical, panel_azimuth, sun_elevation, sun_azimuth):
    """
    Calculate the cosine of the angle between panel normal and sun rays
    panel_tilt_from_vertical: angle from vertical (0° = vertical, 90° = horizontal)
    
    For maximum irradiance, panel should be perpendicular to sun rays.
    When sun elevation is high (e.g., 60°), optimal panel should be close to horizontal.
    When sun elevation is low (e.g., 20°), optimal panel should be more tilted.
    """
    
    # Simple approach: For south-facing panels in southern hemisphere,
    # optimal tilt from horizontal ≈ (90° - sun_elevation)
    # So optimal tilt from vertical ≈ sun_elevation
    
    # But we need to calculate the actual dot product for any tilt angle
    
    # Convert panel tilt from vertical to tilt from horizontal
    panel_tilt_from_horizontal = 90 - panel_tilt_from_vertical
    
    # For south-facing panels (panel_azimuth = 0 in southern hemisphere means facing north)
    # In southern hemisphere, panels should face north (azimuth = 0)
    
    # Convert to radians
    panel_tilt_rad = np.radians(panel_tilt_from_horizontal)
    panel_azimuth_rad = np.radians(panel_azimuth)
    sun_elevation_rad = np.radians(sun_elevation)
    sun_azimuth_rad = np.radians(sun_azimuth)
    
    # Panel normal vector components (pointing away from panel surface)
    # When panel_tilt_from_horizontal = 0 (horizontal), normal points straight up (0,0,1)
    # When panel_tilt_from_horizontal = 90 (vertical), normal points horizontal
    panel_normal = np.array([
        np.sin(panel_tilt_rad) * np.sin(panel_azimuth_rad),  # x component
        np.sin(panel_tilt_rad) * np.cos(panel_azimuth_rad),  # y component (north-south)
        np.cos(panel_tilt_rad)  # z component (up)
    ])
    
    # Sun vector (pointing from ground toward sun)
    sun_vector = np.array([
        np.cos(sun_elevation_rad) * np.sin(sun_azimuth_rad),  # x component
        np.cos(sun_elevation_rad) * np.cos(sun_azimuth_rad),  # y component
        np.sin(sun_elevation_rad)  # z component (up)
    ])
    
    # Cosine of angle between vectors (dot product)
    cosine_angle = np.dot(panel_normal, sun_vector)
    
    # Ensure non-negative (panel only collects light from front)
    return max(0, cosine_angle)

def optimize_single_period(latitude, longitude, date, start_hour, end_hour, tz, 
                          panel_azimuth=0, time_step_minutes=15):
    """
    Find optimal tilt angle for a single time period
    Returns angle from vertical (0° = vertical, 90° = horizontal)
    """
    
    if isinstance(date, str):
        date = datetime.fromisoformat(date)
    
    # Generate time points for the period
    times = []
    current_time = date.replace(hour=int(start_hour), minute=int((start_hour % 1) * 60))
    end_time = date.replace(hour=int(end_hour), minute=int((end_hour % 1) * 60))
    
    while current_time <= end_time:
        times.append(current_time)
        current_time += timedelta(minutes=time_step_minutes)
    
    # Test different tilt angles from vertical (0° to 90°)
    tilt_angles_from_vertical = np.arange(0, 91, 1)
    total_irradiance = []
    sun_positions = []
    
    # Collect sun positions for this period
    for time_point in times:
        elevation, azimuth = solar_position(latitude, longitude, time_point, tz)
        if elevation > 0:  # Sun is above horizon
            sun_positions.append({
                'time': time_point.strftime('%H:%M'),
                'elevation': elevation,
                'azimuth': azimuth
            })
    
    # Calculate average sun elevation for reference
    avg_sun_elevation = np.mean([pos['elevation'] for pos in sun_positions]) if sun_positions else 0
    
    for tilt_from_vertical in tilt_angles_from_vertical:
        irradiance_sum = 0
        valid_points = 0
        
        for time_point in times:
            elevation, azimuth = solar_position(latitude, longitude, time_point, tz)
            
            if elevation > 0:
                irradiance = calculate_irradiance_factor(tilt_from_vertical, panel_azimuth, elevation, azimuth)
                irradiance_sum += irradiance
                valid_points += 1
        
        avg_irradiance = irradiance_sum / max(1, valid_points)
        total_irradiance.append(avg_irradiance)
    
    # Find optimal tilt angle
    if total_irradiance:
        optimal_index = np.argmax(total_irradiance)
        optimal_tilt_from_vertical = tilt_angles_from_vertical[optimal_index]
        max_irradiance = total_irradiance[optimal_index]
    else:
        optimal_tilt_from_vertical = 0
        max_irradiance = 0
    
    return {
        'optimal_tilt_from_vertical': optimal_tilt_from_vertical,
        'optimal_tilt_from_horizontal': 90 - optimal_tilt_from_vertical,
        'max_irradiance': max_irradiance,
        'avg_sun_elevation': avg_sun_elevation,
        'sun_positions': sun_positions,
        'tilt_angles': tilt_angles_from_vertical,
        'irradiance_values': total_irradiance
    }

def verify_calculation_logic():
    """
    Test the calculation with known scenarios to verify correctness
    """
    print("VERIFICATION TESTS:")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Sun directly overhead (90° elevation)',
            'sun_elevation': 90,
            'sun_azimuth': 0,
            'expected_optimal_tilt_from_vertical': 90,  # Panel should be horizontal
            'expected_optimal_tilt_from_horizontal': 0
        },
        {
            'name': 'Sun at 45° elevation (noon-ish)',
            'sun_elevation': 45,
            'sun_azimuth': 0,
            'expected_optimal_tilt_from_vertical': 45,  # Panel should tilt to face sun
            'expected_optimal_tilt_from_horizontal': 45
        },
        {
            'name': 'Sun at 30° elevation (morning/evening)',
            'sun_elevation': 30,
            'sun_azimuth': 90,  # East or West
            'expected_optimal_tilt_from_vertical': 30,  # Panel should tilt more toward sun
            'expected_optimal_tilt_from_horizontal': 60
        }
    ]
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"Sun elevation: {test['sun_elevation']}°, azimuth: {test['sun_azimuth']}°")
        
        # Test different panel tilts and find the one with maximum irradiance
        best_irradiance = 0
        best_tilt_from_vertical = 0
        
        for tilt_from_vertical in range(0, 91, 1):
            irradiance = calculate_irradiance_factor(tilt_from_vertical, 0, 
                                                   test['sun_elevation'], test['sun_azimuth'])
            if irradiance > best_irradiance:
                best_irradiance = irradiance
                best_tilt_from_vertical = tilt_from_vertical
        
        print(f"Calculated optimal tilt from vertical: {best_tilt_from_vertical}°")
        print(f"Expected optimal tilt from vertical: {test['expected_optimal_tilt_from_vertical']}°")
        print(f"Calculated optimal tilt from horizontal: {90 - best_tilt_from_vertical}°")
        print(f"Max irradiance factor: {best_irradiance:.3f}")
        
        # Check if result makes sense
        if abs(best_tilt_from_vertical - test['expected_optimal_tilt_from_vertical']) < 5:
            print("✓ PASS - Result is reasonable")
        else:
            print("✗ FAIL - Result doesn't match expectation")

def main():
    # First run verification
    verify_calculation_logic()
    
    print("\n" + "=" * 70)
    print("ACTUAL ANALYSIS")
    print("=" * 70)
    # Location parameters
    locations = {
        'Adelaide': {
            'latitude': -34.9285,
            'longitude': 138.6007,
            'tz': 'Australia/Adelaide'
        },
        'Darwin': {
            'latitude': -12.4634,
            'longitude': 130.8456,
            'tz': 'Australia/Darwin'
        }
    }
    
    # Analysis parameters
    date = "2025-08-15"  # Mid-August
    time_periods = [
        (6, 8, "6am-8am"),
        (12, 13, "12pm-1pm"),
        (15, 16, "3pm-4pm"),
        (17, 19, "5pm-7pm")
    ]
    
    print(f"Individual Period Solar Panel Tilt Optimization")
    print(f"Date: {date} (Mid-August)")
    print(f"Angles measured from VERTICAL (0° = vertical, 90° = horizontal)")
    print("=" * 70)
    
    # Create plots
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    fig.suptitle('Optimal Tilt Angles by Time Period - Adelaide vs Darwin (August 15)', fontsize=16)
    
    all_results = {}
    
    for city_idx, (city, params) in enumerate(locations.items()):
        lat, lon, tz = params['latitude'], params['longitude'], params['tz']
        
        print(f"\n{city.upper()} - Latitude: {lat}°")
        print("=" * 50)
        print(f"{'Period':<12} {'Optimal Tilt':<12} {'From Horiz':<12} {'Max Irrad':<12} {'Avg Sun Elev':<12}")
        print(f"{'':12} {'(from vert)':<12} {'(from horiz)':<12} {'Factor':<12} {'(degrees)':<12}")
        print("-" * 70)
        
        period_results = []
        
        for period_idx, (start_hour, end_hour, period_name) in enumerate(time_periods):
            result = optimize_single_period(lat, lon, date, start_hour, end_hour, tz)
            
            period_results.append({
                'period': period_name,
                'result': result
            })
            
            # Print results
            print(f"{period_name:<12} {result['optimal_tilt_from_vertical']:>8.0f}°    "
                  f"{result['optimal_tilt_from_horizontal']:>8.0f}°      "
                  f"{result['max_irradiance']:>8.3f}      "
                  f"{result['avg_sun_elevation']:>8.1f}°")
            
            # Plot for this period and city
            ax = axes[city_idx, period_idx]
            
            if result['irradiance_values']:
                ax.plot(result['tilt_angles'], result['irradiance_values'], 'b-', linewidth=2)
                ax.axvline(x=result['optimal_tilt_from_vertical'], color='r', linestyle='--', 
                          label=f"Optimal: {result['optimal_tilt_from_vertical']:.0f}°")
                ax.axvline(x=90-abs(lat), color='g', linestyle='--', alpha=0.7,
                          label=f"Lat rule: {90-abs(lat):.0f}°")
                
                ax.set_xlabel('Tilt from Vertical (degrees)')
                ax.set_ylabel('Irradiance Factor')
                ax.set_title(f'{city} - {period_name}')
                ax.grid(True, alpha=0.3)
                ax.legend(fontsize=8)
                ax.set_xlim(0, 90)
                
                # Add sun elevation info
                ax.text(0.02, 0.98, f'Avg Sun: {result["avg_sun_elevation"]:.1f}°', 
                       transform=ax.transAxes, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        all_results[city] = period_results
        
        # Print detailed sun positions for each period
        print(f"\nDetailed Sun Positions for {city}:")
        for period_data in period_results:
            period_name = period_data['period']
            sun_positions = period_data['result']['sun_positions']
            print(f"\n  {period_name}:")
            if sun_positions:
                for pos in sun_positions[::2]:  # Show every other position to avoid clutter
                    print(f"    {pos['time']}: elevation {pos['elevation']:5.1f}°, azimuth {pos['azimuth']:5.1f}°")
            else:
                print(f"    No sun above horizon during this period")
    
    plt.tight_layout()
    plt.show()
    
    # Summary comparison table
    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON - OPTIMAL TILT ANGLES FROM VERTICAL")
    print("=" * 80)
    print(f"{'Period':<12} {'Adelaide':<15} {'Darwin':<15} {'Difference':<15}")
    print(f"{'':12} {'(from vert)':<15} {'(from vert)':<15} {'(Adel-Dar)':<15}")
    print("-" * 80)
    
    adelaide_results = all_results['Adelaide']
    darwin_results = all_results['Darwin']
    
    for i, period_name in enumerate(['6am-8am', '12pm-1pm', '3pm-4pm', '5pm-7pm']):
        adel_tilt = adelaide_results[i]['result']['optimal_tilt_from_vertical']
        darwin_tilt = darwin_results[i]['result']['optimal_tilt_from_vertical']
        diff = adel_tilt - darwin_tilt
        
        print(f"{period_name:<12} {adel_tilt:>8.0f}°       {darwin_tilt:>8.0f}°       {diff:>+8.0f}°")
    
    print("\n" + "=" * 80)
    print("QUICK REFERENCE - TILT FROM HORIZONTAL (TRADITIONAL MEASUREMENT)")
    print("=" * 80)
    print(f"{'Period':<12} {'Adelaide':<15} {'Darwin':<15}")
    print(f"{'':12} {'(from horiz)':<15} {'(from horiz)':<15}")
    print("-" * 60)
    
    for i, period_name in enumerate(['6am-8am', '12pm-1pm', '3pm-4pm', '5pm-7pm']):
        adel_tilt_horiz = adelaide_results[i]['result']['optimal_tilt_from_horizontal']
        darwin_tilt_horiz = darwin_results[i]['result']['optimal_tilt_from_horizontal']
        
        print(f"{period_name:<12} {adel_tilt_horiz:>8.0f}°       {darwin_tilt_horiz:>8.0f}°")
    
    print(f"\nNote: Angle from vertical means 0° = perfectly vertical panel, 90° = horizontal panel")
    print(f"      Angle from horizontal means 0° = horizontal panel, 90° = vertical panel")

if __name__ == "__main__":
    main()