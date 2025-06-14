import numpy as np

from weather import get_solar_power, get_wind_data
from car import calculate_power

import state
from config import BatteryCapacity, DeepDischargeCap, MaxVelocity, MaxCurrent, BusVoltage

SafeBatteryLevel = BatteryCapacity * (DeepDischargeCap)
MaxPower = MaxCurrent * BusVoltage
EPSILON = 10**-8

def get_bounds(N):
    return ([(0, 0)] + [(0.01, MaxVelocity)]*(N-2) + [(0, 0)])

def objective(velocity_profile, dx):
    return np.sum(2 * dx / (velocity_profile[:-1] + velocity_profile[1:] + EPSILON))

def battery_acc_constraint_func(v, dx, ds, dir):
    start_speeds, stop_speeds = v[:-1], v[1:]
    avg_speed = (start_speeds + stop_speeds) / 2

    dt =  dx / (avg_speed + EPSILON)
    acceleration = (stop_speeds - start_speeds) / dt

    minutes = dt.cumsum() / 60

    ws, wd = get_wind_data(minutes)
    P, _ = calculate_power(avg_speed, acceleration, ds, dir, ws, wd)
    SolP = get_solar_power(minutes)

    energy_consumption = ((P - SolP) * dt).cumsum() / 3600
    battery_profile = state.InitialBatteryCapacity - energy_consumption - SafeBatteryLevel

    return np.min(battery_profile), MaxPower - np.max(P)