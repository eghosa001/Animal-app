import 'dart:convert';

import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/core/video_feed_models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  const uid = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
  final clip = <String, dynamic>{
    'id': uid,
    'creator_name': 'Pet care',
    'caption': 'Enrichment play',
    'playback_url':
        'https://videodelivery.net/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/manifest/video.m3u8',
    'poster_url': 'https://videodelivery.net/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/thumbnails/thumbnail.jpg',
    'listing': <String, dynamic>{
      'id': uid,
      'title': 'Companion dog',
      'price_minor': 250050,
      'currency': 'NGN',
      'region': 'Lagos',
    },
  };

  test('rejects insecure playback locations', () {
    expect(
      () => AnimalVideoPost.fromJson({...clip, 'playback_url': 'http://example.com/video'}),
      throwsFormatException,
    );
  });

  test('converts permitted listing amount without rounding away minor units', () {
    final video = AnimalVideoPost.fromJson(clip);
    expect(video.listing!.displayPrice, '₦2500.50');
    expect(video.creatorName, 'Pet care');
  });

  test('client reads paginated moderated video contract', () async {
    final seen = <Uri>[];
    final api = ApiClient(
      baseUrl: 'https://api.example.invalid',
      client: MockClient((request) async {
        seen.add(request.url);
        return http.Response(jsonEncode({
          'count': 2,
          'next': 'https://api.example.invalid/api/v1/feed/videos/?page=2',
          'results': [clip],
        }), 200, headers: {'content-type': 'application/json'});
      }),
    );
    final page = await api.getVideoFeed();
    expect(page.posts.length, 1);
    expect(page.hasMore, isTrue);
    expect(seen.single.path, '/api/v1/feed/videos/');
    api.dispose();
  });

  test('the video endpoint rejects broken response contracts', () async {
    final api = ApiClient(
      baseUrl: 'https://api.example.invalid',
      client: MockClient((_) async => http.Response('{"results":"wrong"}', 200)),
    );
    expect(() => api.getVideoFeed(), throwsA(isA<ApiFailure>()));
    api.dispose();
  });
}
