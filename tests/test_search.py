from src.healthtech_search import patient_safe_level


def test_urgent_patient_notice_is_escalated():
    assert patient_safe_level("Patient reports chest pain after treatment") == "urgent"
    assert patient_safe_level("Bring your medication list") == "routine"
