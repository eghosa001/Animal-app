/// Listing-linked, authenticated buyer/seller messaging API objects.
class ChatConversation {
  const ChatConversation({
    required this.id,
    required this.listingId,
    required this.listingTitle,
    required this.counterpartyName,
    this.counterpartyId = '',
    required this.canSend,
    required this.updatedAt,
  });

  final String id;
  final String listingId;
  final String listingTitle;
  final String counterpartyName;
  final String counterpartyId;
  final bool canSend;
  final DateTime? updatedAt;

  factory ChatConversation.fromJson(Map<String, dynamic> data) {
    return ChatConversation(
      id: data['id']?.toString() ?? '',
      listingId: data['listing']?.toString() ?? '',
      listingTitle: data['listing_title']?.toString() ?? 'Animal listing',
      counterpartyName: data['counterparty_name']?.toString() ?? 'Participant',
      counterpartyId: data['counterparty_id']?.toString() ?? '',
      canSend: data['can_send'] == true,
      updatedAt: DateTime.tryParse(data['updated_at']?.toString() ?? ''),
    );
  }
}

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.senderId,
    required this.senderName,
    required this.body,
    required this.createdAt,
    required this.clientNonce,
  });
  final String id;
  final String senderId;
  final String senderName;
  final String body;
  final DateTime? createdAt;
  final String clientNonce;

  factory ChatMessage.fromJson(Map<String, dynamic> data) => ChatMessage(
        id: data['id']?.toString() ?? '',
        senderId: data['sender']?.toString() ?? '',
        senderName: data['sender_name']?.toString() ?? '',
        body: data['body']?.toString() ?? '',
        createdAt: DateTime.tryParse(data['created_at']?.toString() ?? ''),
        clientNonce: data['client_nonce']?.toString() ?? '',
      );
}

class ChatMessagePage {
  const ChatMessagePage({required this.messages, required this.hasMore});
  final List<ChatMessage> messages;
  final bool hasMore;
}
