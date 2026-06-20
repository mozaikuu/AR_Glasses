# Simulation Module

This package powers the prototype realism layer.

## Responsibilities

- Simulate NMU Bus Route #1 movement along route coordinates
- Apply speed variation, stop behavior, and passenger boarding patterns
- Generate random incidents (traffic jam, delay, breakdown, etc.)
- Feed ETA and demand predictors with current traffic state

## Files

- `route_data.py`: Route geometry, schedule, stop metadata, driver info
- `historical_data.py`: 3-month synthetic dataset generator
- `predictor.py`: scikit-learn regression models for ETA and demand
- `engine.py`: Continuous async simulation runtime

## Runtime Integration

`bus_system/backend/app/main.py` starts `BusSimulationEngine` automatically in FastAPI lifespan.

---

Copyright © 2026 Ahmed Moussa

This software is provided to New Mansoura University solely for academic evaluation purposes.

No license, ownership rights, distribution rights, modification rights, or commercial rights are granted.

All intellectual property rights remain with the author.
