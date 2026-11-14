import 'package:anima_app/chat_inbox_page.dart';
import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/core/chat_models.dart';
import 'package:anima_app/listing_detail_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const testListingId = '00000000-0000-0000-0000-000000000001';
const testConversationId = '00000000-0000-0000-0000-000000000002';

const testConversation = ChatConversation(
  id: testConversationId,
  listingId: testListingId,
  listingTitle: 'Healthy companion dog',
  counterpartyName: 'Approved breeder',
  canSend: true,
  updatedAt: null,
);

class FakeChatApi extends ApiClient {
  final messages = <ChatMessage>[];
  String? submittedText;
  String? submittedNonce;
  int starts = 0;
  bool requireLogin = false;

  @override
  Future<List<ChatConversation>> getMyConversations() async {
    if (requireLogin) {
      throw const ApiFailure('Sign in to message animal sellers');
    }
    return [testConversation];
  }

  @override
  Future<ChatConversation> startChatForListing(String listingId) async {
    starts++;
    expect(listingId, testListingId);
    return testConversation;
  }

  @override
  Future<ChatMessagePage> getConversationMessages(
    String conversationId, {int page = 1},
  ) async {
    expect(conversationId, testConversationId);
    return ChatMessagePage(
      messages: messages.reversed.toList(),
      hasMore: false,
    );
  }

  @override
  Future<ChatMessage> sendChatMessage(
    String conversationId, String body,
    {required String clientNonce},
  ) async {
    expect(conversationId, testConversationId);
    submittedText = body;
    submittedNonce = clientNonce;
    final created = ChatMessage(
      id: '00000000-0000-0000-0000-000000000003',
      senderId: testListingId,
      senderName: 'Buyer',
      body: body,
      createdAt: null,
      clientNonce: clientNonce,
    );
    messages.add(created);
    return created;
  }

  @override
  Future<AnimalListing> getListing(String id) async {
    return const AnimalListing(
      id: testListingId,
      title: 'Healthy companion dog',
      description: 'An independently moderated animal listing.',
      speciesName: 'Dogs',
      animalName: 'Bella',
      sellerName: 'Approved breeder',
      region: 'Lagos',
      currency: 'NGN',
      priceMinor: 250050,
      photoUrls: [],
    );
  }
}

void main() {
  test('chat model keeps only supported public display fields', () {
    final parsed = ChatConversation.fromJson({
      'id': testConversationId,
      'listing': testListingId,
      'listing_title': 'Healthy companion dog',
      'counterparty_name': 'Approved breeder',
      'can_send': false,
      'updated_at': '2026-11-14T12:00:00Z',
    });
    expect(parsed.canSend, isFalse);
    expect(parsed.updatedAt!.isUtc, isTrue);
  });

  test('message nonce is securely randomized and well-formed', () {
    final first = ApiClient.newChatNonce();
    final second = ApiClient.newChatNonce();
    expect(first, matches(RegExp(
      r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    )));
    expect(first, isNot(second));
  });

  testWidgets('inbox navigates to a private conversation and sends a message',
      (tester) async {
    final api = FakeChatApi();
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ChatInboxPage(api: api, openAccount: () {}),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Approved breeder'), findsOneWidget);
    expect(find.text('Healthy companion dog'), findsOneWidget);
    await tester.tap(find.text('Approved breeder'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Off-platform payments'), findsOneWidget);
    await tester.enterText(
      find.byType(TextField), 'Is the animal available for a visit?',
    );
    await tester.tap(find.byTooltip('Send message'));
    await tester.pumpAndSettle();
    expect(api.submittedText, 'Is the animal available for a visit?');
    expect(api.submittedNonce, isNotNull);
    expect(find.text('Is the animal available for a visit?'), findsOneWidget);
    api.dispose();
  });

  testWidgets('inbox asks a signed-out buyer to sign in', (tester) async {
    final api = FakeChatApi()..requireLogin = true;
    var opened = false;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ChatInboxPage(
          api: api,
          openAccount: () => opened = true,
        ),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Sign in to see your private conversations.'),
        findsOneWidget);
    await tester.tap(find.text('Go to profile'));
    expect(opened, isTrue);
    api.dispose();
  });

  testWidgets('an approved animal detail opens its seller conversation',
      (tester) async {
    final api = FakeChatApi();
    await tester.pumpWidget(
      MaterialApp(home: ListingDetailPage(api: api, listingId: testListingId)),
    );
    await tester.pumpAndSettle();
    expect(find.text('Message seller'), findsOneWidget);
    await tester.ensureVisible(find.text('Message seller'));
    await tester.tap(find.text('Message seller'));
    await tester.pumpAndSettle();
    expect(api.starts, 1);
    expect(find.text('Approved breeder'), findsOneWidget);
    api.dispose();
  });
}
