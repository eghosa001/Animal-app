import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/seller_media_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeSellerApi extends ApiClient {
  @override
  Future<List<Map<String, dynamic>>> getMyListings() async => [];

  @override
  Future<List<Map<String, dynamic>>> getMyMedia() async => [];
}

void main() {
  testWidgets('seller media UI starts private and disables upload until a file is chosen',
      (tester) async {
    final api = FakeSellerApi();
    await tester.pumpWidget(MaterialApp(home: SellerMediaPage(api: api)));
    await tester.pumpAndSettle();

    expect(find.text('Seller media'), findsOneWidget);
    expect(find.text('Upload securely'), findsOneWidget);
    expect(find.text('Animal photos'), findsOneWidget);
    expect(find.text('Verification'), findsOneWidget);
    expect(find.textContaining('You have no draft listings yet.'), findsOneWidget);
    final upload = find.widgetWithText(FilledButton, 'Upload for review');
    expect(tester.widget<FilledButton>(upload).onPressed, isNull);

    await tester.tap(find.text('Verification'));
    await tester.pumpAndSettle();
    expect(find.text('Verification document category'), findsOneWidget);
    expect(find.textContaining('maximum 5 MB'), findsOneWidget);
    expect(tester.widget<FilledButton>(upload).onPressed, isNull);
    api.dispose();
  });
}
