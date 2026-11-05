"""Creates disabled trade policies for candidate domestic species."""
from django.core.management.base import BaseCommand

from modules.catalog.models import Species

DEFAULT_SPECIES = (
    ("dogs", "Dogs", "companion"),
    ("cats", "Cats", "companion"),
    ("rabbits", "Rabbits", "companion"),
    ("chickens", "Chickens", "farm"),
    ("goats", "Goats", "farm"),
    ("sheep", "Sheep", "farm"),
    ("cattle", "Cattle", "farm"),
    ("aquarium-fish", "Aquarium fish", "aquatic"),
)


class Command(BaseCommand):
    help = "Seed candidate animal taxonomy; all trading remains disabled by default."

    def handle(self, *args, **kwargs):
        created = 0
        for slug, name, category in DEFAULT_SPECIES:
            _, was_created = Species.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "category": category, "trade_enabled": False},
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Created {created} species; none enabled for commerce."))
