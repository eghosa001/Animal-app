/// Video-first, read-only public feed contract (only moderated videos arrive).
class AnimalVideoPost {
  const AnimalVideoPost({
    required this.id,
    required this.creatorName,
    this.creatorId = '',
    required this.caption,
    required this.playbackUrl,
    required this.posterUrl,
    this.listing,
    this.likesCount = 0,
    this.commentsCount = 0,
    this.isLiked = false,
  });

  final String id;
  final String creatorName;
  final String creatorId;
  final String caption;
  final String playbackUrl;
  final String posterUrl;
  final VideoListingLink? listing;
  final int likesCount;
  final int commentsCount;
  final bool isLiked;

  AnimalVideoPost copyWith({int? likesCount, int? commentsCount, bool? isLiked}) {
    return AnimalVideoPost(
      id: id, creatorName: creatorName, creatorId: creatorId,
      caption: caption, playbackUrl: playbackUrl, posterUrl: posterUrl,
      listing: listing,
      likesCount: likesCount ?? this.likesCount,
      commentsCount: commentsCount ?? this.commentsCount,
      isLiked: isLiked ?? this.isLiked,
    );
  }

  factory AnimalVideoPost.fromJson(Map<String, dynamic> json) {
    final playback = Uri.tryParse(json['playback_url']?.toString() ?? '');
    if (playback == null || playback.scheme != 'https' || playback.host.isEmpty) {
      throw const FormatException('Video playback requires an HTTPS source');
    }
    final rawListing = json['listing'];
    return AnimalVideoPost(
      id: json['id']?.toString() ?? '',
      creatorName: json['creator_name']?.toString() ?? 'Animal creator',
      creatorId: json['creator_id']?.toString() ?? '',
      likesCount: (json['likes_count'] as num?)?.toInt() ?? 0,
      commentsCount: (json['comments_count'] as num?)?.toInt() ?? 0,
      isLiked: json['is_liked'] == true,
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

class VideoLikeResult {
  const VideoLikeResult({required this.likesCount, required this.isLiked});
  final int likesCount;
  final bool isLiked;

  factory VideoLikeResult.fromJson(Map<String, dynamic> data) {
    final count = data['likes_count'];
    if (count is! int || count < 0 || data['is_liked'] is! bool) {
      throw const FormatException('Unexpected video reaction response');
    }
    return VideoLikeResult(
      likesCount: count,
      isLiked: data['is_liked'] as bool,
    );
  }
}


class VideoComment {
  const VideoComment({
    required this.id,
    required this.authorName,
    required this.body,
  });
  final String id;
  final String authorName;
  final String body;

  factory VideoComment.fromJson(Map<String, dynamic> value) {
    final id = value['id'];
    final body = value['body'];
    if (id is! String || id.isEmpty || body is! String || body.isEmpty) {
      throw const FormatException('Unexpected comment response');
    }
    return VideoComment(
      id: id,
      authorName: value['author_name']?.toString() ?? 'Animal user',
      body: body,
    );
  }
}

class VideoCommentPage {
  const VideoCommentPage({required this.comments, required this.hasMore});
  final List<VideoComment> comments;
  final bool hasMore;
}

class VideoCommentReceipt {
  const VideoCommentReceipt({required this.id, required this.status});
  final String id;
  final String status;

  factory VideoCommentReceipt.fromJson(Map<String, dynamic> value) {
    final id = value['id'];
    final status = value['status'];
    if (id is! String || id.isEmpty ||
        !const {'pending', 'approved', 'rejected', 'removed'}.contains(status)) {
      throw const FormatException('Unexpected comment submission response');
    }
    return VideoCommentReceipt(id: id, status: status as String);
  }
}
