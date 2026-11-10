import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  testWidgets('opens directly into a moderated video feed with five tabs', (tester) async {
    final api = ApiClient(
      baseUrl: 'https://api.example.invalid',
      client: MockClient((_) async => http.Response(
        '{"count":0,"next":null,"results":[]}',
        200, headers: {'content-type': 'application/json'},
      )),
    );
    await tester.pumpWidget(MaterialApp(home: AppShell(api: api)));
    await tester.pumpAndSettle();

    expect(find.text('Anima'), findsOneWidget);
    expect(find.text('For You'), findsOneWidget);
    expect(find.text('No approved animal videos yet'), findsOneWidget);
    expect(find.text('Browse animal listings'), findsOneWidget);
    expect(find.byType(NavigationBar), findsOneWidget);
    expect(find.text('Home'), findsOneWidget);
    expect(find.text('Market'), findsOneWidget);
    expect(find.text('Create'), findsOneWidget);
    expect(find.text('Chats'), findsOneWidget);
    expect(find.text('Profile'), findsOneWidget);
  });
}
