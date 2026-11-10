import 'package:anima_app/core/api_client.dart';
import 'package:anima_app/create_hub_page.dart';
import 'package:anima_app/video_upload_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  test('availability endpoint is a real server feature flag', () async {
    final api = ApiClient(
      baseUrl: 'https://api.example.invalid',
      client: MockClient((request) async {
        expect(request.url.path, '/api/v1/feed/videos/upload-capabilities/');
        return http.Response(
          '{"enabled":false,"max_duration_seconds":60,"max_file_bytes":200000000}',
          200,
        );
      }),
    );
    final capabilities = await api.getVideoUploadCapabilities();
    expect(capabilities['enabled'], isFalse);
    expect(capabilities['max_file_bytes'], 200000000);
    api.dispose();
  });

  test('malformed feature flag never enables creator uploads', () async {
    final api = ApiClient(
      baseUrl: 'https://api.example.invalid',
      client: MockClient((_) async => http.Response('{"enabled":"true"}', 200)),
    );
    expect(api.getVideoUploadCapabilities(), throwsA(isA<ApiFailure>()));
    api.dispose();
  });

  test('rejects forged upload destinations without any network request', () async {
    var calls = 0;
    final api = ApiClient(
      baseUrl: 'https://api.example.invalid',
      client: MockClient((_) async {
        calls++;
        return http.Response('unexpected', 200);
      }),
    );
    for (final uri in [
      'http://upload.videodelivery.net/file',
      'https://upload.videodelivery.net.attacker.invalid/file',
      'https://user:pass@upload.videodelivery.net/file',
      'https://upload.videodelivery.net:8443/file',
    ]) {
      expect(
        () => api.uploadVideoToStream(
          uploadUrl: uri,
          filePath: '/not/present.mp4',
          mimeType: 'video/mp4',
        ),
        throwsA(isA<ApiFailure>()),
      );
    }
    expect(calls, 0);
    api.dispose();
  });

  testWidgets('Create hub offers video creation and existing listing management', (tester) async {
    final api = ApiClient(
      baseUrl: 'https://api.example.invalid',
      client: MockClient((_) async => http.Response('{}', 200)),
    );
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: CreateHubPage(api: api, onOpenAccount: () {}),
      ),
    ));
    expect(find.text('Post an animal video'), findsOneWidget);
    expect(find.text('List or manage an animal'), findsOneWidget);
    api.dispose();
  });

  testWidgets('disabled Stream does not show a video picker or upload button', (tester) async {
    final api = ApiClient(
      baseUrl: 'https://api.example.invalid',
      client: MockClient((request) async => http.Response(
        '{"enabled":false,"max_duration_seconds":60,"max_file_bytes":200000000}', 200,
      )),
    );
    await tester.pumpWidget(MaterialApp(home: VideoUploadPage(api: api)));
    await tester.pumpAndSettle();
    expect(find.text('Video posting is not available yet'), findsOneWidget);
    expect(find.text('Choose video'), findsNothing);
    expect(find.text('Submit video for review'), findsNothing);
    api.dispose();
  });
}
