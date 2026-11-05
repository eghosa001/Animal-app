import 'package:anima_app/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('app launches with five primary navigation destinations', (tester) async {
    await tester.pumpWidget(const AnimaApp());
    expect(find.text('Anima'), findsOneWidget);
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Market'), findsOneWidget);
    expect(find.text('Create'), findsOneWidget);
    expect(find.text('Chats'), findsOneWidget);
    expect(find.text('Profile'), findsOneWidget);
    expect(find.text('Browse marketplace'), findsOneWidget);
  });
}
