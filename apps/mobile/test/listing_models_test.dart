import 'package:anima_app/core/listing_models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('money parser uses integer kobo and rejects ambiguous prices', () {
    expect(NairaMoney.parseMinor('25000'), 2500000);
    expect(NairaMoney.parseMinor('25000.05'), 2500005);
    expect(NairaMoney.parseMinor('0.01'), 1);
    expect(NairaMoney.parseMinor('0'), isNull);
    expect(NairaMoney.parseMinor('0.00'), isNull);
    expect(NairaMoney.parseMinor('-10.00'), isNull);
    expect(NairaMoney.parseMinor('1.123'), isNull);
    expect(NairaMoney.parseMinor('abc'), isNull);
    expect(NairaMoney.parseMinor('1000000000000000000'), isNull);
    expect(NairaMoney.formatMinor(2500005), '25000.05');
    expect(NairaMoney.formatMinor(1), '0.01');
  });

  test('species category hints do not claim automatic trade approval', () {
    final dog = SpeciesOption.fromJson({
      'id': 1,
      'name': 'Dogs',
      'slug': 'dogs',
      'category': 'companion',
      'trade_enabled': false,
    });
    expect(dog.tradeEnabled, false);
    expect(dog.inputGuidance, contains('one individual animal'));
    final farm = SpeciesOption.fromJson({
      'id': 2,
      'name': 'Cattle',
      'category': 'farm',
      'trade_enabled': false,
    });
    expect(farm.inputGuidance, contains('not a herd or batch'));
  });
}
