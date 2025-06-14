import numpy as np

from config import BatteryCapacity
import state
from car import calculate_power
from weather import get_solar_power,get_wind_data

EPSILON = 1e-8

def extract_profiles(v, dx, ds, dir):
    start_speeds, stop_speeds = v[:-1], v[1:]
    avg_speed = (start_speeds + stop_speeds) / 2

    dt =  dx / (avg_speed + EPSILON)
    acceleration = (stop_speeds - start_speeds) / dt

    minutes = dt.cumsum() / 60

    ws, wd = get_wind_data(minutes)
    P,_ = calculate_power(avg_speed, acceleration, ds, dir, ws, wd)
    SolP = get_solar_power(minutes)

    print(P)
    print(SolP)

    energy_consumption = P * dt / 3600
    energy_gain = SolP * dt / 3600

    net_energy_profile = energy_consumption.cumsum() - energy_gain.cumsum()
    
    battery_profile = state.InitialBatteryCapacity - net_energy_profile
    battery_profile = np.concatenate((np.array([state.InitialBatteryCapacity]), battery_profile))

    battery_profile = battery_profile * 100 / (BatteryCapacity)

    distances = np.append([0], dx)

    return [
        distances,
        v,
        np.concatenate((np.array([np.nan]), acceleration,)),
        battery_profile,
        np.concatenate((np.array([np.nan]), energy_consumption,)),
        np.concatenate((np.array([np.nan]), energy_gain)),
        np.concatenate((np.array([0]), dt.cumsum())),
    ]