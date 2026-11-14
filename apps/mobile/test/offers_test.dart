import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/core/chat_models.dart';
import 'package:anima_app/core/offer_models.dart';
import 'package:anima_app/offer_negotiation_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const conversationId = '00000000-0000-0000-0000-000000000001';
const buyerId = '00000000-0000-0000-0000-000000000002';
const sellerId = '00000000-0000-0000-0000-000000000003';

const chat = ChatConversation(
  id: conversationId,
  listingId: '00000000-0000-0000-0000-000000000004',
  listingTitle: 'Approved animal listing',
  counterpartyName: 'Animal Seller',
  counterpartyId: sellerId,
  canSend: true,
  updatedAt: null,
);

class FakeOfferApi extends ApiClient {
  final quotes = <AnimalOfferQuote>[];
  int proposes = 0;
  int decisions = 0;
  int? lastAmount;
  String? lastNonce;

  @override
  Future<Map<String, dynamic>?> me() async => {
    'id': buyerId,
    'display_name': 'Buyer',
  };

  @override
  Future<List<AnimalOfferQuote>> getConversationOffers(String id) async {
    expect(id, conversationId);
    return List.of(quotes);
  }

  @override
  Future<AnimalOfferQuote> proposeAnimalOffer(
      String id, int amountMinor, {required String clientNonce}) async {
    expect(id, conversationId);
    proposes++;
    lastAmount = amountMinor;
    lastNonce = clientNonce;
    final quote = AnimalOfferQuote(
      id: '00000000-0000-0000-0000-000000000005',
      proposerId: buyerId,
      proposerName: 'Buyer',
      amountMinor: amountMinor,
      currency: 'NGN',
      status: 'pending',
      expiresAt: null,
    );
    quotes.insert(0, quote);
    return quote;
  }

  @override
  Future<AnimalOfferQuote> decideAnimalOffer(
      String id, String decision) async {
    decisions++;
    final old = quotes.firstWhere((x) => x.id == id);
    final updated = AnimalOfferQuote(
      id: old.id,
      proposerId: old.proposerId,
      proposerName: old.proposerName,
      amountMinor: old.amountMinor,
      currency: old.currency,
      status: decision == 'accept' ? 'accepted' : 'declined',
      expiresAt: old.expiresAt,
    );
    quotes[quotes.indexOf(old)] = updated;
    return updated;
  }
}

void main() {
  test('minor amounts display without floating-point rounding', () {
    const quote = AnimalOfferQuote(
      id: 'id',
      proposerId: buyerId,
      proposerName: 'Buyer',
      amountMinor: 250050,
      currency: 'NGN',
      status: 'pending',
      expiresAt: null,
    );
    expect(quote.amountDisplay, '₦2500.50');
  });

  testWidgets('creates a quoted price, not a payment or escrow record',
      (tester) async {
    final api = FakeOfferApi();
    await tester.pumpWidget(MaterialApp(
      home: OfferNegotiationPage(api: api, conversation: chat),
    ));
    await tester.pumpAndSettle();
    expect(find.text('No price proposals yet.'), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('offer-amount')), '300000.50',
    );
    await tester.tap(find.byKey(const Key('submit-offer')));
    await tester.pumpAndSettle();
    expect(api.proposes, 1);
    expect(api.lastAmount, 30000050);
    expect(api.lastNonce, isNotNull);
    expect(find.text('₦300000.50'), findsOneWidget);
    expect(find.textContaining('Anima has not received or protected any funds'),
        findsOneWidget);
    api.dispose();
  });

  testWidgets('recipient acceptance requires clear payment disclaimer',
      (tester) async {
    final api = FakeOfferApi();
    api.quotes.add(const AnimalOfferQuote(
      id: '00000000-0000-0000-0000-000000000005',
      proposerId: sellerId,
      proposerName: 'Animal Seller',
      amountMinor: 25000000,
      currency: 'NGN',
      status: 'pending',
      expiresAt: null,
    ));
    await tester.pumpWidget(MaterialApp(
      home: OfferNegotiationPage(api: api, conversation: chat),
    ));
    await tester.pumpAndSettle();
    await tester.ensureVisible(find.text('Accept price'));
    await tester.tap(find.text('Accept price'));
    await tester.pumpAndSettle();
    expect(api.decisions, 0);
    expect(find.textContaining('No payment is made here'), findsOneWidget);
    await tester.tap(find.text('Agree to price'));
    await tester.pumpAndSettle();
    expect(api.decisions, 1);
    expect(find.text('Price agreed. Payment and protected checkout remain unavailable.'),
        findsOneWidget);
    api.dispose();
  });
}
