"""Staff MFA fixture helper for Django/DRF regression tests only."""
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice


def verify_staff_test_session(client, user):
    """Simulate a *confirmed* device in a test session; never use in production code."""
    client.force_authenticate(user=None)
    client.force_login(user)
    device = TOTPDevice.objects.create(
        user=user, name="Test authenticator", confirmed=True,
    )
    session = client.session
    session[DEVICE_ID_SESSION_KEY] = device.persistent_id
    session.save()
    return device
