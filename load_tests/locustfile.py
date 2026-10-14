import os

scenario = os.environ.get("LOAD_SCENARIO", "browse")

if scenario == "mixed":
    from load_tests.scenarios.mixed import MixedUser
elif scenario == "contention":
    from load_tests.scenarios.seat_contention import SeatContentionUser
elif scenario == "login":
    from load_tests.scenarios.login import LoginUser
else:
    from load_tests.scenarios.browse import BrowseUser

__all__ = [name for name in globals() if name.endswith("User")]
