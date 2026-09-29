"""
LKT / SES: what the session endpoint issues, and what it refuses.

Contract tests: they POST to the endpoint the product page uses and read the
token it returns. Nobody joins, so no agent is ever started - token dispatch
only fires when the room is created by a first join. Cost: about a dozen
requests from the shared 100/minute window.

Requirement from the product owner, 2026-09-28: the phone field takes a US
number with or without the +1 country code.
"""

from __future__ import annotations

import pytest

from lkqa import cases, session
from lkqa.bridge import testbed

pytestmark = pytest.mark.contract

LK = testbed.judge_config()["livekit"]
SDK = testbed.config()["livekitSdk"]


@pytest.fixture(scope="module")
def a_caller(r) -> dict[str, str]:
    kb = cases.serial_routed_kbs()[0]
    return cases.caller(r, cases.serial_for(kb["id"], r))


@pytest.fixture(scope="module")
def grant(a_caller) -> session.Grant:
    return session.request_session(a_caller)


def test_lkt01_token_is_room_scoped_with_exactly_the_grants_a_caller_needs(grant, report):
    """LKT-01."""
    video = grant.claims["video"]
    report.record("LKT-01", grants=video, ttlSeconds=grant.ttl_seconds, identity=grant.identity)
    assert video.get("roomJoin") is True
    assert video.get("room") == grant.room and grant.room
    assert video.get("canPublish") and video.get("canSubscribe") and video.get("canPublishData")
    for admin_grant in ("roomAdmin", "roomCreate", "roomList", "roomRecord", "ingressAdmin"):
        assert not video.get(admin_grant), f"a caller token carries {admin_grant}"
    if not video.get("canPublishSources"):
        report.finding(
            "LKT-01",
            "caller tokens may publish ANY source (camera, screen share), not just a microphone",
            grants=video,
        )


def test_lkt01_token_lives_for_the_documented_ttl(grant):
    """LKT-01. A reconnect after the TTL cannot rejoin, so the TTL bounds how
    long a call can survive a network drop."""
    assert grant.ttl_seconds == int(SDK["tokenTtlSeconds"])


def test_lkt02_token_dispatches_exactly_one_agent_by_the_verified_name(grant):
    """LKT-02. The dispatch rides inside the token; this is what makes an agent
    join at all."""
    assert [d["agentName"] for d in grant.dispatches] == [LK["agentName"]]


def test_lkt09_dispatch_metadata_carries_the_intake_form_verbatim(grant, a_caller):
    """LKT-09. The serial in the metadata is what routes the agent to a manual.
    A backend that mangled it would route every call to the wrong machine and
    no browser test would notice."""
    meta = grant.dispatch_metadata
    assert meta["product_serial_number"] == a_caller["serialNumber"]
    assert meta["remote_participant_name"] == a_caller["customerName"]
    assert meta["remote_participant_company"] == a_caller["companyName"]
    assert meta["remote_participant_phone"] == a_caller["phone"]


def test_lkt04_every_session_gets_a_fresh_room_and_identity(grant, a_caller):
    """LKT-04. A reused room inherits the previous caller's conversation."""
    again = session.request_session(a_caller)
    assert again.room != grant.room
    assert again.identity != grant.identity


def test_server_url_is_the_livekit_project_the_suite_observes(grant):
    """If the deployment moved project, every server-side assertion in this
    suite would watch an empty project and pass vacuously."""
    import os

    configured = os.getenv("LIVEKIT_URL")
    if not configured:
        pytest.skip("LIVEKIT_URL not set - nothing to compare")
    assert grant.server_url.rstrip("/") == configured.rstrip("/")


# ---------------------------------------------------------------------------
# Validation - what the endpoint refuses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "phone",
    ["{area}5550142", "+1{area}5550142", "1{area}5550142", "+1 {area} 555 0142", "{area}-555-0142", "({area}) 555-0142"],
    ids=["10-digit", "+1", "1-prefix", "+1-spaced", "dashed", "parenthesised"],
)
def test_ses_phone_accepts_us_numbers_with_and_without_country_code(a_caller, phone):
    """SES-PH-01. The stated requirement. The BROWSER form cannot enter most of
    these (ui/tests/functional/caller-intake.spec.ts) - this pins the backend
    half, so the mismatch is attributable."""
    area = testbed.config()["callerIntake"]["phoneAreaCodes"][0]
    result = session.post_session(session.intake_body({**a_caller, "phone": phone.format(area=area)}))
    assert result.status == 200, f"{phone} -> HTTP {result.status} {result.body}"


@pytest.mark.parametrize("phone", ["555-0100", "12345", "not a phone"], ids=["placeholder", "short", "text"])
def test_ses_phone_rejects_invalid_numbers(a_caller, phone):
    """SES-PH-02. 555-0100 is the form's own placeholder (a known defect)."""
    result = session.post_session(session.intake_body({**a_caller, "phone": phone}))
    assert result.status == 400, f"{phone} -> HTTP {result.status} {result.body}"
    assert any("phone" in m for m in result.body["message"])


@pytest.mark.parametrize(
    "phone",
    ["+44 20 7946 0958", "+91 22 5555 0142", "+52 55 5555 0142", "+61 2 5550 0142", "+49 30 55501420"],
    ids=["uk", "india", "mexico", "australia", "germany"],
)
def test_ses_phone_rejects_non_us_numbers(a_caller, phone):
    """SES-PH-03. REQUIREMENT (product owner, 2026-09-28): only US numbers are
    accepted. A foreign number must be refused by the backend, not just by the
    browser field."""
    result = session.post_session(session.intake_body({**a_caller, "phone": phone}))
    assert result.status == 400, f"non-US number {phone} was accepted: HTTP {result.status}"


@pytest.mark.parametrize("phone", ["+1 416 555 0142", "4165550142", "+1 604 555 0142"], ids=["toronto+1", "toronto", "vancouver"])
def test_ses_phone_rejects_canadian_numbers(a_caller, phone):
    """SES-PH-04. Canada shares +1 with the US (NANP), so it is the one foreign
    number a US-looking validator could let through. VERIFIED 2026-09-28: the
    backend refuses it - pinned, because "US only" is the requirement."""
    result = session.post_session(session.intake_body({**a_caller, "phone": phone}))
    assert result.status == 400, f"Canadian number {phone} was accepted: HTTP {result.status}"


def test_ses_every_missing_field_is_named_in_the_400(report):
    """SES-VAL-01. An empty body must list all four problems, not the first."""
    result = session.post_session({})
    assert result.status == 400
    text = " ".join(result.body["message"]).lower()
    for field in ("serialnumber", "customername", "companyname", "phone"):
        assert field in text.replace(" ", ""), f"{field} not named: {result.body}"
    report.finding(
        "SES-VAL-01",
        "validation messages name DTO fields (serialNumber) while the request uses serial_number",
        body=result.body,
    )


def test_ses_unknown_product_is_a_404_not_a_session():
    """SES-VAL-02. Fail-closed: no token for a product that does not exist."""
    result = session.post_session(
        session.intake_body(
            {"serialNumber": "K7170", "customerName": "QA", "companyName": "QA", "phone": "4805550142"}
        ),
        product="definitely-not-a-real-product",
    )
    assert result.status == 404


def test_res09_serial_rules_differ_between_ui_and_api(a_caller, report):
    """RES-09 (contract half). The form only allows letters and digits; the API
    takes anything. Recorded, because which one is right is a product call."""
    result = session.post_session(session.intake_body({**a_caller, "serialNumber": "K-7170"}))
    if result.status == 200:
        report.finding("RES-09", "the API issues a session for serial 'K-7170', which the browser form refuses")
    assert result.status in (200, 400)


def test_res09_an_unknown_serial_still_gets_a_session(a_caller, report):
    """RES-09. What the caller then hears is the agent's handling, tested live
    in test_resilience.py."""
    result = session.post_session(session.intake_body({**a_caller, "serialNumber": SDK["unknownSerial"]}))
    report.record("RES-09-contract", status=result.status)
    assert result.status == 200
