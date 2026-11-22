import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'core/chat_models.dart';
import 'safety_actions.dart';
import 'offer_negotiation_page.dart';

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

class _ChatThreadPageState extends State<ChatThreadPage> with WidgetsBindingObserver {
  WebSocket? _socket;
  StreamSubscription<dynamic>? _socketEvents;
  Timer? _socketRetry;
  Timer? _socketRefresh;
  bool _socketEnabled = true;
  bool _connectingSocket = false;
  int _socketFailures = 0;

  final _input = TextEditingController();
  final _scroll = ScrollController();
  List<ChatMessage> _messages = [];
  bool _loading = true;
  bool _busy = false;
  bool _blocked = false;
  bool _older = false;
  bool _hasMore = false;
  int _page = 1;
  String _error = '';
  String? _pendingNonce;
  String? _pendingText;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    unawaited(_load(reset: true));
    unawaited(_connectSocket());
  }

  Future<void> _connectSocket() async {
    if (!mounted || !_socketEnabled || _connectingSocket || _socket != null) {
      return;
    }
    _connectingSocket = true;
    try {
      final socket = await widget.api.connectConversationUpdates(
        widget.conversation.id,
      );
      if (!mounted || !_socketEnabled) {
        await socket?.close();
        return;
      }
      // A test/mock API may opt out of realtime while preserving REST messaging.
      if (socket == null) { return; }
      _socket = socket;
      _socketFailures = 0;
      _socketEvents = socket.listen((event) {
        if (event is! String) { return; }
        try {
          final message = jsonDecode(event);
          if (message is Map<String, dynamic> &&
              message['type'] == 'message.created' &&
              message['conversation_id'] == widget.conversation.id) {
            _scheduleSocketRefresh();
          }
        } catch (_) {
          // Ignore malformed remote notices; never execute server-provided code.
        }
      }, onDone: _socketDisconnected, onError: (_) {
        _socketDisconnected();
      }, cancelOnError: true);
    } catch (_) {
      _retrySocket();
    } finally {
      _connectingSocket = false;
    }
  }

  void _scheduleSocketRefresh() {
    _socketRefresh?.cancel();
    _socketRefresh = Timer(const Duration(milliseconds: 350), () {
      if (!mounted || !_socketEnabled) { return; }
      if (_older || _loading) {
        _scheduleSocketRefresh();
      } else {
        unawaited(_load(reset: true));
      }
    });
  }

  void _socketDisconnected() {
    _socket = null;
    _socketEvents = null;
    _retrySocket();
  }

  void _retrySocket() {
    if (!mounted || !_socketEnabled) { return; }
    _socketRetry?.cancel();
    const delays = <int>[2, 4, 8, 15, 30];
    final index = _socketFailures < delays.length
        ? _socketFailures : delays.length - 1;
    _socketFailures++;
    _socketRetry = Timer(Duration(seconds: delays[index]), () {
      if (mounted && _socketEnabled) {
        unawaited(_connectSocket());
      }
    });
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _socketEnabled = true;
      unawaited(_load(reset: true));
      unawaited(_connectSocket());
    } else {
      _socketEnabled = false;
      _socketRetry?.cancel();
      _socketRefresh?.cancel();
      unawaited(_socketEvents?.cancel());
      unawaited(_socket?.close());
      _socket = null;
      _socketEvents = null;
    }
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
      if (reset && result.messages.isNotEmpty) {
        final lastDisplayedMessageId = result.messages.first.id;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) {
            unawaited(_ackDisplayedMessage(lastDisplayedMessageId));
          }
        });
      }
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

  Future<void> _ackDisplayedMessage(String messageId) async {
    try {
      await widget.api.markConversationRead(
        widget.conversation.id, messageId,
      );
    } catch (_) {
      // Offline/rejected acknowledgement leaves unread state unchanged.
      // A later conversation refresh will retry with a real displayed ID.
    }
  }

  Future<void> _send() async {
    final text = _input.text.trim();
    if (_busy || text.isEmpty || !widget.conversation.canSend || _blocked) { return; }
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

  Future<void> _blockCounterparty() async {
    final blocked = await confirmBlockAccount(
      context: context,
      api: widget.api,
      userId: widget.conversation.counterpartyId,
    );
    if (blocked && mounted) { setState(() { _blocked = true; }); }
  }

  Future<void> _reportUser() async {
    if (widget.conversation.counterpartyId.isEmpty) { return; }
    await openSafetyReport(
      context: context,
      api: widget.api,
      targetType: 'user',
      targetId: widget.conversation.counterpartyId,
    );
  }

  Future<void> _reportMessage(String id) async {
    await openSafetyReport(
      context: context,
      api: widget.api,
      targetType: 'message',
      targetId: id,
    );
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _socketEnabled = false;
    _socketRetry?.cancel();
    _socketRefresh?.cancel();
    unawaited(_socketEvents?.cancel());
    unawaited(_socket?.close());
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.conversation.counterpartyName),
        actions: [
          IconButton(
            tooltip: 'Price offers',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (context) => OfferNegotiationPage(
                  api: widget.api,
                  conversation: widget.conversation,
                ),
              ),
            ),
            icon: const Icon(Icons.handshake_outlined),
          ),
          PopupMenuButton<String>(
            tooltip: 'Conversation safety options',
            onSelected: (action) {
              if (action == 'report') {
                unawaited(_reportUser());
              } else if (action == 'block') {
                unawaited(_blockCounterparty());
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'report',
                child: Text('Report account'),
              ),
              if (!_blocked)
                const PopupMenuItem(
                  value: 'block',
                  child: Text('Block account'),
                ),
            ],
          ),
        ],
      ),
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
                                    Row(
                                      children: [
                                        Expanded(child: Text(item.body)),
                                        IconButton(
                                          tooltip: 'Report message',
                                          onPressed: () =>
                                              unawaited(_reportMessage(item.id)),
                                          icon: const Icon(Icons.flag_outlined),
                                        ),
                                      ],
                                    ),
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
          if (widget.conversation.canSend && !_blocked)
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
