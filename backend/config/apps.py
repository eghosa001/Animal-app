"""Override Django's default admin with OTP-gated staff access."""
from django.contrib.admin.apps import AdminConfig


class SecureAdminConfig(AdminConfig):
    default_site = "config.secure_admin.SecureAdminSite"
