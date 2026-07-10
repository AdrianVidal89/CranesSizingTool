"""A saved CalculationRun's stored input, replayed through the calculation
engine again, must reproduce the exact stored result (CLAUDE.md: a
CalculationRun is a frozen snapshot, never recomputed from mutable
references — but replaying the same frozen input must be deterministic).
"""

from tests.conftest import SAVE_CALCULATION_RUN_PAYLOAD, register_and_login


def test_replaying_stored_input_reproduces_stored_result(make_client):
    client = make_client()
    csrf_token = register_and_login(client, "repro@example.com")

    save_response = client.post(
        "/api/calculation-runs",
        json=SAVE_CALCULATION_RUN_PAYLOAD,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert save_response.status_code == 201
    saved = save_response.json()

    fetched = client.get(f"/api/calculation-runs/{saved['id']}")
    assert fetched.status_code == 200
    run = fetched.json()

    # Replay the exact stored input through the (stateless) calculation
    # endpoint and compare against the exact stored result.
    replay_response = client.post("/api/calc/validate-candidate", json=run["input_snapshot"])
    assert replay_response.status_code == 200
    assert replay_response.json() == run["result_snapshot"]


def test_saved_result_matches_direct_calculation_at_save_time(make_client):
    """The result stored at save time already equals what a direct call to
    the calculation endpoint with the same inputs produces (no drift
    introduced by the persistence round-trip)."""
    client = make_client()
    csrf_token = register_and_login(client, "repro2@example.com")

    calc_only_payload = {
        k: v
        for k, v in SAVE_CALCULATION_RUN_PAYLOAD.items()
        if k
        not in {
            "new_project_name",
            "crane_configuration_name",
            "movement_kind",
            "movement_name",
        }
    }
    direct_response = client.post("/api/calc/validate-candidate", json=calc_only_payload)
    assert direct_response.status_code == 200

    save_response = client.post(
        "/api/calculation-runs",
        json=SAVE_CALCULATION_RUN_PAYLOAD,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert save_response.status_code == 201

    assert save_response.json()["result_snapshot"] == direct_response.json()
