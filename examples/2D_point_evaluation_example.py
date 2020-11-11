""" 
Simple 2D point evaluation example to test and evaluate tracker for basic functionality
"""

import os
import sys
sys.path.append(
    os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
import lmb

def main():
    
    sim_params = lmb.Sim_Parameters() 
    tracker_params = lmb.Tracker_Parameters()

    tracker = lmb.LMB(params=tracker_params)

    gt_target_track_history = lmb.create_target_tracks(params=sim_params)
 
    measuerment_history = lmb.create_measurement_history(gt_target_track_history, params=sim_params)

    tracker_estimates_history = []
    for k in sim_params.sim_length:
        tracks_estimates_k = tracker.update(measuerment_history[k])
        tracker_estimates_history.append(tracks_estimates_k)

    lmb.evaluate(gt_target_track_history,tracker_estimates_history)


if __name__ == '__main__':
    main()
