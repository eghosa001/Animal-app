import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/core/listing_models.dart';
import 'package:anima_app/seller_listings_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeListingApi extends ApiClient {
  FakeListingApi({this.showDraft = false});

  final bool showDraft;

  @override
  Future<Map<String, dynamic>?> me() async => {
    'email': 'seller@example.com',
    'email_verified': true,
    'seller_status': 'pending',
  };

  @override
  Future<List<SpeciesOption>> getSpecies() async => [
    const SpeciesOption(
      id: 1,
      name: 'Dogs',
      slug: 'dogs',
      category: 'companion',
      tradeEnabled: false,
    ),
  ];

  @override
  Future<List<Map<String, dynamic>>> getMyListings() async => showDraft
      ? [
          {
            'id': '00000000-0000-0000-0000-000000000001',
            'title': 'Sample dog listing',
            'description': 'A private draft for UI testing only.',
            'price_minor': 1250000,
            'currency': 'NGN',
            'region': 'Abuja',
            'status': 'draft',
            'animal_name': 'Bella',
            'sex': 'female',
            'species': {'id': 1, 'name': 'Dogs', 'trade_enabled': false},
          },
        ]
      : [];

  @override
  Future<List<Map<String, dynamic>>> getMyMedia() async => [];
}

void main() {
  testWidgets('create tab opens animal listing form with private draft messaging',
      (tester) async {
    final api = FakeListingApi();
    await tester.pumpWidget(MaterialApp(home: SellerListingsPage(api: api)));
    await tester.pumpAndSettle();

    expect(find.text('Manage animal listings'), findsOneWidget);
    expect(find.text('Create listing'), findsOneWidget);
    expect(find.textContaining('pending'), findsWidgets);

    await tester.tap(find.text('Create listing'));
    await tester.pumpAndSettle();

    expect(find.text('Create animal listing'), findsOneWidget);
    expect(find.text('Individual animal'), findsOneWidget);
    expect(find.text('Animal category'), findsOneWidget);
    expect(find.text('Save private draft'), findsOneWidget);
    expect(find.text('Save and manage photos'), findsOneWidget);
    api.dispose();
  });

  testWidgets('disabled species and pending seller cannot submit a draft',
      (tester) async {
    final api = FakeListingApi(showDraft: true);
    await tester.pumpWidget(MaterialApp(home: SellerListingsPage(api: api)));
    await tester.pumpAndSettle();

    expect(find.text('Sample dog listing'), findsOneWidget);
    expect(find.textContaining('disabled for trading'), findsOneWidget);
    expect(find.text('Edit draft'), findsOneWidget);
    expect(find.text('Manage photos'), findsOneWidget);
    final submit = find.widgetWithText(FilledButton, 'Submit for review');
    expect(tester.widget<FilledButton>(submit).onPressed, isNull);
    api.dispose();
  });
}
