import 'package:anima_app/core/api_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('animal listing parses approved photo paths without exposing storage keys', () {
    final listing = AnimalListing.fromJson({
      'id': 'sample-id',
      'title': 'A friendly sample dog',
      'description': 'Preview content',
      'species': {'name': 'Dogs'},
      'animal_name': 'Example',
      'seller_name': 'Verified Demo',
      'region': 'Lagos',
      'currency': 'NGN',
      'price_minor': 25000000,
      'photo_urls': ['/api/v1/media/12345678-1234-1234-1234-123456789012/file/'],
    });
    expect(listing.photoUrls.length, 1);
    expect(listing.photoUrls.first.startsWith('/api/v1/media/'), isTrue);
    expect(listing.displayPrice.startsWith('₦'), isTrue);
  });

  test('animal listing is safe when the photo array is absent', () {
    final listing = AnimalListing.fromJson({'id': 'demo', 'title': 'Demo'});
    expect(listing.photoUrls, isEmpty);
  });
}
