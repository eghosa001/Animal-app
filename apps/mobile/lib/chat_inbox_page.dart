import 'package:flutter/material.dart';

import 'chat_thread_page.dart';
import 'core/api_client.dart';
import 'core/chat_models.dart';

/// Inbox contains conversations where this account is the buyer or seller.
class ChatInboxPage extends StatefulWidget {
  const ChatInboxPage({
    required this.api,
    required this.openAccount,
    super.key,
  });

  final ApiClient api;
  final VoidCallback openAccount;

  @override
  State<ChatInboxPage> createState() => _ChatInboxPageState();
}

class _ChatInboxPageState extends State<ChatInboxPage> {
  late Future<List<ChatConversation>> _inbox;

  @override
  void initState() {
    super.initState();
    _inbox = widget.api.getMyConversations();
  }

  void _refresh() {
    final next = widget.api.getMyConversations();
    setState(() {
      _inbox = next;
    });
  }

  Future<void> _open(ChatConversation conversation) async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute<void>(
        builder: (context) => ChatThreadPage(
          api: widget.api, conversation: conversation,
        ),
      ),
    );
    if (mounted) { _refresh(); }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<ChatConversation>>(
      future: _inbox,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          final error = snapshot.error;
          final notSignedIn = error is ApiFailure &&
              error.message.contains('Sign in');
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.chat_bubble_outline, size: 48),
                  const SizedBox(height: 12),
                  Text(
                    notSignedIn
                        ? 'Sign in to see your private conversations.'
                        : 'Could not load conversations. Try again.',
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 15),
                  if (notSignedIn)
                    FilledButton(
                      onPressed: widget.openAccount,
                      child: const Text('Go to profile'),
                    )
                  else
                    OutlinedButton(
                      onPressed: _refresh,
                      child: const Text('Retry'),
                    ),
                ],
              ),
            ),
          );
        }
        final inbox = snapshot.data ?? [];
        if (inbox.isEmpty) {
          return Center(child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.mark_chat_unread_outlined, size: 48),
                const SizedBox(height: 16),
                Text('No conversations yet',
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 8),
                const Text(
                  'Open an approved animal listing and select Message seller.',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 18),
                OutlinedButton(
                  onPressed: _refresh,
                  child: const Text('Refresh conversations'),
                ),
              ],
            ),
          ));
        }
        return RefreshIndicator(
          onRefresh: () async {
            final future = widget.api.getMyConversations();
            setState(() {
              _inbox = future;
            });
            await future;
          },
          child: ListView.builder(
            physics: const AlwaysScrollableScrollPhysics(),
            itemCount: inbox.length,
            itemBuilder: (context, index) {
              final item = inbox[index];
              return ListTile(
                leading: const CircleAvatar(child: Icon(Icons.pets)),
                title: Text(item.counterpartyName),
                subtitle: Text(item.listingTitle, maxLines: 1,
                    overflow: TextOverflow.ellipsis),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => _open(item),
              );
            },
          ),
        );
      },
    );
  }
}
