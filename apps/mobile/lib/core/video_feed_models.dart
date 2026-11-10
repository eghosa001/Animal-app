/// Video-first, read-only public feed contract (only moderated videos arrive).
class AnimalVideoPost {
  const AnimalVideoPost({
    required this.id,
    required this.creatorName,
    required this.caption,
    required this.playbackUrl,
    required this.posterUrl,
    this.listing,
  });

  final String id;
  final String creatorName;
  final String caption;
  final String playbackUrl;
  final String posterUrl;
  final VideoListingLink? listing;

  factory AnimalVideoPost.fromJson(Map<String, dynamic> json) {
    final playback = Uri.tryParse(json['playback_url']?.toString() ?? '');
    if (playback == null || playback.scheme != 'https' || playback.host.isEmpty) {
      throw const FormatException('Video playback requires an HTTPS source');
    }
    final rawListing = json['listing'];
    return AnimalVideoPost(
      id: json['id']?.toString() ?? '',
      creatorName: json['creator_name']?.toString() ?? 'Animal creator',
      caption: json['caption']?.toString() ?? '',
      playbackUrl: playback.toString(),
      posterUrl: json['poster_url']?.toString() ?? '',
      listing: rawListing is Map<String, dynamic>
          ? VideoListingLink.fromJson(rawListing)
          : null,
    );
  }
}

class VideoListingLink {
  const VideoListingLink({
    required this.id,
    required this.title,
    required this.region,
    required this.priceMinor,
    required this.currency,
  });
  final String id;
  final String title;
  final String region;
  final int priceMinor;
  final String currency;

  factory VideoListingLink.fromJson(Map<String, dynamic> json) =>
      VideoListingLink(
        id: json['id']?.toString() ?? '',
        title: json['title']?.toString() ?? '',
        region: json['region']?.toString() ?? '',
        priceMinor: (json['price_minor'] as num?)?.toInt() ?? 0,
        currency: json['currency']?.toString() ?? '',
      );

  String get displayPrice =>
      '${currency == 'NGN' ? '₦' : '$currency '}${(priceMinor / 100).toStringAsFixed(2)}';
}

class AnimalVideoPage {
  const AnimalVideoPage({required this.posts, required this.hasMore});
  final List<AnimalVideoPost> posts;
  final bool hasMore;
}
