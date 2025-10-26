import pytest

from src.cardiac import VanDerPolOscillator
from src.coupling import CouplingParameters, HeartBrainCouplingModel
from src.neural import FitzHughNagumo


@pytest.mark.parametrize(
    "state,input_drive,expected",
    [
        ((0.0, 0.0), 0.0, (0.0, pytest.approx(0.7 / 3.0))),
        ((1.0, -0.5), 0.1, (pytest.approx(1.0 - (1.0 ** 3) / 3.0 + 0.5 + 0.1), pytest.approx((1.0 + 0.7 - 0.8 * -0.5) / 3.0))),
    ],
)
def test_fitzhugh_nagumo_derivatives(state, input_drive, expected):
    model = FitzHughNagumo()
    dv, dw = model.derivatives(0.0, state, input_drive=input_drive)
    expected_dv, expected_dw = expected
    assert dv == expected_dv
    assert dw == expected_dw


def test_van_der_pol_derivatives_basic():
    model = VanDerPolOscillator()
    dx, dy = model.derivatives(0.0, (1.0, 0.0))
    assert dx == 0.0
    assert dy == pytest.approx(-model.omega ** 2)


def test_coupled_simulation_produces_expected_timesteps():
    model = HeartBrainCouplingModel(
        coupling=CouplingParameters(neural_to_cardiac_gain=0.0, cardiac_to_neural_gain=0.0)
    )
    trajectory = model.simulate(initial_state=(0.0, 0.0, 1.0, 0.0), t_span=(0.0, 0.5), dt=0.1)
    times = [time for time, _ in trajectory]
    assert times[0] == pytest.approx(0.0)
    assert times[-1] == pytest.approx(0.5)
    assert len(times) == 6


def test_delay_lookup_uses_history_when_available():
    model = HeartBrainCouplingModel()
    model.history.append((0.0, (1.0, 0.5), (2.0, 1.5)))
    model.history.append((0.1, (1.1, 0.6), (2.1, 1.6)))
    delayed_neural = model._delayed_state(0.2, 0.1, "neural", (0.0, 0.0))
    delayed_cardiac = model._delayed_state(0.2, 0.1, "cardiac", (0.0, 0.0))
    assert delayed_neural == (1.1, 0.6)
    assert delayed_cardiac == (2.1, 1.6)
