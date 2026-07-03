"""
Minimal invocation stub showing how the deliverable is invoked.
This file contains no sensitive logic and is safe to distribute.
"""
from src_minimal.interfaces.pathfinder_interface import PathfinderInterface


class DummyPathfinder(PathfinderInterface):
    def find_path(self, start, end):
        # Return a trivial two-point path for verification
        return [start, end]


def main():
    pf = DummyPathfinder()
    path = pf.find_path("31.0400,31.3700", "31.0500,31.3800")
    print("Demo path:", path)


if __name__ == "__main__":
    main()
