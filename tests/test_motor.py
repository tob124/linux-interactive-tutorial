"""Physical and integration-contract tests; run without third-party packages."""
import json
import math
import unittest

from server import motor


class MotorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default = motor.simulate({})
        cls.no_load = motor.simulate({"mode": "open", "load_Nm": 0.0})
        cls.loaded = motor.simulate({"mode": "open"})

    def test_zero_input_zero_initial_conditions(self):
        result = motor.simulate({"mode": "open", "voltage": 0, "load_Nm": 0,
                                 "target_rpm": 0, "duration": 0.2})
        for row in result["series"]:
            for key in ("rpm", "current", "torque", "voltage"):
                self.assertEqual(row[key], 0.0)
        self.assertEqual(result["metrics"]["peak_current"], 0.0)
        self.assertIsNone(result["metrics"]["steady_error_pct"])

    def test_open_loop_analytic_steady_state(self):
        # Derived directly from Kirchoff/torque balance, not from the integrator.
        expected_w = 0.05 * 12.0 / (2.0 * 0.0001 + 0.05 * 0.05)
        expected_i = (12.0 - 0.05 * expected_w) / 2.0
        final = self.no_load["series"][-1]
        self.assertAlmostEqual(final["rpm"], expected_w * 60 / (2 * math.pi), places=7)
        self.assertAlmostEqual(final["current"], expected_i, places=9)

    def test_open_loop_loaded_steady_state(self):
        expected_w = (0.05 * 12.0 - 2.0 * 0.03) / (2.0 * 0.0001 + 0.05 * 0.05)
        expected_i = (12.0 - 0.05 * expected_w) / 2.0
        final = self.loaded["series"][-1]
        self.assertAlmostEqual(final["rpm"], expected_w * 60 / (2 * math.pi), delta=0.001)
        self.assertAlmostEqual(final["current"], expected_i, delta=0.00001)

    def test_rk4_step_convergence_open_and_closed(self):
        for mode in ("open", "closed"):
            with self.subTest(mode=mode):
                common = {"mode": mode, "duration": 0.5, "load_time": 0.20015}
                coarse = motor.simulate({**common, "dt": 0.0001})
                medium = motor.simulate({**common, "dt": 0.00005})
                fine = motor.simulate({**common, "dt": 0.000025})
                error_cm = max(abs(a["rpm"] - b["rpm"]) for a, b in
                               zip(coarse["series"], medium["series"]))
                error_mf = max(abs(a["rpm"] - b["rpm"]) for a, b in
                               zip(medium["series"], fine["series"]))
                self.assertLess(error_cm, 0.001)
                self.assertLess(error_mf, error_cm / 5.0)

    def test_exact_load_discontinuity_and_non_grid_horizon(self):
        # No current/rotation can precede the external load; load is applied
        # between sample/substep grid points, and the endpoint is retained.
        cfg = {"mode": "open", "voltage": 0, "duration": 0.01523,
               "load_time": 0.01015, "load_Nm": 0.03}
        result = motor.simulate(cfg)
        rows = result["series"]
        self.assertEqual([row["t"] for row in rows], [0.0, 0.005, 0.01, 0.015, 0.01523])
        self.assertEqual(rows[2]["rpm"], 0.0)
        self.assertEqual(rows[2]["load"], 0.0)
        self.assertLess(rows[-1]["rpm"], 0.0)
        self.assertEqual(rows[-1]["load"], 0.03)

    def test_default_pi_acceptance(self):
        metrics = self.default["metrics"]
        self.assertLess(metrics["steady_error_pct"], 1.0)
        self.assertLess(metrics["overshoot_pct"], 15.0)
        self.assertIsNotNone(metrics["settling_time"])
        self.assertLess(metrics["settling_time"], 1.0)
        self.assertAlmostEqual(metrics["final_rpm"], 900.0, delta=1.0)
        self.assertEqual(metrics["saturation_pct"], 0.0)

    def test_supply_saturation_and_unreachable_target(self):
        result = motor.simulate({"target_rpm": 6000, "kp": 5, "ki": 100, "duration": 1})
        self.assertTrue(all(abs(row["voltage"]) <= 24.0 for row in result["series"]))
        self.assertGreater(result["metrics"]["saturation_pct"], 90.0)
        self.assertGreater(result["metrics"]["steady_error_pct"], 20.0)
        self.assertIsNone(result["metrics"]["settling_time"])
        self.assertTrue(any("超过 ±24 V" in warning for warning in result["warnings"]))

    def test_feedback_faults_are_detectable(self):
        units = motor.simulate({"fault": "units"})
        bias = motor.simulate({"fault": "bias"})
        reversed_feedback = motor.simulate({"fault": "reversed"})
        self.assertAlmostEqual(units["metrics"]["final_rpm"],
                               900.0 / motor.RPM_PER_RAD_S, delta=1.0)
        self.assertAlmostEqual(bias["metrics"]["final_rpm"], 780.0, delta=1.0)
        self.assertGreater(reversed_feedback["metrics"]["final_rpm"], 3500)
        for result in (units, bias, reversed_feedback):
            self.assertGreater(result["metrics"]["steady_error_pct"], 10.0)
            self.assertIsNone(result["metrics"]["settling_time"])
        self.assertAlmostEqual(bias["series"][-1]["measured_rpm"], 900.0, delta=1.0)
        self.assertLess(reversed_feedback["series"][-1]["measured_rpm"], 0.0)

    def test_feedback_fault_does_not_change_open_loop_physics(self):
        baseline = motor.simulate({"mode": "open", "duration": 0.1})
        for fault in ("units", "reversed", "bias"):
            with self.subTest(fault=fault):
                changed = motor.simulate({"mode": "open", "duration": 0.1, "fault": fault})
                for a, b in zip(baseline["series"], changed["series"]):
                    for key in ("rpm", "current", "torque", "voltage", "load"):
                        self.assertEqual(a[key], b[key])

    def test_gain_change_changes_computed_response(self):
        slower = motor.simulate({"kp": 0.02, "ki": 0.1, "duration": 0.2})
        same_time = self.default["series"][40]
        self.assertGreater(abs(slower["series"][-1]["rpm"] - same_time["rpm"]), 20)

    def test_anti_windup_changes_saturated_transient(self):
        common = {"target_rpm": 3000, "kp": 1.0, "ki": 10.0, "duration": 2.0}
        enabled = motor.simulate({**common, "anti_windup": True})
        disabled = motor.simulate({**common, "anti_windup": False})
        self.assertLess(enabled["metrics"]["overshoot_pct"],
                        disabled["metrics"]["overshoot_pct"])
        self.assertLess(enabled["metrics"]["saturation_pct"],
                        disabled["metrics"]["saturation_pct"])

    def test_output_contract_and_determinism(self):
        result = motor.simulate({"duration": 0.1})
        self.assertEqual(len(result["series"]), 21)
        self.assertEqual(set(result), {"config", "model", "units", "series", "metrics", "warnings"})
        self.assertEqual(set(result["series"][0]),
                         {"t", "rpm", "measured_rpm", "target_rpm", "current", "voltage", "torque", "load"})
        self.assertEqual(result, motor.simulate({"duration": 0.1}))
        json.dumps(result, allow_nan=False)

    def test_invalid_configuration(self):
        invalid = [
            [], "{}", {"mode": "demo"}, {"mode": []}, {"fault": "stall"},
            {"fault": []}, {"duration": 10.01}, {"duration": 0},
            {"duration": float("nan")}, {"voltage": float("inf")},
            {"kp": -1}, {"ki": 101}, {"target_rpm": 6001},
            {"load_Nm": 0.21}, {"load_time": -1}, {"dt": 0.001},
            {"dt": 0.000001}, {"anti_windup": 1}, {"kp": True},
            {"voltage": "12"}, {"extra": 1}, {"duration": 10**1000},
        ]
        for cfg in invalid:
            with self.subTest(config=str(cfg)[:80]):
                with self.assertRaises(ValueError):
                    motor.validate_config(cfg)

    def test_config_copy_and_zero_gains(self):
        cfg = {"kp": 0.0, "ki": 0.0, "duration": 0.1, "load_Nm": 0.0}
        snapshot = dict(cfg)
        result = motor.simulate(cfg)
        self.assertEqual(cfg, snapshot)
        self.assertEqual(result["metrics"]["final_rpm"], 0.0)

    def test_crosscheck_is_open_loop_only(self):
        with self.assertRaises(ValueError):
            motor.crosscheck({"mode": "closed"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
