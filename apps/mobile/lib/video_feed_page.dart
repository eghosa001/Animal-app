import 'dart:async';

import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

import 'core/api_client.dart';
import 'core/video_feed_models.dart';

/// Full-height vertical feed. The server supplies only reviewed/processed clips.
class VideoFeedPage extends StatefulWidget {
  const VideoFeedPage({
    required this.api,
    required this.openMarket,
    required this.openListing,
    super.key,
  });
  final ApiClient api;
  final VoidCallback openMarket;
  final Future<void> Function(String) openListing;

  @override
  State<VideoFeedPage> createState() => _VideoFeedPageState();
}

class _VideoFeedPageState extends State<VideoFeedPage> {
  final List<AnimalVideoPost> _posts = [];
  bool _loading = true;
  bool _loadingMore = false;
  bool _hasMore = true;
  int _page = 1;
  int _active = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    unawaited(_loadPage(reset: true));
  }

  Future<void> _loadPage({required bool reset}) async {
    if (!reset && (_loadingMore || !_hasMore)) return;
    if (reset) {
      setState(() {
        _loading = true;
        _error = null;
        _active = 0;
      });
    } else {
      setState(() => _loadingMore = true);
    }
    final requestedPage = reset ? 1 : _page;
    try {
      final result = await widget.api.getVideoFeed(page: requestedPage);
      if (!mounted) return;
      setState(() {
        if (reset) _posts.clear();
        _posts.addAll(result.posts);
        _hasMore = result.hasMore;
        _page = requestedPage + 1;
        _error = null;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Could not load animal videos. Check your connection.');
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _loadingMore = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    Widget child;
    if (_loading && _posts.isEmpty) {
      child = const Center(child: CircularProgressIndicator(color: Colors.white));
    } else if (_posts.isEmpty) {
      child = Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.pets_rounded, size: 58, color: Colors.white),
              const SizedBox(height: 16),
              Text(
                _error == null ? 'No approved animal videos yet' : _error!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white, fontSize: 18),
              ),
              const SizedBox(height: 12),
              const Text(
                'Videos will appear here after processing and safety review.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white70),
              ),
              const SizedBox(height: 20),
              if (_error != null)
                OutlinedButton(
                  onPressed: () => _loadPage(reset: true),
                  child: const Text('Retry'),
                ),
              TextButton(
                onPressed: widget.openMarket,
                child: const Text('Browse animal listings'),
              ),
            ],
          ),
        ),
      );
    } else {
      child = PageView.builder(
        scrollDirection: Axis.vertical,
        itemCount: _posts.length + (_loadingMore ? 1 : 0),
        onPageChanged: (index) {
          if (index >= _posts.length) return;
          setState(() => _active = index);
          if (index >= _posts.length - 3 && _hasMore) {
            unawaited(_loadPage(reset: false));
          }
        },
        itemBuilder: (context, index) {
          if (index >= _posts.length) {
            return const Center(child: CircularProgressIndicator(color: Colors.white));
          }
          final post = _posts[index];
          return _AnimalVideoTile(
            key: ValueKey(post.id),
            post: post,
            active: index == _active,
            openListing: widget.openListing,
          );
        },
      );
    }

    return ColoredBox(
      color: Colors.black,
      child: Stack(
        children: [
          Positioned.fill(child: child),
          Positioned(
            top: MediaQuery.paddingOf(context).top + 12,
            left: 16,
            right: 16,
            child: const IgnorePointer(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Anima', style: TextStyle(
                    color: Colors.white, fontSize: 23, fontWeight: FontWeight.bold,
                    shadows: [Shadow(blurRadius: 5, color: Colors.black)],
                  )),
                  Text('For You', style: TextStyle(
                    color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600,
                    shadows: [Shadow(blurRadius: 5, color: Colors.black)],
                  )),
                ],
              ),
            ),
          ),
          if (_posts.isNotEmpty && _error != null)
            Positioned(
              top: MediaQuery.paddingOf(context).top + 55,
              left: 16, right: 16,
              child: Material(
                color: Colors.black87,
                child: ListTile(
                  title: Text(_error!, style: const TextStyle(color: Colors.white)),
                  trailing: TextButton(
                    onPressed: () => _loadPage(reset: false),
                    child: const Text('Retry'),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _AnimalVideoTile extends StatefulWidget {
  const _AnimalVideoTile({
    required this.post,
    required this.active,
    required this.openListing,
    super.key,
  });
  final AnimalVideoPost post;
  final bool active;
  final Future<void> Function(String) openListing;

  @override
  State<_AnimalVideoTile> createState() => _AnimalVideoTileState();
}

class _AnimalVideoTileState extends State<_AnimalVideoTile>
    with WidgetsBindingObserver {
  VideoPlayerController? _controller;
  bool _muted = false;
  bool _ready = false;
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    if (widget.active) unawaited(_start());
  }

  Future<void> _start() async {
    if (_controller != null || !widget.active) return;
    final controller = VideoPlayerController.networkUrl(
      Uri.parse(widget.post.playbackUrl),
    );
    _controller = controller;
    try {
      await controller.initialize();
      if (!mounted || _controller != controller || !widget.active) return;
      await controller.setLooping(true);
      await controller.setVolume(_muted ? 0 : 1);
      await controller.play();
      if (mounted && _controller == controller) setState(() => _ready = true);
    } catch (_) {
      if (mounted && _controller == controller) setState(() => _failed = true);
    }
  }

  void _release() {
    final controller = _controller;
    _controller = null;
    _ready = false;
    _failed = false;
    if (controller != null) unawaited(controller.dispose());
  }

  @override
  void didUpdateWidget(covariant _AnimalVideoTile oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.post.id != widget.post.id || !widget.active) {
      _release();
    }
    if (widget.active && _controller == null) unawaited(_start());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final controller = _controller;
    if (controller == null || !_ready) return;
    if (state == AppLifecycleState.resumed && widget.active) {
      unawaited(controller.play());
    } else {
      unawaited(controller.pause());
    }
  }

  void _togglePlayback() {
    final controller = _controller;
    if (controller == null || !_ready) return;
    if (controller.value.isPlaying) {
      unawaited(controller.pause());
    } else {
      unawaited(controller.play());
    }
    setState(() {});
  }

  void _toggleSound() {
    _muted = !_muted;
    unawaited(_controller?.setVolume(_muted ? 0 : 1) ?? Future<void>.value());
    setState(() {});
  }

  Future<void> _openLinkedListing(String id) async {
    final controller = _controller;
    if (controller != null && _ready) {
      await controller.pause();
      if (mounted) setState(() {});
    }
    try {
      await widget.openListing(id);
    } finally {
      if (mounted && widget.active && controller == _controller && _ready) {
        await controller?.play();
        if (mounted) setState(() {});
      }
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _release();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    final size = controller?.value.size ?? Size.zero;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: _togglePlayback,
      child: Stack(
        fit: StackFit.expand,
        children: [
          if (_ready && controller != null && size.width > 0 && size.height > 0)
            FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: size.width,
                height: size.height,
                child: VideoPlayer(controller),
              ),
            ),
          if (!_ready)
            Center(
              child: _failed
                  ? FilledButton.icon(
                      onPressed: () {
                        _release();
                        unawaited(_start());
                      },
                      icon: const Icon(Icons.refresh),
                      label: const Text('Retry video'),
                    )
                  : const CircularProgressIndicator(color: Colors.white),
            ),
          const Positioned.fill(
            child: IgnorePointer(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [Colors.black26, Colors.transparent, Colors.black87],
                    stops: [0, 0.5, 1],
                  ),
                ),
              ),
            ),
          ),
          Positioned(
            right: 14, bottom: 96,
            child: Column(
              children: [
                IconButton(
                  tooltip: _muted ? 'Unmute video' : 'Mute video',
                  onPressed: _toggleSound,
                  color: Colors.white,
                  iconSize: 30,
                  icon: Icon(_muted ? Icons.volume_off : Icons.volume_up),
                ),
                const SizedBox(height: 16),
                IconButton(
                  tooltip: controller?.value.isPlaying == true ? 'Pause video' : 'Play video',
                  onPressed: _togglePlayback,
                  color: Colors.white,
                  iconSize: 30,
                  icon: Icon(controller?.value.isPlaying == true ? Icons.pause : Icons.play_arrow),
                ),
              ],
            ),
          ),
          Positioned(
            bottom: 36, left: 16, right: 90,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('@${widget.post.creatorName}', style: const TextStyle(
                  fontSize: 17, fontWeight: FontWeight.bold, color: Colors.white,
                )),
                const SizedBox(height: 8),
                Text(widget.post.caption, maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Colors.white, fontSize: 15)),
                if (widget.post.listing case final listing?) ...[
                  const SizedBox(height: 14),
                  FilledButton.icon(
                    onPressed: () => unawaited(_openLinkedListing(listing.id)),
                    icon: const Icon(Icons.pets),
                    label: Text('View animal · ${listing.displayPrice}',
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
