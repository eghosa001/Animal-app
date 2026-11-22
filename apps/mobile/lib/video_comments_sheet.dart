import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'core/video_feed_models.dart';
import 'safety_actions.dart';

/// Public comments are reviewed before publication. Never optimistically
/// append unapproved submissions to the public comment list.
class VideoCommentsSheet extends StatefulWidget {
  const VideoCommentsSheet({required this.api, required this.videoId, super.key});
  final ApiClient api;
  final String videoId;

  @override
  State<VideoCommentsSheet> createState() => _VideoCommentsSheetState();
}

class _VideoCommentsSheetState extends State<VideoCommentsSheet> {
  final _composer = TextEditingController();
  final _comments = <VideoComment>[];
  bool _loading = true;
  bool _loadingMore = false;
  bool _sending = false;
  bool _hasMore = false;
  int _page = 1;
  String? _error;
  VideoCommentReceipt? _pending;
  String? _pendingBody;

  @override
  void initState() {
    super.initState();
    _load(reset: true);
  }

  Future<void> _load({required bool reset}) async {
    if (_loadingMore || (!reset && !_hasMore)) return;
    setState(() {
      if (reset) {
        _loading = true;
        _error = null;
      } else {
        _loadingMore = true;
      }
    });
    try {
      final page = await widget.api.getVideoComments(
        widget.videoId, page: reset ? 1 : _page,
      );
      if (!mounted) return;
      setState(() {
        if (reset) _comments.clear();
        _comments.addAll(page.comments);
        _hasMore = page.hasMore;
        _page = reset ? 2 : _page + 1;
        _error = null;
      });
    } on ApiFailure catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Comments could not be loaded.');
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _loadingMore = false;
        });
      }
    }
  }

  Future<void> _send() async {
    final body = _composer.text.trim();
    if (_sending || body.length < 3 || body.length > 500) return;
    setState(() => _sending = true);
    try {
      // Keep nonce stable for a given attempted write to avoid duplicates when
      // an HTTP response is lost and the sender retries.
      final nonce = _submissionNonce ??= ApiClient.newChatNonce();
      final receipt = await widget.api.postVideoComment(
        widget.videoId, body, clientNonce: nonce,
      );
      if (!mounted) return;
      setState(() {
        _pending = receipt;
        _pendingBody = body;
        _submissionNonce = null;
        _composer.clear();
        _error = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Comment submitted for moderation. Not public yet.'),
      ));
    } on ApiFailure catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.message)),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Could not submit comment. Please retry.'),
        ));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  String? _submissionNonce;

  Future<void> _withdraw() async {
    final receipt = _pending;
    if (receipt == null || _sending) return;
    setState(() => _sending = true);
    try {
      await widget.api.deleteVideoComment(widget.videoId, receipt.id);
      if (mounted) setState(() {
        _pending = null;
        _pendingBody = null;
      });
    } on ApiFailure catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.message)),
        );
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  void dispose() {
    _composer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.viewInsetsOf(context).bottom;
    return SafeArea(
      top: false,
      child: Padding(
        padding: EdgeInsets.fromLTRB(16, 12, 16, bottom + 12),
        child: SizedBox(
          height: (MediaQuery.sizeOf(context).height - bottom) * 0.67,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Center(child: SizedBox(
                width: 40, height: 4,
                child: DecoratedBox(decoration: BoxDecoration(
                  color: Colors.grey,
                  borderRadius: BorderRadius.all(Radius.circular(6)),
                )),
              )),
              const SizedBox(height: 12),
              const Text('Animal video comments',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const Text('Comments are checked before anyone can see them.',
                style: TextStyle(fontSize: 12)),
              const SizedBox(height: 8),
              if (_pending != null) Card(
                key: const Key('pending-video-comment'),
                child: ListTile(
                  title: const Text('Awaiting moderation'),
                  subtitle: Text(_pendingBody ?? 'Your comment is pending review'),
                  trailing: TextButton(
                    onPressed: _sending ? null : _withdraw,
                    child: const Text('Withdraw'),
                  ),
                ),
              ),
              Expanded(
                child: _loading
                    ? const Center(child: CircularProgressIndicator())
                    : _error != null && _comments.isEmpty
                        ? Center(child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(_error!),
                              TextButton(
                                onPressed: () => _load(reset: true),
                                child: const Text('Retry'),
                              ),
                            ],
                          ))
                        : _comments.isEmpty
                            ? const Center(child: Text('No approved comments yet.'))
                            : RefreshIndicator(
                                onRefresh: () => _load(reset: true),
                                child: ListView.builder(
                                  itemCount: _comments.length + (_hasMore ? 1 : 0),
                                  itemBuilder: (context, index) {
                                    if (index == _comments.length) {
                                      return TextButton(
                                        onPressed: _loadingMore
                                            ? null : () => _load(reset: false),
                                        child: Text(_loadingMore ? 'Loading…' : 'Load more'),
                                      );
                                    }
                                    final comment = _comments[index];
                                    return ListTile(
                                      title: Text(comment.authorName),
                                      subtitle: Text(comment.body),
                                      contentPadding: EdgeInsets.zero,
                                      trailing: IconButton(
                                        tooltip: 'Report comment',
                                        icon: const Icon(Icons.flag_outlined),
                                        onPressed: () => openSafetyReport(
                                          context: context, api: widget.api,
                                          targetType: 'comment', targetId: comment.id,
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              ),
              ),
              const Divider(),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      key: const Key('video-comment-input'),
                      controller: _composer,
                      maxLength: 500,
                      minLines: 1,
                      maxLines: 3,
                      onChanged: (_) {
                        _submissionNonce = null;
                        setState(() {});
                      },
                      decoration: const InputDecoration(
                        hintText: 'Write a respectful comment',
                        isDense: true,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    tooltip: 'Submit comment for review',
                    onPressed: _sending ||
                        _composer.text.trim().length < 3
                        ? null : _send,
                    icon: const Icon(Icons.send_rounded),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
