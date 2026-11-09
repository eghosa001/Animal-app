"""Bootstrap a primary staff authenticator from a trusted interactive server shell.

Never run this command through CI, deploy logs, GitHub Actions or remote chat.
"""
import getpass
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_otp.plugins.otp_totp.models import TOTPDevice

from modules.accounts.models import User


class Command(BaseCommand):
    help = "Interactively enroll a verified staff member's primary TOTP device."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Staff email (not a token)")

    def handle(self, *args, **options):
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise CommandError("Staff TOTP enrollment requires a private interactive TTY.")
        user = User.objects.filter(email__iexact=options["email"]).first()
        if user is None or not user.is_active or not user.is_staff or not user.is_email_verified:
            raise CommandError("An active, email-verified staff account is required.")
        if TOTPDevice.objects.filter(user=user, confirmed=True).exists():
            raise CommandError("A confirmed authenticator already exists. Use the documented recovery procedure.")
        if TOTPDevice.objects.filter(user=user, confirmed=False).exists():
            raise CommandError("Unconfirmed setup exists. Remove it using an authorized database recovery procedure.")

        device = TOTPDevice.objects.create(user=user, name="Primary authenticator", confirmed=False)
        try:
            self.stdout.write(
                "\nThis setup URI contains a secret. Do not copy it to tickets, logs or chat.\n"
                "Import it into your authenticator app on a trusted device:\n\n"
                + device.config_url + "\n"
            )
            code = getpass.getpass("Enter the current 6-digit code from the authenticator: ").strip()
            if not code.isdigit() or len(code) != 6:
                raise CommandError("A six-digit authenticator code is required.")
            with transaction.atomic():
                device = TOTPDevice.objects.select_for_update().get(pk=device.pk)
                if not device.verify_token(code):
                    raise CommandError("Authenticator code rejected; enrollment was not saved.")
                device.confirmed = True
                device.save(update_fields=["confirmed"])
        except BaseException:
            if not device.confirmed:
                device.delete()
            raise

        self.stdout.write(self.style.SUCCESS(
            "Authenticator enrollment verified. Admin access now requires this second factor."
        ))
