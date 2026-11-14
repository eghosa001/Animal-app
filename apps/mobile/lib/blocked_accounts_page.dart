import 'package:flutter/material.dart';

import 'core/api_client.dart';

/// Each user manages only their own blocklist. Unblock requires confirmation.
class BlockedAccountsPage extends StatefulWidget {
  const BlockedAccountsPage({required this.api, super.key});
  final ApiClient api;

  @override
  State<BlockedAccountsPage> createState() => _BlockedAccountsPageState();
}

class _BlockedAccountsPageState extends State<BlockedAccountsPage> {
  late Future<List<Map<String, dynamic>>> _blocked;
  String? _busyId;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _blocked = widget.api.getBlockedUsers();
  }

  void _refresh() {
    final next = widget.api.getBlockedUsers();
    setState(() {
      _blocked = next;
      _error = '';
    });
  }

  Future<void> _unblock(String id) async {
    if (_busyId != null) { return; }
    final accepted = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Unblock account?'),
        content: const Text(
          'You may see this account’s approved videos and listings again. '
          'Existing chats may become writable if the animal is still available.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Unblock'),
          ),
        ],
      ),
    );
    if (accepted != true || !mounted) { return; }
    setState(() {
      _busyId = id;
      _error = '';
    });
    try {
      await widget.api.unblockUser(id);
      if (mounted) { _refresh(); }
    } on ApiFailure catch (error) {
      if (mounted) { setState(() { _error = error.message; }); }
    } catch (_) {
      if (mounted) setState(() {
        _error = 'Could not unblock account. Try again.';
      });
    } finally {
      if (mounted) { setState(() { _busyId = null; }); }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Blocked accounts')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: _blocked,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Unable to load your blocked accounts.'),
                OutlinedButton(onPressed: _refresh, child: const Text('Retry')),
              ],
            ));
          }
          final items = snapshot.data ?? [];
          if (items.isEmpty) {
            return const Center(child: Padding(
              padding: EdgeInsets.all(24),
              child: Text('You have not blocked any accounts.'),
            ));
          }
          return ListView(
            children: [
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text('Blocking hides that account’s public content '
                    'and prevents new messages between you.'),
              ),
              if (_error.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(_error, style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                  )),
                ),
              for (final item in items)
                ListTile(
                  leading: const CircleAvatar(child: Icon(Icons.block)),
                  title: Text(item['blocked_name']?.toString() ?? 'Account'),
                  trailing: OutlinedButton(
                    onPressed: _busyId != null
                        ? null : () => _unblock(item['blocked'].toString()),
                    child: const Text('Unblock'),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
