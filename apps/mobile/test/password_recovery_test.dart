import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/password_recovery_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeRecoveryApi extends ApiClient {
  int requestCalls = 0;
  int confirmCalls = 0;
  String? lastEmail;
  String? lastCode;
  String? lastPassword;

  @override
  Future<void> requestPasswordReset(String email) async {
    requestCalls++;
    lastEmail = email;
  }

  @override
  Future<void> confirmPasswordReset({
    required String email,
    required String code,
    required String newPassword,
  }) async {
    confirmCalls++;
    lastEmail = email;
    lastCode = code;
    lastPassword = newPassword;
  }
}

void main() {
  testWidgets('recovery request never reveals whether an email exists', (tester) async {
    final api = FakeRecoveryApi();
    await tester.pumpWidget(MaterialApp(
      home: PasswordRecoveryPage(api: api),
    ));
    expect(find.text('Recover your account'), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('recovery-email')),
      'recovery@example.com',
    );
    await tester.tap(find.byKey(const Key('recovery-primary-action')));
    await tester.pumpAndSettle();
    expect(api.requestCalls, 1);
    expect(api.lastEmail, 'recovery@example.com');
    expect(find.text('Enter your recovery code'), findsOneWidget);
    expect(find.textContaining('If an active account exists'), findsOneWidget);
    api.dispose();
  });

  testWidgets('recovery request validates email before API call', (tester) async {
    final api = FakeRecoveryApi();
    await tester.pumpWidget(MaterialApp(
      home: PasswordRecoveryPage(api: api),
    ));
    await tester.tap(find.byKey(const Key('recovery-primary-action')));
    await tester.pumpAndSettle();
    expect(find.text('Enter a valid email address'), findsOneWidget);
    expect(api.requestCalls, 0);
    api.dispose();
  });

  testWidgets('recovery confirmation validates and sends a new password', (tester) async {
    final api = FakeRecoveryApi();
    await tester.pumpWidget(MaterialApp(
      home: PasswordRecoveryPage(
        api: api,
        initialEmail: 'breeder@example.com',
      ),
    ));
    await tester.tap(find.byKey(const Key('recovery-primary-action')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('recovery-code')),
      'valid-test-code',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-new-password')),
      'NewPassword!2026',
    );
    await tester.enterText(
      find.byKey(const Key('recovery-password-confirmation')),
      'NotSamePassword!2026',
    );
    await tester.ensureVisible(find.byKey(const Key('recovery-primary-action')));
    await tester.tap(find.byKey(const Key('recovery-primary-action')));
    await tester.pumpAndSettle();
    expect(find.text('Passwords do not match'), findsOneWidget);
    expect(api.confirmCalls, 0);

    await tester.enterText(
      find.byKey(const Key('recovery-password-confirmation')),
      'NewPassword!2026',
    );
    await tester.ensureVisible(find.byKey(const Key('recovery-primary-action')));
    await tester.tap(find.byKey(const Key('recovery-primary-action')));
    await tester.pumpAndSettle();
    expect(api.confirmCalls, 1);
    expect(api.lastEmail, 'breeder@example.com');
    expect(api.lastCode, 'valid-test-code');
    expect(api.lastPassword, 'NewPassword!2026');
    api.dispose();
  });
}
