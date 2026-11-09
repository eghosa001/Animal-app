"""Admin access requires a verified second factor, including custom admin actions."""
from django_otp.admin import OTPAdminSite


class SecureAdminSite(OTPAdminSite):
    # Keep existing admin: names and URL reversals unchanged.
    def __init__(self, name="admin"):
        super().__init__(name=name)

    site_header = "Anima Platform Administration"
    site_title = "Anima Staff"
