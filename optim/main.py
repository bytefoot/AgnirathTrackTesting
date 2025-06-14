import numpy as np
from scipy.optimize import minimize
from pprint import pprint

import state
import config
from constraints import objective, battery_acc_constraint_func, get_bounds
from profiles import extract_profiles

def run_optimise(dx, dir, ds):
    N_V = len(dx) + 1
    velocity_profile = np.concatenate([[0], np.ones(N_V-2) * state.InitialGuessVelocity, [0]])

    bounds = get_bounds(N_V)
    constraints = [
        {
            "type": "ineq",
            "fun": battery_acc_constraint_func,
            "args": (dx, ds, dir)
        },
    ]


    print("Starting Optimisation")
    print("=" * 60)

    optimised_velocity_profile = minimize(
        objective, velocity_profile,
        args=(dx,),
        bounds=bounds,
        method=state.ModelMethod,
        # method="SLSQP",
        constraints=constraints,
        # options={
        #     'verbose': 3,
        # }
    )
    optimised_velocity_profile = np.array(optimised_velocity_profile.x)*1

    print(optimised_velocity_profile)
    time_taken = objective(optimised_velocity_profile, dx)

    # print("done.")
    print("Total time taken for race:", time_taken/3600, "hrs")

    pprint(extract_profiles(optimised_velocity_profile, dx, ds, dir))


    return

if __name__ == "__main__":
    step = state.route_data['step'].to_numpy()
    direction = state.route_data['direction'].to_numpy()
    slope = state.route_data['slope'].to_numpy()

    # LAPS = 2
    # step = np.tile(step, LAPS)
    # direction = np.tile(direction, LAPS)
    # slope = np.tile(slope, LAPS)

    outdf = run_optimise(step, direction, slope)