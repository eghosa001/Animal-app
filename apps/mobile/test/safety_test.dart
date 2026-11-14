import 'package:anima_app/blocked_accounts_page.dart';
import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/safety_actions.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const testUser = '00000000-0000-0000-0000-000000000001';
const testVideo = '00000000-0000-0000-0000-000000000002';

class FakeSafetyApi extends ApiClient {
  int reportCalls = 0;
  int blockCalls = 0;
  int unblockCalls = 0;
  String? lastReportCategory;
  String? lastReportId;
  String? lastReportType;
  String? blockedId;
  String? lastReportText;
  bool failReport = false;
  bool failBlock = false;
  bool failUnblock = false;
  bool blocked = true;

  @override
  Future<String> reportContent({
    required String targetType,
    required String targetId,
    required String category,
    required String detail,
  }) async {
    reportCalls++;
    lastReportType = targetType;
    lastReportId = targetId;
    lastReportText = detail;
    lastReportCategory = category;
    if (failReport) throw const ApiFailure('Report rejected by server');
    return 'case-reference';
  }

  @override
  Future<void> blockUser(String userId) async {
    blockCalls++;
    blockedId = userId;
    if (failBlock) throw const ApiFailure('Unable to block user');
    blocked = true;
  }

  @override
  Future<void> unblockUser(String userId) async {
    unblockCalls++;
    blockedId = userId;
    if (failUnblock) throw const ApiFailure('Unable to unblock user');
    blocked = false;
  }

  @override
  Future<List<Map<String, dynamic>>> getBlockedUsers() async {
    if (!blocked) return [];
    return [{
      'blocked': testUser,
      'blocked_name': 'Sample seller',
      'id': '00000000-0000-0000-0000-000000000010',
    }];
  }
}

void main() {
  testWidgets('report needs meaningful detail and returns only after API receipt',
      (tester) async {
    final api = FakeSafetyApi();
    await tester.pumpWidget(MaterialApp(
      home: ReportContentPage(
        api: api, targetType: 'video', targetId: testVideo,
      ),
    ));
    await tester.tap(find.byKey(const Key('submit-safety-report')));
    await tester.pumpAndSettle();
    expect(api.reportCalls, 0);
    expect(find.text('Explain the concern in 20–1500 characters.'),
        findsOneWidget);
    await tester.enterText(find.byKey(const Key('safety-details')),
        'The video advertises a prohibited wildlife species for sale.');
    await tester.tap(find.byKey(const Key('submit-safety-report')));
    await tester.pumpAndSettle();
    expect(api.reportCalls, 1);
    expect(api.lastReportType, 'video');
    expect(api.lastReportId, testVideo);
    expect(api.lastReportCategory, 'scam');
    expect(api.lastReportText, contains('prohibited wildlife'));
    api.dispose();
  });

  testWidgets('report failures stay in the form and display server error',
      (tester) async {
    final api = FakeSafetyApi()..failReport = true;
    await tester.pumpWidget(MaterialApp(
      home: ReportContentPage(
        api: api, targetType: 'user', targetId: testUser,
      ),
    ));
    await tester.enterText(find.byKey(const Key('safety-details')),
        'This seller repeatedly demanded payment through an outside account.');
    await tester.tap(find.byKey(const Key('submit-safety-report')));
    await tester.pumpAndSettle();
    expect(api.reportCalls, 1);
    expect(find.text('Report rejected by server'), findsOneWidget);
    api.dispose();
  });

  testWidgets('block confirmation permits cancellation without server action',
      (tester) async {
    final api = FakeSafetyApi();
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: Builder(builder: (context) => FilledButton(
        onPressed: () => confirmBlockAccount(
          context: context, api: api, userId: testUser,
        ),
        child: const Text('Safety options'),
      )),
    )));
    await tester.tap(find.text('Safety options'));
    await tester.pumpAndSettle();
    expect(find.text('Block this account?'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(api.blockCalls, 0);
    await tester.tap(find.text('Safety options'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Block account'));
    await tester.pumpAndSettle();
    expect(api.blockCalls, 1);
    expect(api.blockedId, testUser);
    api.dispose();
  });

  testWidgets('profile blocklist confirms unblocking then refreshes',
      (tester) async {
    final api = FakeSafetyApi();
    await tester.pumpWidget(MaterialApp(home: BlockedAccountsPage(api: api)));
    await tester.pumpAndSettle();
    expect(find.text('Sample seller'), findsOneWidget);
    await tester.tap(find.text('Unblock'));
    await tester.pumpAndSettle();
    expect(api.unblockCalls, 0);
    await tester.tap(find.widgetWithText(AlertDialog, 'Unblock')
        .evaluate().isNotEmpty ? find.text('Unblock').last : find.text('Unblock'));
    await tester.pumpAndSettle();
    expect(api.unblockCalls, 1);
    expect(find.text('You have not blocked any accounts.'), findsOneWidget);
    api.dispose();
  });
}
