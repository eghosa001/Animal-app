/// Catalog rows are policy candidates; not an assertion that commercial trade is legal.
class SpeciesOption {
  const SpeciesOption({
    required this.id,
    required this.name,
    required this.slug,
    required this.category,
    required this.tradeEnabled,
  });

  final int id;
  final String name;
  final String slug;
  final String category;
  final bool tradeEnabled;

  factory SpeciesOption.fromJson(Map<String, dynamic> json) {
    return SpeciesOption(
      id: (json['id'] as num).toInt(),
      name: json['name'] as String? ?? 'Animal',
      slug: json['slug'] as String? ?? '',
      category: json['category'] as String? ?? 'other',
      tradeEnabled: json['trade_enabled'] == true,
    );
  }

  String get inputGuidance {
    switch (category) {
      case 'companion':
        return 'Describe one individual animal. Include breed or mixed ancestry, '
            'sex, estimated age and any known health disclosures. '
            'Health documents need separate verification.';
      case 'farm':
        return 'This form handles one identified animal, not a herd or batch. '
            'Movement, veterinary and ownership requirements remain subject '
            'to regional review.';
      case 'aquatic':
        return 'Only an individually identified animal is supported here. '
            'Fish lots and bulk sales are not available in this version.';
      case 'bird':
        return 'Describe one individual bird. Protected species and '
            'permit-controlled trade must not be listed.';
      default:
        return 'Describe one individual animal. This category needs '
            'policy approval before public trading.';
    }
  }
}

/// Never use binary floating point for currency conversion.
class NairaMoney {
  static const int maxMinor = 10000000000000;

  static int? parseMinor(String text) {
    final cleaned = text.trim();
    if (!RegExp(r'^\d+(?:\.\d{1,2})?$').hasMatch(cleaned)) {
      return null;
    }
    final parts = cleaned.split('.');
    final naira = int.tryParse(parts.first);
    if (naira == null || naira > maxMinor ~/ 100) {
      return null;
    }
    final fraction = parts.length == 2 ? parts.last.padRight(2, '0') : '00';
    final kobo = int.tryParse(fraction);
    if (kobo == null) {
      return null;
    }
    final minor = naira * 100 + kobo;
    return minor > 0 && minor <= maxMinor ? minor : null;
  }

  static String formatMinor(int value) {
    final whole = value ~/ 100;
    final fraction = (value % 100).toString().padLeft(2, '0');
    return '$whole.$fraction';
  }
}
