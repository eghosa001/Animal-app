import 'dart:async';

import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'core/chat_models.dart';

/// Safe, text-only conversation with one approved animal listing as context.
class ChatThreadPage extends StatefulWidget {
  const ChatThreadPage({
    required this.api,
    required this.conversation,
    super.key,
  });
  final ApiClient api;
  final ChatConversation conversation;

  @override
  State<ChatThreadPage> createState() => _ChatThreadPageState();
}

class _ChatThreadPageState extends State<ChatThreadPage> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  List<ChatMessage> _messages = [];
  bool _loading = true;
  bool _busy = false;
  bool _older = false;
  bool _hasMore = false;
  int _page = 1;
  String _error = '';
  String? _pendingNonce;
  String? _pendingText;

  @override
  void initState() {
    super.initState();
    unawaited(_load(reset: true));
  }

  Future<void> _load({required bool reset}) async {
    if (_older) { return; }
    if (!reset && !_hasMore) { return; }
    if (mounted) {
      setState(() {
        if (reset) {
          _loading = true;
        } else {
          _older = true;
        }
        _error = '';
      });
    }
    try {
      final page = reset ? 1 : _page;
      final result = await widget.api.getConversationMessages(
        widget.conversation.id, page: page,
      );
      if (!mounted) { return; }
      setState(() {
        if (reset) {
          _messages = result.messages;
        } else {
          _messages.addAll(result.messages);
        }
        _hasMore = result.hasMore;
        _page = page + 1;
      });
    } on ApiFailure catch (error) {
      if (mounted) { setState(() => _error = error.message); }
    } catch (_) {
      if (mounted) { setState(() =>
          _error = 'Unable to load messages. Check your connection.'); }
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
          _older = false;
        });
      }
    }
  }

  Future<void> _send() async {
    final text = _input.text.trim();
    if (_busy || text.isEmpty || !widget.conversation.canSend) { return; }
    if (text.length > 2000) {
      setState(() => _error = 'Messages cannot exceed 2000 characters.');
      return;
    }
    // After a failed network response, reuse the nonce for the same text
    // to avoid duplicating a message that the server may have accepted.
    if (_pendingText != text || _pendingNonce == null) {
      _pendingText = text;
      _pendingNonce = ApiClient.newChatNonce();
    }
    setState(() {
      _busy = true;
      _error = '';
    });
    try {
      await widget.api.sendChatMessage(
        widget.conversation.id, text, clientNonce: _pendingNonce!,
      );
      if (!mounted) return;
      _input.clear();
      _pendingText = null;
      _pendingNonce = null;
      await _load(reset: true);
    } on ApiFailure catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) { setState(() =>
          _error = 'Message status is uncertain; retry to avoid duplicates.'); }
    } finally {
      if (mounted) { setState(() => _busy = false); }
    }
  }

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.conversation.counterpartyName)),
      body: Column(
        children: [
          Material(
            color: Theme.of(context).colorScheme.surfaceContainerLow,
            child: ListTile(
              leading: const Icon(Icons.pets),
              title: Text(widget.conversation.listingTitle),
              subtitle: const Text('Conversation about this animal only'),
            ),
          ),
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 10, 16, 8),
            child: Text(
              'Stay on the platform. Off-platform payments and deals are not '
              'protected by Anima. Never share passwords or verification codes.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12),
            ),
          ),
          if (_error.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(8),
              child: Text(_error, style: TextStyle(
                  color: Theme.of(context).colorScheme.error)),
            ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : RefreshIndicator(
                    onRefresh: () => _load(reset: true),
                    child: ListView(
                      controller: _scroll,
                      reverse: true,
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.symmetric(
                        vertical: 8, horizontal: 12,
                      ),
                      children: [
                        for (final item in _messages)
                          Align(
                            alignment: Alignment.centerLeft,
                            child: Card(
                              margin: const EdgeInsets.symmetric(vertical: 3),
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(item.senderName,
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w600)),
                                    const SizedBox(height: 3),
                                    Text(item.body),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        if (_hasMore)
                          TextButton(
                            onPressed: _older ? null
                                : () => _load(reset: false),
                            child: Text(_older ? 'Loading…' : 'Load older messages'),
                          ),
                      ],
                    ),
                  ),
          ),
          if (widget.conversation.canSend)
            SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 10),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _input,
                        enabled: !_busy,
                        maxLines: 3,
                        minLines: 1,
                        maxLength: 2000,
                        decoration: const InputDecoration(
                          hintText: 'Message about this animal',
                          border: OutlineInputBorder(),
                          counterText: '',
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    IconButton.filled(
                      tooltip: 'Send message',
                      onPressed: _busy ? null : _send,
                      icon: const Icon(Icons.send),
                    ),
                  ],
                ),
              ),
            )
          else
            const SafeArea(
              top: false,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Text('This listing is not currently available for new messages.'),
              ),
            ),
        ],
      ),
    );
  }
}
