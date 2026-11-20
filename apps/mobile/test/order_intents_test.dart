import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/core/chat_models.dart';
import 'package:anima_app/core/offer_models.dart';
import 'package:anima_app/core/order_intent_models.dart';
import 'package:anima_app/offer_negotiation_page.dart';
import 'package:anima_app/order_intents_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const buyerId = '00000000-0000-0000-0000-000000000011';
const sellerId = '00000000-0000-0000-0000-000000000012';
const offerId = '00000000-0000-0000-0000-000000000013';
const orderId = '00000000-0000-0000-0000-000000000014';
const chatId = '00000000-0000-0000-0000-000000000015';
const listingId = '00000000-0000-0000-0000-000000000016';

const acceptedChat = ChatConversation(
  id: chatId,
  listingId: listingId,
  listingTitle: 'Approved companion animal',
  counterpartyName: 'Breeder',
  counterpartyId: sellerId,
  buyerId: buyerId,
  canSend: true,
  updatedAt: null,
);

const acceptedQuote = AnimalOfferQuote(
  id: offerId,
  proposerId: sellerId,
  proposerName: 'Breeder',
  amountMinor: 35005050,
  currency: 'NGN',
  status: 'accepted',
  expiresAt: null,
);

const initialReceipt = OrderIntentReceipt(
  id: orderId,
  acceptedOfferId: offerId,
  listingTitle: 'Approved companion animal',
  animalName: 'Bella',
  region: 'Benin City',
  priceMinor: 35005050,
  currency: 'NGN',
  status: 'awaiting_partner',
  buyerName: 'Buyer',
  sellerName: 'Breeder',
  checkoutAvailable: false,
  fundsSecured: false,
  animalReserved: false,
);

class FakeOrderApi extends ApiClient {
  FakeOrderApi({this.isSeller = false});
  final bool isSeller;
  final orders = <OrderIntentReceipt>[];
  int created = 0;
  int cancelled = 0;
  String? createdNonce;
  String? cancelReason;
  bool failCreate = false;

  @override
  Future<Map<String, dynamic>?> me() async => {
    'id': isSeller ? sellerId : buyerId,
    'email_verified': true,
  };

  @override
  Future<List<AnimalOfferQuote>> getConversationOffers(String conversationId) async {
    expect(conversationId, chatId);
    return [acceptedQuote];
  }

  @override
  Future<OrderIntentReceipt> createUnfundedOrderIntent(
    String acceptedOfferId, {required String requestNonce}
  ) async {
    expect(acceptedOfferId, offerId);
    created++;
    createdNonce = requestNonce;
    if (failCreate) throw const ApiFailure('Request could not be saved');
    if (orders.isEmpty) orders.add(initialReceipt);
    return orders.first;
  }

  @override
  Future<List<OrderIntentReceipt>> getMyOrderIntents() async => List.of(orders);

  @override
  Future<OrderIntentReceipt> cancelUnfundedOrderIntent(
    String intentId, String reason,
  ) async {
    expect(intentId, orderId);
    cancelled++;
    cancelReason = reason;
    final updated = OrderIntentReceipt(
      id: initialReceipt.id,
      acceptedOfferId: initialReceipt.acceptedOfferId,
      listingTitle: initialReceipt.listingTitle,
      animalName: initialReceipt.animalName,
      region: initialReceipt.region,
      priceMinor: initialReceipt.priceMinor,
      currency: initialReceipt.currency,
      status: 'cancelled',
      buyerName: initialReceipt.buyerName,
      sellerName: initialReceipt.sellerName,
      checkoutAvailable: false,
      fundsSecured: false,
      animalReserved: false,
    );
    orders
      ..clear()
      ..add(updated);
    return updated;
  }
}

void main() {
  test('order receipt parses immutable NGN minor-unit snapshot', () {
    final result = OrderIntentReceipt.fromJson({
      'id': orderId,
      'accepted_offer': offerId,
      'listing_title_snapshot': 'Approved companion animal',
      'animal_name_snapshot': 'Bella',
      'listing_region_snapshot': 'Benin City',
      'price_minor': 35005050,
      'currency': 'NGN',
      'status': 'awaiting_partner',
      'buyer_name': 'Buyer',
      'seller_name': 'Breeder',
      'checkout_available': false,
      'funds_secured': false,
      'animal_reserved': false,
    });
    expect(result.priceDisplay, '₦350050.50');
    expect(result.statusLabel, 'Awaiting authorized checkout provider');
    expect(result.checkoutAvailable, false);
    expect(result.fundsSecured, false);
    expect(result.animalReserved, false);
  });

  testWidgets('buyer must confirm no checkout before saving order request',
      (tester) async {
    final api = FakeOrderApi();
    await tester.pumpWidget(MaterialApp(
      home: OfferNegotiationPage(api: api, conversation: acceptedChat),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Save unfunded order request'), findsOneWidget);
    await tester.tap(find.byKey(const Key('prepare-unfunded-order')));
    await tester.pumpAndSettle();
    expect(api.created, 0);
    expect(find.textContaining('NO checkout, payment'), findsOneWidget);
    await tester.tap(find.text('Not now'));
    await tester.pumpAndSettle();
    expect(api.created, 0);
    await tester.tap(find.byKey(const Key('prepare-unfunded-order')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('I understand — save request'));
    await tester.pumpAndSettle();
    expect(api.created, 1);
    expect(api.createdNonce, isNotEmpty);
    expect(find.text('Order requests'), findsOneWidget);
    expect(find.text('No payment received • No reservation'), findsOneWidget);
    api.dispose();
  });

  testWidgets('seller cannot submit buyer-only order requests', (tester) async {
    final api = FakeOrderApi(isSeller: true);
    await tester.pumpWidget(MaterialApp(
      home: OfferNegotiationPage(api: api, conversation: acceptedChat),
    ));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('prepare-unfunded-order')), findsNothing);
    expect(api.created, 0);
    api.dispose();
  });

  testWidgets('private order can be cancelled with explicit reason only',
      (tester) async {
    final api = FakeOrderApi()..orders.add(initialReceipt);
    await tester.pumpWidget(MaterialApp(
      home: OrderIntentsPage(api: api),
    ));
    await tester.pumpAndSettle();
    expect(find.text('₦350050.50'), findsOneWidget);
    await tester.tap(find.byKey(const Key('cancel-intent')));
    await tester.pumpAndSettle();
    expect(api.cancelled, 0);
    await tester.tap(find.text('Keep request'));
    await tester.pumpAndSettle();
    expect(api.cancelled, 0);
    await tester.tap(find.byKey(const Key('cancel-intent')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('cancel-order-reason')),
      'I am cancelling because the purchase is not proceeding.',
    );
    await tester.tap(find.byKey(const Key('confirm-cancel-request')));
    await tester.pumpAndSettle();
    expect(api.cancelled, 1);
    expect(api.cancelReason, contains('not proceeding'));
    expect(find.text('Cancelled before payment'), findsOneWidget);
    expect(find.byKey(const Key('cancel-intent')), findsNothing);
    api.dispose();
  });
}
