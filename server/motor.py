"""Small, deterministic DC-motor teaching model; no runtime dependencies.

All physical states use SI units. A digital PI samples every 1 ms and holds its
voltage between samples. RK4 advances the plant every 0.1 ms (or a smaller dt).
Only the feedback measurement is changed by a fault. Positive load_Nm is an
external negative torque, not a brake that always opposes the velocity.

This is an averaged, ideal permanent-magnet brushed-DC motor. It has no PWM,
current controller, thermal, switching, friction, encoder-count, timing-jitter
or real-drive/fieldbus model. Its parameters are teaching values, not hardware
identification data. Computation is offline simulation, not real-time control.

Run: python3 motor.py '{"mode":"closed"}'
Test: python3 -m unittest -v test_motor
"""
from __future__ import annotations

import json
import math
import sys

R = 2.0                 # ohm
L = 0.002               # H
J = 0.0002              # kg m^2
B = 0.0001              # N m s/rad
KT = 0.05               # N m/A
KE = 0.05               # V s/rad
MAX_VOLTAGE = 24.0      # V
SAMPLE_TIME = 0.001     # s, digital controller period
OUTPUT_PERIOD = 0.005  # s
RPM_PER_RAD_S = 60.0 / (2.0 * math.pi)
BIAS_RPM = 120.0        # constant sensor offset for the bias fault
_EPS = 1e-12

DEFAULTS = {
    "mode": "closed",
    "voltage": 12.0,
    "target_rpm": 900.0,
    "kp": 0.08,
    "ki": 0.6,
    "duration": 5.0,
    "load_time": 2.5,
    "load_Nm": 0.03,
    "fault": "none",
    "anti_windup": True,
    "dt": 0.0001,
}
_RANGES = {
    "voltage": (-24.0, 24.0),
    "target_rpm": (-6000.0, 6000.0),
    "kp": (0.0, 5.0),
    "ki": (0.0, 100.0),
    "duration": (0.01, 10.0),
    "load_time": (0.0, 10.0),
    "load_Nm": (-0.2, 0.2),
    "dt": (0.000025, 0.0001),
}

LIMITATIONS = [
    "教学参数的平均直流电机模型，未通过真实电机辨识或硬件实验验证。",
    "不包含 PWM、真实驱动器、电流闭环、热效应、库仑摩擦或实时总线。",
    "电压限制为 ±24 V；电流是物理积分结果，没有伪造的状态裁剪或电流保护。",
]


def validate_config(config: dict) -> dict:
    """Return a normalized copy; raise ValueError for unsupported/unsafe input.

    dt is the plant integration step, not the fixed controller sample time.
    Numeric strings and booleans are deliberately not accepted as numbers.
    """
    if not isinstance(config, dict):
        raise ValueError("config must be a JSON object")
    unknown = set(config).difference(DEFAULTS)
    if unknown:
        raise ValueError("unknown configuration field(s): " +
                         ", ".join(sorted(map(str, unknown))))
    result = dict(DEFAULTS)
    result.update(config)
    if not isinstance(result["mode"], str) or result["mode"] not in ("open", "closed"):
        raise ValueError("mode must be 'open' or 'closed'")
    if not isinstance(result["fault"], str) or result["fault"] not in (
            "none", "units", "reversed", "bias"):
        raise ValueError("fault must be 'none', 'units', 'reversed', or 'bias'")
    if not isinstance(result["anti_windup"], bool):
        raise ValueError("anti_windup must be boolean")
    for key, (low, high) in _RANGES.items():
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be a finite number in [{low}, {high}]")
        try:
            value = float(value)
        except (ValueError, OverflowError):
            raise ValueError(f"{key} must be a finite number") from None
        if not math.isfinite(value) or value < low or value > high:
            raise ValueError(f"{key} must be a finite number in [{low}, {high}]")
        result[key] = value
    return result


def analytic_steady_state(voltage: float, load_Nm: float = 0.0) -> dict:
    """Unconstrained constant-input motor equilibrium, independent of PI."""
    omega = (KT * voltage - R * load_Nm) / (R * B + KT * KE)
    current = (voltage - KE * omega) / R
    return {"omega": omega, "rpm": omega * RPM_PER_RAD_S, "current": current}


def _load_at(t: float, cfg: dict) -> float:
    return cfg["load_Nm"] if t + _EPS >= cfg["load_time"] else 0.0


def _measured_omega(omega: float, fault: str) -> float:
    if fault == "units":
        # Sensor emits rpm, but controller treats that numeric value as rad/s.
        return omega * RPM_PER_RAD_S
    if fault == "reversed":
        return -omega
    if fault == "bias":
        return omega + BIAS_RPM / RPM_PER_RAD_S
    return omega


def _rhs(state: tuple, voltage: float, load: float) -> tuple:
    current, omega = state
    return ((voltage - R * current - KE * omega) / L,
            (KT * current - B * omega - load) / J)


def _rk4(state: tuple, voltage: float, load: float, step: float) -> tuple:
    current, omega = state
    a_i, a_w = _rhs(state, voltage, load)
    b_i, b_w = _rhs((current + step * a_i / 2.0, omega + step * a_w / 2.0),
                    voltage, load)
    c_i, c_w = _rhs((current + step * b_i / 2.0, omega + step * b_w / 2.0),
                    voltage, load)
    d_i, d_w = _rhs((current + step * c_i, omega + step * c_w), voltage, load)
    return (current + step * (a_i + 2 * b_i + 2 * c_i + d_i) / 6.0,
            omega + step * (a_w + 2 * b_w + 2 * c_w + d_w) / 6.0)


def _advance(state: tuple, start: float, end: float, voltage: float,
             cfg: dict) -> tuple:
    """Integrate a held voltage, splitting exactly at the load discontinuity."""
    t = start
    peak = abs(state[0])
    while t < end - _EPS:
        next_t = min(t + cfg["dt"], end)
        if t + _EPS < cfg["load_time"] < next_t - _EPS:
            next_t = cfg["load_time"]
        state = _rk4(state, voltage, _load_at(t, cfg), next_t - t)
        peak = max(peak, abs(state[0]))
        t = next_t
    return state, peak


def _sample_row(t: float, state: tuple, voltage: float, cfg: dict) -> dict:
    current, omega = state
    return {
        "t": round(t, 12),
        "rpm": omega * RPM_PER_RAD_S,
        # In rpm after interpreting the possibly faulty feedback as rad/s.
        "measured_rpm": _measured_omega(omega, cfg["fault"]) * RPM_PER_RAD_S,
        "target_rpm": cfg["target_rpm"],
        "current": current,
        "voltage": voltage,
        "torque": KT * current,
        "load": _load_at(t, cfg),
    }


def _calculate_metrics(cfg: dict, trace: list, peak_current: float,
                       saturated_seconds: float) -> tuple:
    final_load = _load_at(cfg["duration"], cfg)
    reference = (cfg["target_rpm"] if cfg["mode"] == "closed" else
                 analytic_steady_state(cfg["voltage"], final_load)["rpm"])
    active_load_change = (cfg["load_Nm"] != 0.0 and
                          0.0 < cfg["load_time"] < cfg["duration"])
    segment_start = cfg["load_time"] if active_load_change else 0.0
    tail_start = max(segment_start, cfg["duration"] - 0.25)
    tail = [rpm for t, rpm in trace if t + _EPS >= tail_start]
    mean_rpm = sum(tail) / len(tail)
    scale = abs(reference)
    steady_error = 100.0 * abs(mean_rpm - reference) / scale if scale > _EPS else None
    if scale > _EPS:
        direction = 1.0 if reference > 0.0 else -1.0
        overshoot = max(0.0, max(direction * rpm for _, rpm in trace) - scale) / scale * 100.0
    else:
        overshoot = None
    # Settling is after the last applied load change, measured from that change.
    # It must remain within a 2% / minimum 1 rpm band for >= 100 ms at the end.
    segment = [(t, rpm) for t, rpm in trace if t + _EPS >= segment_start]
    band = max(0.02 * scale, 1.0)
    last_outside = next((index for index in range(len(segment) - 1, -1, -1)
                         if abs(segment[index][1] - reference) > band), -1)
    settled = None
    if last_outside + 1 < len(segment):
        candidate = segment[last_outside + 1][0]
        if cfg["duration"] - candidate + _EPS >= 0.1:
            settled = max(0.0, candidate - segment_start)
    return ({
        "steady_error_pct": steady_error,
        "overshoot_pct": overshoot,
        "peak_current": peak_current,
        "settling_time": settled,
        "final_rpm": trace[-1][1],
        "saturation_pct": 100.0 * saturated_seconds / cfg["duration"],
    }, reference)


def simulate(config: dict | None = None) -> dict:
    """Compute a complete trajectory from zero physical and PI initial states.

    PI gains use rad/s error: kp [V/(rad/s)], ki [V/rad].
    At each sample, u[k] = clamp(kp*e[k] + integral[k], -24, 24).
    The Euler integral update prepares integral[k+1]; conditional integration
    stops accumulation only if saturation and error would push farther outward.
    """
    cfg = validate_config({} if config is None else config)
    state = (0.0, 0.0)   # current, angular velocity
    integral = 0.0      # integral contribution already in volts
    series = []
    trace = []
    saturated_seconds = 0.0
    peak_current = 0.0
    last_voltage = cfg["voltage"] if cfg["mode"] == "open" else 0.0
    ticks = int(math.ceil(cfg["duration"] / SAMPLE_TIME - _EPS))
    for tick in range(ticks):
        t = tick * SAMPLE_TIME
        end = min((tick + 1) * SAMPLE_TIME, cfg["duration"])
        period = end - t
        if cfg["mode"] == "closed":
            error = cfg["target_rpm"] / RPM_PER_RAD_S - _measured_omega(state[1], cfg["fault"])
            raw_voltage = cfg["kp"] * error + integral
            voltage = min(MAX_VOLTAGE, max(-MAX_VOLTAGE, raw_voltage))
            pushes_outward = ((raw_voltage >= MAX_VOLTAGE and error > 0.0) or
                               (raw_voltage <= -MAX_VOLTAGE and error < 0.0))
            if not cfg["anti_windup"] or not pushes_outward:
                integral += cfg["ki"] * error * period
        else:
            voltage = cfg["voltage"]
        trace.append((t, state[1] * RPM_PER_RAD_S))
        if tick % 5 == 0:
            series.append(_sample_row(t, state, voltage, cfg))
        state, step_peak = _advance(state, t, end, voltage, cfg)
        if not all(math.isfinite(value) for value in state):
            raise ArithmeticError("non-finite physical state; reject this simulation")
        peak_current = max(peak_current, step_peak)
        if abs(voltage) >= MAX_VOLTAGE - _EPS:
            saturated_seconds += period
        last_voltage = voltage
    final_time = cfg["duration"]
    trace.append((final_time, state[1] * RPM_PER_RAD_S))
    # Include the exact final instant even if duration is not divisible by 5 ms.
    series.append(_sample_row(final_time, state, last_voltage, cfg))
    metrics, reference = _calculate_metrics(cfg, trace, peak_current, saturated_seconds)
    warnings = list(LIMITATIONS)
    if cfg["fault"] != "none":
        warnings.append({
            "units": "故障：传感器 rpm 数字被误当作 rad/s；measured_rpm 显示控制器解释后的反馈。",
            "reversed": "故障：速度反馈符号接反；物理速度、电流仍由电机方程计算。",
            "bias": "故障：速度传感器存在 +120 rpm 固定偏差。",
        }[cfg["fault"]])
        if cfg["mode"] == "open":
            warnings.append("开环不使用速度反馈，因此反馈故障不会改变物理轨迹。")
    if cfg["mode"] == "open":
        warnings.append("开环的误差和稳定时间以恒压/末段负载的解析稳态为参照；target_rpm 不参与控制。")
    else:
        omega_target = cfg["target_rpm"] / RPM_PER_RAD_S
        required_voltage = R * (B * omega_target + _load_at(final_time, cfg)) / KT + KE * omega_target
        if abs(required_voltage) > MAX_VOLTAGE:
            warnings.append("所给目标与末段负载需要超过 ±24 V，实际转速无法达到目标。")
    if cfg["duration"] - min(cfg["load_time"], cfg["duration"]) < 0.25 and cfg["load_Nm"] != 0.0:
        warnings.append("负载变化后不足 0.25 s；末段误差不能视为已经达到稳态。")
    return {
        "config": cfg,
        "model": {
            "name": "ideal averaged permanent-magnet DC motor",
            "R": R, "L": L, "J": J, "b": B, "Kt": KT, "Ke": KE,
            "max_voltage": MAX_VOLTAGE, "sample_time": SAMPLE_TIME,
            "integration_step": cfg["dt"], "output_period": OUTPUT_PERIOD,
            "equations": ["L*di/dt = u - R*i - Ke*omega",
                          "J*domega/dt = Kt*i - b*omega - load"],
            "reference_rpm": reference,
            "metrics_definitions": {
                "steady_error_pct": "absolute final <=0.25 s mean error / abs(reference); null for zero reference",
                "overshoot_pct": "whole-run peak in reference direction above reference / abs(reference); null at zero",
                "peak_current": "maximum abs(current) over every RK4 substep, in A",
                "settling_time": "seconds after last applied load step (or t=0), within 2% or 1 rpm until end for >=0.1 s; null if not settled",
                "final_rpm": "physical speed at the exact simulation end",
                "saturation_pct": "percentage of simulated duration commanded at either voltage rail",
            },
        },
        "units": {
            "t": "s", "rpm": "rev/min", "measured_rpm": "rev/min",
            "target_rpm": "rev/min", "current": "A", "voltage": "V",
            "torque": "N m", "load": "N m", "kp": "V/(rad/s)", "ki": "V/rad",
            "R": "ohm", "L": "H", "J": "kg m^2", "b": "N m s/rad",
            "Kt": "N m/A", "Ke": "V s/rad",
        },
        "series": series,
        "metrics": metrics,
        "warnings": warnings,
    }


def crosscheck(config: dict | None = None, backend: str = "auto") -> dict:
    """Optional independent OPEN-LOOP reference; no installation side effects.

    backend='scipy' uses adaptive solve_ivp with event-split inputs.
    backend='control' uses an independent two-input LTI state-space response and
    superposition of exact voltage/load steps (no interpolated discontinuity).
    backend='auto' prefers SciPy. Returns available=False if import is missing.
    Closed-loop crosschecking is deliberately rejected: this check validates
    the plant, not a duplicated implementation of the digital PI.
    """
    cfg = validate_config({"mode": "open"} if config is None else config)
    if cfg["mode"] != "open":
        raise ValueError("crosscheck validates the open-loop plant only")
    if backend not in ("auto", "scipy", "control"):
        raise ValueError("backend must be 'auto', 'scipy', or 'control'")
    result = simulate(cfg)
    times = [row["t"] for row in result["series"]]
    selected = backend
    if backend in ("auto", "scipy"):
        try:
            from scipy.integrate import solve_ivp
        except ImportError:
            if backend == "scipy":
                return {"available": False, "backend": "scipy", "reason": "SciPy is not installed"}
            selected = "control"
        else:
            selected = "scipy"
    if selected == "scipy":
        # Equation coefficients are written separately rather than calling _rhs.
        def derivative(load):
            def f(t, x):
                return [(-2.0 * x[0] - 0.05 * x[1] + cfg["voltage"]) / 0.002,
                        (0.05 * x[0] - 0.0001 * x[1] - load) / 0.0002]
            return f
        cuts = [0.0]
        if 0.0 < cfg["load_time"] < cfg["duration"]:
            cuts.append(cfg["load_time"])
        cuts.append(cfg["duration"])
        state = [0.0, 0.0]
        pieces = []
        for a, b in zip(cuts, cuts[1:]):
            solved = solve_ivp(derivative(_load_at(a, cfg)), (a, b), state,
                               rtol=1e-10, atol=1e-12,
                               max_step=0.0005, dense_output=True)
            if not solved.success:
                raise ArithmeticError(solved.message)
            pieces.append((a, b, solved.sol))
            state = solved.y[:, -1]
        reference = []
        for t in times:
            piece = next(p for p in pieces if p[0] - _EPS <= t <= p[1] + _EPS)
            point = piece[2](t)
            reference.append((float(point[0]), float(point[1]) * RPM_PER_RAD_S))
    else:
        try:
            import control
            import numpy as np
        except ImportError:
            return {"available": False, "backend": "control",
                    "reason": "python-control/NumPy is not installed"}
        selected = "control"
        plant = control.ss([[-1000.0, -25.0], [250.0, -0.5]],
                           [[500.0, 0.0], [0.0, -5000.0]],
                           [[1.0, 0.0], [0.0, 1.0]], [[0.0, 0.0], [0.0, 0.0]])
        # forced_response's zero-input path uses matrix exponentials and supports
        # the irregular final sample and non-grid-aligned load time independently.
        matrix_a = np.array([[-1000.0, -25.0], [250.0, -0.5]])
        def constant_step(elapsed, vector):
            equilibrium = -np.linalg.solve(matrix_a, vector)
            if elapsed <= _EPS:
                return np.zeros(2)
            response = control.initial_response(
                plant, timepts=[0.0, elapsed], initial_state=-equilibrium)
            return equilibrium + np.asarray(response.outputs)[:, -1]
        reference = []
        for t in times:
            point = constant_step(t, np.array([500.0 * cfg["voltage"], 0.0]))
            if t >= cfg["load_time"]:
                point += constant_step(t - cfg["load_time"],
                                       np.array([0.0, -5000.0 * cfg["load_Nm"]]))
            reference.append((float(point[0]), float(point[1]) * RPM_PER_RAD_S))
    rpm_error = max(abs(row["rpm"] - ref[1]) for row, ref in zip(result["series"], reference))
    current_error = max(abs(row["current"] - ref[0]) for row, ref in zip(result["series"], reference))
    return {"available": True, "backend": selected,
            "max_abs_rpm_error": rpm_error,
            "max_abs_current_error": current_error,
            "points": len(times),
            "passed": rpm_error < 0.001 and current_error < 0.00001}


if __name__ == "__main__":
    try:
        requested = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
        print(json.dumps(simulate(requested), ensure_ascii=False, allow_nan=False))
    except (ValueError, ArithmeticError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
