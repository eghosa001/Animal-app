/// An unfunded order request, not an animal reservation or completed purchase.
class OrderIntentReceipt {
  const OrderIntentReceipt({
    required this.id,
    required this.acceptedOfferId,
    required this.listingTitle,
    required this.animalName,
    required this.region,
    required this.priceMinor,
    required this.currency,
    required this.status,
    required this.buyerName,
    required this.sellerName,
    required this.checkoutAvailable,
    required this.fundsSecured,
    required this.animalReserved,
  });

  final String id;
  final String acceptedOfferId;
  final String listingTitle;
  final String animalName;
  final String region;
  final int priceMinor;
  final String currency;
  final String status;
  final String buyerName;
  final String sellerName;
  final bool checkoutAvailable;
  final bool fundsSecured;
  final bool animalReserved;

  factory OrderIntentReceipt.fromJson(Map<String, dynamic> json) =>
      OrderIntentReceipt(
        id: json['id']?.toString() ?? '',
        acceptedOfferId: json['accepted_offer']?.toString() ?? '',
        listingTitle: json['listing_title_snapshot']?.toString() ?? '',
        animalName: json['animal_name_snapshot']?.toString() ?? '',
        region: json['listing_region_snapshot']?.toString() ?? '',
        priceMinor: (json['price_minor'] as num?)?.toInt() ?? 0,
        currency: json['currency']?.toString() ?? '',
        status: json['status']?.toString() ?? '',
        buyerName: json['buyer_name']?.toString() ?? '',
        sellerName: json['seller_name']?.toString() ?? '',
        checkoutAvailable: json['checkout_available'] == true,
        fundsSecured: json['funds_secured'] == true,
        animalReserved: json['animal_reserved'] == true,
      );

  String get priceDisplay {
    final major = priceMinor ~/ 100;
    final minor = (priceMinor % 100).toString().padLeft(2, '0');
    return '${currency == 'NGN' ? '₦' : '$currency '}$major.$minor';
  }

  String get statusLabel {
    switch (status) {
      case 'awaiting_partner':
        return 'Awaiting authorized checkout provider';
      case 'cancelled':
        return 'Cancelled before payment';
      default:
        return 'Unrecognized order request state';
    }
  }
}
