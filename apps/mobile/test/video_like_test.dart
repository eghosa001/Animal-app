import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/core/video_feed_models.dart';
import 'package:anima_app/video_feed_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const clipId = '00000000-0000-0000-0000-000000000018';
const clip = AnimalVideoPost(
  id: clipId,
  creatorName: 'Responsible breeder',
  creatorId: '00000000-0000-0000-0000-000000000017',
  caption: 'Playing safely with a companion animal',
  playbackUrl: 'https://videodelivery.net/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/manifest/video.m3u8',
  posterUrl: 'https://videodelivery.net/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/thumbnails/thumbnail.jpg',
  likesCount: 4,
  isLiked: false,
);

class FakeVideoReactionApi extends ApiClient {
  int requests = 0;
  bool failNext = false;
  bool liked = false;
  int count = 4;

  @override
  Future<AnimalVideoPage> getVideoFeed({int page = 1}) async {
    return const AnimalVideoPage(posts: [clip], hasMore: false);
  }

  @override
  Future<VideoLikeResult> setVideoLiked(String id, bool target) async {
    expect(id, clipId);
    requests++;
    if (failNext) {
      throw const ApiFailure('Sign in to like animal videos');
    }
    if (target != liked) {
      count += target ? 1 : -1;
      liked = target;
    }
    return VideoLikeResult(likesCount: count, isLiked: liked);
  }
}

void main() {
  test('likes parse as a typed bounded private-state response', () {
    final parsed = AnimalVideoPost.fromJson({
      'id': clipId, 'creator_name': 'Responsible breeder',
      'caption': 'Video with animal enrichment',
      'playback_url': clip.playbackUrl,
      'poster_url': clip.posterUrl,
      'likes_count': 12, 'is_liked': true,
    });
    expect(parsed.likesCount, 12);
    expect(parsed.isLiked, isTrue);
    final changed = parsed.copyWith(likesCount: 11, isLiked: false);
    expect(changed.likesCount, 11);
    expect(parsed.likesCount, 12);
    expect(changed.isLiked, isFalse);
    expect(
      () => VideoLikeResult.fromJson({
        'likes_count': -10, 'is_liked': true,
      }), throwsFormatException,
    );
  });

  testWidgets('liking and unliking updates counts only after server reply',
      (tester) async {
    final api = FakeVideoReactionApi();
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: VideoFeedPage(
        api: api,
        openMarket: () {},
        openListing: (_) async {},
      ),
    )));
    await tester.pumpAndSettle();
    expect(find.byTooltip('Like video'), findsOneWidget);
    expect(find.text('4'), findsOneWidget);
    await tester.tap(find.byTooltip('Like video'));
    await tester.pumpAndSettle();
    expect(api.requests, 1);
    expect(find.byTooltip('Unlike video'), findsOneWidget);
    expect(find.text('5'), findsOneWidget);
    await tester.tap(find.byTooltip('Unlike video'));
    await tester.pumpAndSettle();
    expect(api.requests, 2);
    expect(find.byTooltip('Like video'), findsOneWidget);
    expect(find.text('4'), findsOneWidget);
    api.dispose();
  });

  testWidgets('failed reactions preserve accurate like state',
      (tester) async {
    final api = FakeVideoReactionApi()..failNext = true;
    await tester.pumpWidget(MaterialApp(home: Scaffold(
      body: VideoFeedPage(
        api: api,
        openMarket: () {},
        openListing: (_) async {},
      ),
    )));
    await tester.pumpAndSettle();
    await tester.tap(find.byTooltip('Like video'));
    await tester.pumpAndSettle();
    expect(api.requests, 1);
    expect(find.byTooltip('Unlike video'), findsNothing);
    expect(find.text('4'), findsOneWidget);
    expect(find.text('Sign in to like animal videos'), findsOneWidget);
    api.dispose();
  });
}
