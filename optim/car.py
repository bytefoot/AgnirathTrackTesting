import numpy as np
import pandas as pd

from config import (
    Mass, ZeroSpeedCrr, AirDensity, CDA, R_Out, Ta,
    GravityAcc,
)

EPSILON = 10**-8

# Constants
_frictional_tou = R_Out * Mass * GravityAcc * ZeroSpeedCrr
_drag_coeff = 0.5 * CDA * AirDensity * (R_Out ** 3)
_drag_coeff_wR2 = _drag_coeff / (R_Out ** 2)
_slope_coeff = Mass * GravityAcc
_windage_losses_coeff_wR2 = (170.4 * 10**-6) / (R_Out ** 2)

def calculate_power(speed, acceleration, slope, dir, ws, wd):
    speed2 = speed ** 2

    # Calculate drag torque considering wind speed
    # drag_tou = _drag_coeff_wR2 * ((speed2 + ws**2 - 2 * speed * ws * np.cos(dir - wd)))
    drag_tou = _drag_coeff_wR2 * speed2
    tou = _frictional_tou * np.cos(slope) + drag_tou
    
    # Finding winding temperature
    Tw_i = Ta

    while True:
        # B = 1.32 - 1.2 * 10**-3 * (Ta / 2 + Tw_i / 2 - 293)
        B = 1.6716 - 0.0006 * (Ta + Tw_i)  # magnetic remanence
        i = 0.561 * B * tou  # RMS phase current

        # R = 0.0575 * (1 + 0.0039 * (Tw_i - 293))
        resistance = 0.00022425 * Tw_i - 0.00820525  # resistance of windings
        
        Pc = 3 * i ** 2 * resistance  # copper (ohmic) losses
        Pe = (9.602 * (10**-6) * ((B/R_Out) ** 2) / resistance) * speed2  # eddy current losses
        Tw = 0.455 * (Pc + Pe) + Ta
    
        cond = np.abs(Tw - Tw_i) < 0.001
        if np.all(cond):
            break

        Tw_i = np.where(cond, Tw_i, Tw)

    # Final eta calculations
    P_out = tou * speed / R_Out  # output power
    Pw = (speed2) * _windage_losses_coeff_wR2 # windage losses

    P_acc = (Mass * acceleration + _slope_coeff * np.sin(slope)) * speed

    P_net = P_out + (Pw + Pc + Pe + P_acc) # + 120 # 150
    return P_net.clip(0), P_out