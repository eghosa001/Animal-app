import 'dart:convert';
import 'dart:typed_data';

import 'listing_models.dart';
import 'video_feed_models.dart';

import 'package:http_parser/http_parser.dart';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://127.0.0.1:8000',
);

class ApiFailure implements Exception {
  const ApiFailure(this.message);
  final String message;

  @override
  String toString() => message;
}

class AnimalListing {
  const AnimalListing({
    required this.id,
    required this.title,
    required this.description,
    required this.speciesName,
    required this.animalName,
    required this.sellerName,
    required this.region,
    required this.currency,
    required this.priceMinor,
    required this.photoUrls,
  });

  final String id;
  final String title;
  final String description;
  final String speciesName;
  final String animalName;
  final String sellerName;
  final String region;
  final String currency;
  final int priceMinor;
  final List<String> photoUrls;

  factory AnimalListing.fromJson(Map<String, dynamic> json) {
    final species = json['species'] as Map<String, dynamic>? ?? {};
    return AnimalListing(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      speciesName: species['name'] as String? ?? 'Animal',
      animalName: json['animal_name'] as String? ?? '',
      sellerName: json['seller_name'] as String? ?? '',
      region: json['region'] as String? ?? '',
      currency: json['currency'] as String? ?? 'NGN',
      priceMinor: (json['price_minor'] as num?)?.toInt() ?? 0,
      photoUrls: (json['photo_urls'] as List<dynamic>? ?? []).whereType<String>().toList(),
    );
  }

  String get displayPrice {
    final major = (priceMinor / 100).toStringAsFixed(2);
    return '${currency == 'NGN' ? '₦' : '$currency '}$major';
  }
}

class ApiClient {
  ApiClient({
    http.Client? client,
    FlutterSecureStorage? storage,
    String? baseUrl,
  }) : _client = client ?? http.Client(),
       _storage = storage ?? const FlutterSecureStorage(),
       _baseUrl = (baseUrl ?? apiBaseUrl).replaceFirst(RegExp(r'/$'), '');

  final http.Client _client;
  final FlutterSecureStorage _storage;
  final String _baseUrl;

  Uri _uri(String path) => Uri.parse('$_baseUrl$path');

  Map<String, dynamic> _decode(http.Response response) {
    Map<String, dynamic> body;
    try {
      body = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      throw ApiFailure('Unexpected server response (${response.statusCode})');
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = body['detail'];
      if (detail is String) { throw ApiFailure(detail); }
      final first = body.values.isEmpty ? 'Request failed' : body.values.first;
      throw ApiFailure(first is List ? first.join(', ') : first.toString());
    }
    return body;
  }

  Future<http.Response> _post(
    String path,
    Map<String, dynamic> data, {
    String? token,
  }) {
    return _client.post(
      _uri(path),
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      },
      body: jsonEncode(data),
    ).timeout(const Duration(seconds: 15));
  }

  Future<void> register({
    required String email,
    required String displayName,
    required String password,
  }) async {
    _decode(await _post('/api/v1/auth/register', {
      'email': email,
      'display_name': displayName,
      'password': password,
    }));
  }

  Future<void> verifyEmail(String email, String token) async {
    _decode(await _post('/api/v1/auth/verify-email', {
      'email': email,
      'token': token,
    }));
  }

  /// Generic response whether an active account exists or not.
  Future<void> requestPasswordReset(String email) async {
    _decode(await _post('/api/v1/auth/password-reset/request', {
      'email': email.trim().toLowerCase(),
    }));
  }

  Future<void> confirmPasswordReset({
    required String email,
    required String code,
    required String newPassword,
  }) async {
    _decode(await _post('/api/v1/auth/password-reset/confirm', {
      'email': email.trim().toLowerCase(),
      'token': code.trim(),
      'new_password': newPassword,
    }));
  }

  Future<void> resendVerification(String email) async {
    _decode(await _post('/api/v1/auth/resend-verification', {
      'email': email.trim().toLowerCase(),
    }));
  }

  Future<void> login(String email, String password) async {
    final result = _decode(await _post('/api/v1/auth/login', {
      'email': email,
      'password': password,
    }));
    await _storage.write(key: 'anima_access', value: result['access'] as String);
    await _storage.write(key: 'anima_refresh', value: result['refresh'] as String);
  }

  Future<String?> _refresh() async {
    final refresh = await _storage.read(key: 'anima_refresh');
    if (refresh == null) { return null; }
    try {
      final body = _decode(await _post('/api/v1/auth/refresh', {
        'refresh': refresh,
      }));
      final access = body['access'] as String;
      await _storage.write(key: 'anima_access', value: access);
      if (body['refresh'] is String) {
        await _storage.write(key: 'anima_refresh', value: body['refresh'] as String);
      }
      return access;
    } catch (_) {
      await _storage.delete(key: 'anima_access');
      await _storage.delete(key: 'anima_refresh');
      return null;
    }
  }

  Future<http.Response> _authorizedGet(String path) async {
    var access = await _storage.read(key: 'anima_access');
    if (access == null) { throw const ApiFailure('Sign in to continue'); }
    var response = await _client.get(
      _uri(path),
      headers: {'Authorization': 'Bearer $access'},
    ).timeout(const Duration(seconds: 15));
    if (response.statusCode == 401) {
      access = await _refresh();
      if (access == null) { throw const ApiFailure('Session expired. Sign in again.'); }
      response = await _client.get(
        _uri(path),
        headers: {'Authorization': 'Bearer $access'},
      ).timeout(const Duration(seconds: 15));
    }
    return response;
  }

  Future<Map<String, dynamic>?> me() async {
    if (await _storage.read(key: 'anima_access') == null) { return null; }
    return _decode(await _authorizedGet('/api/v1/auth/me'));
  }

  Future<void> applyAsSeller(String businessName, {required bool adultAttested}) async {
    var access = await _storage.read(key: 'anima_access');
    if (access == null) { throw const ApiFailure('Sign in first'); }
    var response = await _post('/api/v1/auth/seller', {
      'business_name': businessName,
      'adult_attested': adultAttested,
    }, token: access);
    if (response.statusCode == 401) {
      access = await _refresh();
      if (access == null) { throw const ApiFailure('Session expired. Sign in again.'); }
      response = await _post('/api/v1/auth/seller', {
        'business_name': businessName,
        'adult_attested': adultAttested,
      }, token: access);
    }
    _decode(response);
  }


  /// Fetch every page, rather than silently showing only the first 20 drafts.
  Future<List<Map<String, dynamic>>> getMyListings() async {
    final all = <Map<String, dynamic>>[];
    for (var page = 1; page <= 100; page++) {
      final data = _decode(await _authorizedGet('/api/v1/listings/mine/?page=$page'));
      final rows = data['results'];
      if (rows is! List) {
        throw const ApiFailure('Unexpected listing response');
      }
      all.addAll(rows.cast<Map<String, dynamic>>());
      if (data['next'] == null) {
        return all;
      }
    }
    throw const ApiFailure('Too many listing pages. Narrow your search.');
  }

  Future<List<SpeciesOption>> getSpecies() async {
    final response = await _client.get(
      _uri('/api/v1/catalog/species'),
    ).timeout(const Duration(seconds: 15));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw const ApiFailure('Could not load the animal catalogue');
    }
    final dynamic decoded;
    try {
      decoded = jsonDecode(response.body);
    } catch (_) {
      throw const ApiFailure('Unexpected catalogue response');
    }
    if (decoded is! List) {
      throw const ApiFailure('Unexpected catalogue response');
    }
    return decoded.map((item) => SpeciesOption.fromJson(
      item as Map<String, dynamic>,
    )).toList();
  }

  Future<Map<String, dynamic>> saveListingDraft(
    Map<String, dynamic> values, {
    String? listingId,
  }) async {
    final patch = listingId != null;
    final path = patch ? '/api/v1/listings/$listingId/' : '/api/v1/listings/';

    Future<http.Response> send(String token) {
      return patch
          ? _client.patch(
              _uri(path),
              headers: {
                'Authorization': 'Bearer $token',
                'Content-Type': 'application/json',
              },
              body: jsonEncode(values),
            ).timeout(const Duration(seconds: 15))
          : _post(path, values, token: token);
    }

    var token = await _storage.read(key: 'anima_access');
    if (token == null) {
      throw const ApiFailure('Please sign in to manage listings');
    }
    var response = await send(token);
    if (response.statusCode == 401) {
      token = await _refresh();
      if (token == null) {
        throw const ApiFailure('Session expired. Sign in again.');
      }
      response = await send(token);
    }
    return _decode(response);
  }

  Future<Map<String, dynamic>> submitListing(String listingId) async {
    var token = await _storage.read(key: 'anima_access');
    if (token == null) {
      throw const ApiFailure('Please sign in');
    }
    final path = '/api/v1/listings/$listingId/submit/';
    var response = await _post(path, {}, token: token);
    if (response.statusCode == 401) {
      token = await _refresh();
      if (token == null) {
        throw const ApiFailure('Session expired. Sign in again.');
      }
      response = await _post(path, {}, token: token);
    }
    return _decode(response);
  }

  Future<void> removeDraftPhoto(String assetId) async {
    Future<http.Response> send(String token) => _client.delete(
      _uri('/api/v1/media/$assetId/'),
      headers: {'Authorization': 'Bearer $token'},
    ).timeout(const Duration(seconds: 15));

    var token = await _storage.read(key: 'anima_access');
    if (token == null) {
      throw const ApiFailure('Sign in to manage animal photos');
    }
    var response = await send(token);
    if (response.statusCode == 401) {
      token = await _refresh();
      if (token == null) {
        throw const ApiFailure('Session expired. Sign in again.');
      }
      response = await send(token);
    }
    if (response.statusCode != 204) {
      _decode(response);
      throw const ApiFailure('Could not remove this photograph');
    }
  }

  Future<Uint8List> readMyPhoto(String urlPath) async {
    if (!RegExp(r'^/api/v1/media/[0-9a-fA-F-]{36}/file/$').hasMatch(urlPath)) {
      throw const ApiFailure('Invalid photo reference');
    }
    final response = await _authorizedGet(urlPath);
    if (response.statusCode != 200) {
      _decode(response);
      throw const ApiFailure('Photo cannot be viewed');
    }
    return response.bodyBytes;
  }

  /// The owner can see upload status but never private storage keys or bucket details.
  Future<List<Map<String, dynamic>>> getMyMedia() async {
    final response = await _authorizedGet('/api/v1/media/mine/');
    if (response.statusCode < 200 || response.statusCode >= 300) {
      _decode(response);
      throw const ApiFailure('Unable to load uploaded media');
    }
    final decoded = jsonDecode(response.body);
    if (decoded is! List) {
      throw const ApiFailure('Unexpected media response');
    }
    return decoded.cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> uploadPrivateImage({
    required String path,
    required String mimeType,
    String? listingId,
    String? evidenceType,
    bool consent = false,
  }) async {
    if (mimeType != 'image/jpeg' && mimeType != 'image/png') {
      throw const ApiFailure('Only JPEG and PNG images can be uploaded');
    }
    final evidence = listingId == null;
    if (evidence && (evidenceType == null || !consent)) {
      throw const ApiFailure('Evidence category and consent are required');
    }
    if (!evidence && (listingId.isEmpty)) {
      throw const ApiFailure('Select an animal listing');
    }
    final endpoint = evidence
        ? '/api/v1/media/seller-evidence/'
        : '/api/v1/media/listing-photos/';

    Future<http.Response> send(String token) async {
      final request = http.MultipartRequest('POST', _uri(endpoint));
      request.headers['Authorization'] = 'Bearer $token';
      if (evidence) {
        request.fields['evidence_type'] = evidenceType!;
        request.fields['consent'] = 'true';
      } else {
        request.fields['listing_id'] = listingId;
      }
      request.files.add(await http.MultipartFile.fromPath(
        'file',
        path,
        contentType: MediaType.parse(mimeType),
      ));
      final streamed = await _client.send(request).timeout(
        const Duration(seconds: 45),
      );
      return http.Response.fromStream(streamed);
    }

    var access = await _storage.read(key: 'anima_access');
    if (access == null) {
      throw const ApiFailure('Please sign in to upload images');
    }
    var response = await send(access);
    if (response.statusCode == 401) {
      access = await _refresh();
      if (access == null) {
        throw const ApiFailure('Session expired. Sign in again.');
      }
      response = await send(access);
    }
    return _decode(response);
  }

  /// Public, paginated list of safety-reviewed videos.
  Future<AnimalVideoPage> getVideoFeed({int page = 1}) async {
    if (page < 1) throw const ApiFailure('Invalid video page');
    final response = await _client.get(
      _uri('/api/v1/feed/videos/?page=$page'),
    ).timeout(const Duration(seconds: 15));
    final data = _decode(response);
    final raw = data['results'];
    if (raw is! List) throw const ApiFailure('Unexpected video response');
    try {
      return AnimalVideoPage(
        posts: raw.map((item) =>
            AnimalVideoPost.fromJson(item as Map<String, dynamic>)).toList(),
        hasMore: data['next'] != null,
      );
    } on FormatException {
      throw const ApiFailure('Unsupported video source');
    } on TypeError {
      throw const ApiFailure('Unexpected video response');
    }
  }

  Future<AnimalListing> getListing(String id) async {
    if (!RegExp(r'^[0-9a-fA-F-]{36}$').hasMatch(id)) {
      throw const ApiFailure('Invalid animal listing');
    }
    final response = await _client.get(
      _uri('/api/v1/listings/$id/'),
    ).timeout(const Duration(seconds: 15));
    return AnimalListing.fromJson(_decode(response));
  }

  Future<List<AnimalListing>> getListings() async {
    final response = await _client.get(
      _uri('/api/v1/listings/'),
    ).timeout(const Duration(seconds: 15));
    final payload = _decode(response);
    final raw = payload['results'] as List<dynamic>? ?? [];
    return raw.map((item) => AnimalListing.fromJson(item as Map<String, dynamic>)).toList();
  }

  /// Revoke every existing access and refresh session after password confirmation.
  /// Clear this phone only after the server confirms revocation; never report
  /// success on an HTTP error or network failure.
  Future<void> logoutAll(String currentPassword) async {
    Future<http.Response> send(String access) => _post(
      '/api/v1/auth/logout-all',
      {'current_password': currentPassword},
      token: access,
    );

    var access = await _storage.read(key: 'anima_access');
    if (access == null) {
      throw const ApiFailure('Please sign in to manage account sessions');
    }
    var response = await send(access);
    if (response.statusCode == 401) {
      access = await _refresh();
      if (access == null) {
        throw const ApiFailure('Session expired. Sign in again.');
      }
      response = await send(access);
    }
    if (response.statusCode != 204) {
      _decode(response);
      throw const ApiFailure('Could not sign out other devices');
    }
    await _storage.delete(key: 'anima_access');
    await _storage.delete(key: 'anima_refresh');
  }

  Future<void> logout() async {
    final refresh = await _storage.read(key: 'anima_refresh');
    final access = await _storage.read(key: 'anima_access');
    try {
      if (refresh != null && access != null) {
        await _post('/api/v1/auth/logout', {'refresh': refresh}, token: access);
      }
    } finally {
      await _storage.delete(key: 'anima_access');
      await _storage.delete(key: 'anima_refresh');
    }
  }

  void dispose() => _client.close();
}
