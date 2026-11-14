/// Participant-visible price negotiation; no charge or escrow is represented.
class AnimalOfferQuote {
  const AnimalOfferQuote({
    required this.id,
    required this.proposerId,
    required this.proposerName,
    required this.amountMinor,
    required this.currency,
    required this.status,
    required this.expiresAt,
    this.replacesId,
  });
  final String id;
  final String proposerId;
  final String proposerName;
  final int amountMinor;
  final String currency;
  final String status;
  final DateTime? expiresAt;
  final String? replacesId;

  factory AnimalOfferQuote.fromJson(Map<String, dynamic> json) {
    return AnimalOfferQuote(
      id: json['id']?.toString() ?? '',
      proposerId: json['proposer_id']?.toString() ?? '',
      proposerName: json['proposer_name']?.toString() ?? '',
      amountMinor: (json['amount_minor'] as num?)?.toInt() ?? 0,
      currency: json['currency']?.toString() ?? 'NGN',
      status: json['status']?.toString() ?? '',
      expiresAt: DateTime.tryParse(json['expires_at']?.toString() ?? ''),
      replacesId: json['replaces']?.toString(),
    );
  }

  String get amountDisplay {
    final whole = amountMinor ~/ 100;
    final fraction = (amountMinor % 100).toString().padLeft(2, '0');
    return '${currency == 'NGN' ? '₦' : '$currency '}$whole.$fraction';
  }
}
