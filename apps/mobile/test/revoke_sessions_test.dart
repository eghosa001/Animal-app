import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/revoke_sessions_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeRevocationApi extends ApiClient {
  int calls = 0;
  String? submittedPassword;
  bool fail = false;

  @override
  Future<void> logoutAll(String currentPassword) async {
    calls++;
    submittedPassword = currentPassword;
    if (fail) throw const ApiFailure('Incorrect password');
  }
}

void main() {
  testWidgets('requires password before showing the confirmation', (tester) async {
    final api = FakeRevocationApi();
    await tester.pumpWidget(MaterialApp(home: RevokeSessionsPage(api: api)));
    await tester.tap(find.byKey(const Key('revoke-all-button')));
    await tester.pumpAndSettle();

    expect(find.text('Enter your current password to continue.'), findsOneWidget);
    expect(find.text('Sign out everywhere?'), findsNothing);
    expect(api.calls, 0);
    api.dispose();
  });

  testWidgets('confirmation cancel does not revoke any session', (tester) async {
    final api = FakeRevocationApi();
    await tester.pumpWidget(MaterialApp(home: RevokeSessionsPage(api: api)));
    await tester.enterText(find.byKey(const Key('session-password-field')), 'CorrectPassword!2026');
    await tester.tap(find.byKey(const Key('revoke-all-button')));
    await tester.pumpAndSettle();
    expect(find.text('Sign out everywhere?'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();

    expect(api.calls, 0);
    api.dispose();
  });

  testWidgets('server rejects password: action stays open with error', (tester) async {
    final api = FakeRevocationApi()..fail = true;
    await tester.pumpWidget(MaterialApp(home: RevokeSessionsPage(api: api)));
    await tester.enterText(find.byKey(const Key('session-password-field')), 'WrongPassword!2026');
    await tester.tap(find.byKey(const Key('revoke-all-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('revoke-confirm-button')));
    await tester.pumpAndSettle();

    expect(api.calls, 1);
    expect(api.submittedPassword, 'WrongPassword!2026');
    expect(find.text('Incorrect password'), findsOneWidget);
    expect(find.text('Account sessions'), findsOneWidget);
    api.dispose();
  });

  testWidgets('confirmed action sends password and closes on server success', (tester) async {
    final api = FakeRevocationApi();
    await tester.pumpWidget(MaterialApp(
      home: Builder(builder: (context) {
        return Scaffold(body: Center(child: FilledButton(
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute<bool>(
              builder: (context) => RevokeSessionsPage(api: api),
            ),
          ),
          child: const Text('Account security'),
        )));
      }),
    ));
    await tester.tap(find.text('Account security'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('session-password-field')), 'CorrectPassword!2026');
    await tester.tap(find.byKey(const Key('revoke-all-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('revoke-confirm-button')));
    await tester.pumpAndSettle();

    expect(api.calls, 1);
    expect(api.submittedPassword, 'CorrectPassword!2026');
    expect(find.text('Account security'), findsOneWidget);
    expect(find.text('Account sessions'), findsNothing);
    api.dispose();
  });
}
