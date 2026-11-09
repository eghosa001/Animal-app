import 'package:flutter/material.dart';

import 'core/api_client.dart';

/// High-impact account action. Success requires a confirmed server response;
/// the client cannot revoke sessions just by clearing local storage.
class RevokeSessionsPage extends StatefulWidget {
  const RevokeSessionsPage({required this.api, super.key});

  final ApiClient api;

  @override
  State<RevokeSessionsPage> createState() => _RevokeSessionsPageState();
}

class _RevokeSessionsPageState extends State<RevokeSessionsPage> {
  final TextEditingController _password = TextEditingController();
  bool _busy = false;
  bool _showPassword = false;
  String _error = '';

  @override
  void dispose() {
    _password.dispose();
    super.dispose();
  }

  Future<void> _revoke() async {
    if (_busy) {
      return;
    }
    if (_password.text.isEmpty) {
      setState(() => _error = 'Enter your current password to continue.');
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Sign out everywhere?'),
        content: const Text(
          'Every device signed in to this account will lose access, '
          'including this phone. You can sign in again with the same password. '
          'This cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            key: const Key('revoke-confirm-button'),
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Sign out all devices'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }
    setState(() {
      _busy = true;
      _error = '';
    });
    try {
      await widget.api.logoutAll(_password.text);
      _password.clear();
      if (mounted) {
        Navigator.of(context).pop(true);
      }
    } on ApiFailure catch (error) {
      if (mounted) {
        setState(() => _error = error.message);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'Unable to reach the server. Other sessions were not confirmed revoked.');
      }
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Account sessions')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            const Icon(Icons.phonelink_lock_outlined, size: 52),
            const SizedBox(height: 14),
            Text('Sign out of all devices',
                style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 10),
            const Text(
              'Use this if you lost a phone or suspect an account session is no '
              'longer secure. Enter your existing password to revoke all '
              'previous sign-ins. Your password stays the same.',
            ),
            const SizedBox(height: 22),
            TextField(
              key: const Key('session-password-field'),
              controller: _password,
              enabled: !_busy,
              obscureText: !_showPassword,
              autocorrect: false,
              enableSuggestions: false,
              autofillHints: const [AutofillHints.password],
              decoration: InputDecoration(
                labelText: 'Current account password',
                border: const OutlineInputBorder(),
                suffixIcon: IconButton(
                  tooltip: _showPassword ? 'Hide password' : 'Show password',
                  onPressed: _busy
                      ? null
                      : () => setState(() => _showPassword = !_showPassword),
                  icon: Icon(_showPassword
                      ? Icons.visibility_off_outlined
                      : Icons.visibility_outlined),
                ),
              ),
            ),
            if (_error.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(_error,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ],
            const SizedBox(height: 20),
            FilledButton.icon(
              key: const Key('revoke-all-button'),
              onPressed: _busy ? null : _revoke,
              icon: const Icon(Icons.logout_outlined),
              label: Text(_busy ? 'Signing out…' : 'Sign out everywhere'),
            ),
            const SizedBox(height: 14),
            const Text(
              'This action affects all existing logins for your account. '
              'It does not remove your account, listings, or payment records.',
            ),
          ],
        ),
      ),
    );
  }
}
