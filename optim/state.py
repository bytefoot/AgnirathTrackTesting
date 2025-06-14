import config
import os
import pandas as pd

route_data = pd.read_csv(os.path.expanduser("~") + "/Developer/Agnirath/TrackTesting/data/lappedroute.csv")

# Model Settings
ModelMethod = "COBYLA"
InitialGuessVelocity = 25
InitialGuessVelocity = 32

StartTime = 9 * 3600  # 8:00 am
EndTime = (12 + 6) * 3600  # 6:00 pm

InitialBatteryCapacity = config.BatteryCapacity * 1
FinalBatteryCapacity = config.BatteryCapacity * 0.44
