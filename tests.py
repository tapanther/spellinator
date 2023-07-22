import unittest
from extensions.energy_cost import ecost_calculator

from datetime import time, datetime


def expected_cost_calc(soc_delta, avg_cost):
    return 66.6 * soc_delta / 0.85 * avg_cost / 100


# noinspection DuplicatedCode
class MyTestCase(unittest.TestCase):
    def test_ecost(self):
        soc_delta = 10
        today_ovrd = datetime(
            2023, 6, 15
        )
        _, _, _, _, _, total_cost, _ = \
            ecost_calculator(soc_delta=soc_delta, charge_start_time=time.fromisoformat("17:00"),
                             charge_stop_time=time.fromisoformat("19:00"), today_ovrd=today_ovrd)
        expected_cost = expected_cost_calc(soc_delta, 0.49)
        self.assertAlmostEqual(total_cost, expected_cost, delta=0.05)

        _, _, _, _, _, total_cost, _ = \
            ecost_calculator(soc_delta=soc_delta, charge_start_time=time.fromisoformat("08:00"),
                             charge_stop_time=time.fromisoformat("10:00"), today_ovrd=today_ovrd)
        expected_cost = expected_cost_calc(soc_delta, 0.36)
        self.assertAlmostEqual(total_cost, expected_cost, delta=0.05)

        _, peak_dur, _, _, _, total_cost, avg = \
            ecost_calculator(soc_delta=soc_delta, charge_start_time=time.fromisoformat("16:00"),
                             charge_stop_time=time.fromisoformat("18:00"), today_ovrd=today_ovrd)
        expected_cost = expected_cost_calc(soc_delta, 0.425)
        self.assertAlmostEqual(total_cost, expected_cost, delta=0.05)

        _, peak_dur, _, _, _, total_cost, _ = \
            ecost_calculator(soc_delta=soc_delta, charge_start_time=time.fromisoformat("16:00"),
                             charge_stop_time=time.fromisoformat("23:00"), today_ovrd=today_ovrd)
        expected_cost = expected_cost_calc(soc_delta, 0.43)
        self.assertAlmostEqual(total_cost, expected_cost, delta=0.05)

        today_ovrd = datetime(
            2023, 3, 15
        )
        _, _, _, _, _, total_cost, _ = \
            ecost_calculator(soc_delta=soc_delta, charge_start_time=time.fromisoformat("17:00"),
                             charge_stop_time=time.fromisoformat("19:00"), today_ovrd=today_ovrd)
        expected_cost = expected_cost_calc(soc_delta, 0.40)
        self.assertAlmostEqual(total_cost, expected_cost, delta=0.05)

        _, _, _, _, _, total_cost, _ = \
            ecost_calculator(soc_delta=soc_delta, charge_start_time=time.fromisoformat("08:00"),
                             charge_stop_time=time.fromisoformat("10:00"), today_ovrd=today_ovrd)
        expected_cost = expected_cost_calc(soc_delta, 0.37)
        self.assertAlmostEqual(total_cost, expected_cost, delta=0.05)

        _, _, _, _, _, total_cost, _ = \
            ecost_calculator(soc_delta=soc_delta, charge_start_time=time.fromisoformat("16:00"),
                             charge_stop_time=time.fromisoformat("18:00"), today_ovrd=today_ovrd)
        expected_cost = expected_cost_calc(soc_delta, 0.385)
        self.assertAlmostEqual(total_cost, expected_cost, delta=0.05)

        _, peak_dur, _, _, _, total_cost, _ = \
            ecost_calculator(soc_delta=soc_delta, charge_start_time=time.fromisoformat("16:00"),
                             charge_stop_time=time.fromisoformat("23:00"), today_ovrd=today_ovrd)
        expected_cost = expected_cost_calc(soc_delta, 0.385)
        self.assertAlmostEqual(total_cost, expected_cost, delta=0.05)


if __name__ == '__main__':
    unittest.main()
