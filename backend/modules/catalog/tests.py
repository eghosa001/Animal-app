"""Initial catalogue cannot accidentally allow trading."""
from rest_framework.test import APITestCase

from .models import Species


class CatalogTests(APITestCase):
    def test_taxonomy_has_trading_disabled_by_default(self):
        species = Species.objects.create(name="Dogs", slug="dogs", category=Species.Category.COMPANION)
        self.assertFalse(species.trade_enabled)
        result = self.client.get("/api/v1/catalog/species")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data[0]["name"], "Dogs")
        self.assertFalse(result.data[0]["trade_enabled"])
