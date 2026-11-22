import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/core/video_feed_models.dart';
import 'package:anima_app/video_comments_sheet.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const videoId = '11111111-1111-4111-8111-111111111111';
const commentId = '22222222-2222-4222-8222-222222222222';

class FakeCommentApi extends ApiClient {
  int fetches = 0;
  int posts = 0;
  int removals = 0;
  bool failPost = false;

  @override
  Future<VideoCommentPage> getVideoComments(String id, {int page = 1}) async {
    expect(id, videoId);
    fetches++;
    return const VideoCommentPage(
      comments: [VideoComment(
        id: commentId,
        authorName: 'Caring animal keeper',
        body: 'The dog looks very happy',
      )],
      hasMore: false,
    );
  }

  @override
  Future<VideoCommentReceipt> postVideoComment(
      String id, String body, {required String clientNonce}) async {
    expect(id, videoId);
    expect(body, 'Gentle animal enrichment');
    expect(clientNonce, isNotEmpty);
    posts++;
    if (failPost) throw const ApiFailure('Email verification required');
    return const VideoCommentReceipt(id: commentId, status: 'pending');
  }

  @override
  Future<void> deleteVideoComment(String id, String itemId) async {
    expect(id, videoId);
    expect(itemId, commentId);
    removals++;
  }
}

void main() {
  test('comment schema is strict and only counts approved feed comments', () {
    const playback =
        'https://videodelivery.net/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/manifest/video.m3u8';
    final video = AnimalVideoPost.fromJson({
      'id': videoId,
      'creator_name': 'Kennel creator',
      'caption': 'Exercise time',
      'playback_url': playback,
      'comments_count': 2,
    });
    expect(video.commentsCount, 2);
    expect(video.copyWith(likesCount: 5).commentsCount, 2);
    expect(VideoComment.fromJson({
      'id': commentId,
      'author_name': 'Keeper',
      'body': 'A calm animal',
    }).authorName, 'Keeper');
    expect(
      VideoCommentReceipt.fromJson({'id': commentId, 'status': 'pending'}).status,
      'pending',
    );
    expect(
      () => VideoCommentReceipt.fromJson({
        'id': commentId,
        'status': 'published-without-review',
      }), throwsFormatException,
    );
  });

  testWidgets('submission is pending, never appended as public text',
      (tester) async {
    final api = FakeCommentApi();
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: VideoCommentsSheet(api: api, videoId: videoId),
    )));
    await tester.pumpAndSettle();
    expect(find.text('The dog looks very happy'), findsOneWidget);
    expect(find.byTooltip('Report comment'), findsOneWidget);
    expect(find.text('Gentle animal enrichment'), findsNothing);
    await tester.enterText(
      find.byKey(const Key('video-comment-input')),
      'Gentle animal enrichment',
    );
    await tester.pump();
    await tester.tap(find.byTooltip('Submit comment for review'));
    await tester.pumpAndSettle();
    expect(api.posts, 1);
    expect(find.text('Awaiting moderation'), findsOneWidget);
    expect(find.byKey(const Key('pending-video-comment')), findsOneWidget);
    expect(find.text('Gentle animal enrichment'), findsOneWidget);
    // No optimistic public-list append: published list still has one comment.
    expect(find.text('The dog looks very happy'), findsOneWidget);
    await tester.tap(find.text('Withdraw'));
    await tester.pumpAndSettle();
    expect(api.removals, 1);
    expect(find.byKey(const Key('pending-video-comment')), findsNothing);
    api.dispose();
  });

  testWidgets('failed submission preserves text and does not invent a receipt',
      (tester) async {
    final api = FakeCommentApi()..failPost = true;
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: VideoCommentsSheet(api: api, videoId: videoId),
    )));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('video-comment-input')),
      'Gentle animal enrichment',
    );
    await tester.pump();
    await tester.tap(find.byTooltip('Submit comment for review'));
    await tester.pumpAndSettle();
    expect(api.posts, 1);
    expect(find.byKey(const Key('pending-video-comment')), findsNothing);
    expect(find.text('Gentle animal enrichment'), findsOneWidget);
    expect(find.text('Email verification required'), findsOneWidget);
    api.dispose();
  });
}
