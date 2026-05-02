from dataclasses import dataclass

from simulation.engine import BusSimulationEngine
from simulation.predictor import BusPredictor


@dataclass
class RuntimeState:
    predictor: BusPredictor | None = None
    simulation_engine: BusSimulationEngine | None = None


runtime_state = RuntimeState()
