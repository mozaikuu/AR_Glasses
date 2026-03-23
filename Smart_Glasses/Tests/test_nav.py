import sys
import os
sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..")))

from tools.navigation.nav import NavigateAStar


def test():
    print(
        NavigateAStar(
            start="Entrance",
            destination="Dean Office"
        )
    )

if __name__ == "__main__":
    test()
