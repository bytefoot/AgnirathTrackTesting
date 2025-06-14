import numpy as np
import pandas as pd
import os

from config import PanelArea, PanelEfficiency
from state import StartTime

_df = pd.read_csv(os.path.expanduser("~") + "/Developer/Agnirath/TrackTesting/data/sol&wind.csv")
STEP = 5
NET_PANEL_FACTOR = PanelArea * PanelEfficiency
INIT_TIME = StartTime/60 - 8 * 60
# print(INIT_TIME, NET_PANEL_FACTOR)

# _df['minutes_since_start'] = (
#     pd.to_timedelta(_df['time']).dt.total_seconds() // 60
# ).astype(int)

# _minutes = _df['minutes_since_start'].to_numpy()
_ghi = _df['ghi'].to_numpy()
_wind_speed = _df['wind_speed'].to_numpy()
_wind_direction = _df['wind_direction'].to_numpy()

def get_solar_power(input_minutes: np.ndarray) -> np.ndarray:
    idx = np.floor_divide(input_minutes + INIT_TIME, STEP).astype(int)
    # print(input_minutes + INIT_TIME)
    # print(idx)
    return _ghi[idx] * NET_PANEL_FACTOR

def get_wind_data(input_minutes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    idx = np.floor_divide(input_minutes + INIT_TIME, STEP).astype(int)
    return _wind_speed[idx], _wind_direction[idx]
