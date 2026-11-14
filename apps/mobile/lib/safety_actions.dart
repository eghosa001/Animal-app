import 'package:flutter/material.dart';

import 'core/api_client.dart';

/// Collect a safety report without exposing another user's private details.
class ReportContentPage extends StatefulWidget {
  const ReportContentPage({
    required this.api,
    required this.targetType,
    required this.targetId,
    super.key,
  });
  final ApiClient api;
  final String targetType;
  final String targetId;

  @override
  State<ReportContentPage> createState() => _ReportContentPageState();
}

class _ReportContentPageState extends State<ReportContentPage> {
  static const categories = <String, String>{
    'scam': 'Scams or off-platform payments',
    'harassment': 'Harassment or threats',
    'welfare': 'Animal welfare concern',
    'illegal_trade': 'Prohibited animal trading',
    'copyright': 'Unauthorized video or content',
    'other': 'Other policy concern',
  };

  final _details = TextEditingController();
  String _category = 'scam';
  String _error = '';
  bool _busy = false;

  @override
  void dispose() {
    _details.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy) return;
    final explanation = _details.text.trim();
    if (explanation.length < 20 || explanation.length > 1500) {
      setState(() {
        _error = 'Explain the concern in 20–1500 characters.';
      });
      return;
    }
    setState(() {
      _busy = true;
      _error = '';
    });
    try {
      await widget.api.reportContent(
        targetType: widget.targetType,
        targetId: widget.targetId,
        category: _category,
        detail: explanation,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } on ApiFailure catch (error) {
      if (mounted) setState(() { _error = error.message; });
    } catch (_) {
      if (mounted) {
        setState(() { _error = 'Report could not be submitted. Please retry.'; });
      }
    } finally {
      if (mounted) setState(() { _busy = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Report a safety concern')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Reports go to Anima safety staff for review. Reporting does '
            'not automatically remove content or suspend another account.',
          ),
          const SizedBox(height: 20),
          DropdownButtonFormField<String>(
            initialValue: _category,
            decoration: const InputDecoration(
              labelText: 'Reason for reporting',
              border: OutlineInputBorder(),
            ),
            items: [
              for (final item in categories.entries)
                DropdownMenuItem(
                  value: item.key,
                  child: Text(item.value),
                ),
            ],
            onChanged: _busy ? null : (value) {
              if (value != null) setState(() { _category = value; });
            },
          ),
          const SizedBox(height: 16),
          TextField(
            key: const Key('safety-details'),
            controller: _details,
            maxLines: 6,
            minLines: 4,
            maxLength: 1500,
            enabled: !_busy,
            decoration: const InputDecoration(
              labelText: 'What happened?',
              hintText: 'Describe the violation without sharing passwords.',
              border: OutlineInputBorder(),
            ),
          ),
          if (_error.isNotEmpty) Text(
            _error,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
          const SizedBox(height: 10),
          FilledButton.icon(
            key: const Key('submit-safety-report'),
            onPressed: _busy ? null : _submit,
            icon: const Icon(Icons.flag_outlined),
            label: Text(_busy ? 'Submitting report…' : 'Submit report'),
          ),
        ],
      ),
    );
  }
}

/// Confirm with the user before imposing a two-way chat restriction.
Future<bool> confirmBlockAccount({
  required BuildContext context,
  required ApiClient api,
  required String userId,
}) async {
  if (userId.isEmpty) return false;
  final accepted = await showDialog<bool>(
    context: context,
    builder: (dialogContext) => AlertDialog(
      title: const Text('Block this account?'),
      content: const Text(
        'Their videos and animal listings will be hidden from your '
        'signed-in feed. Neither of you can send new messages to the other. '
        'Past conversations remain available for your records.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(dialogContext, false),
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(dialogContext, true),
          child: const Text('Block account'),
        ),
      ],
    ),
  );
  if (accepted != true) return false;
  try {
    await api.blockUser(userId);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Account blocked.')),
      );
    }
    return true;
  } on ApiFailure catch (error) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.message)),
      );
    }
    return false;
  } catch (_) {
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Unable to block this account.')),
      );
    }
    return false;
  }
}

Future<void> openSafetyReport({
  required BuildContext context,
  required ApiClient api,
  required String targetType,
  required String targetId,
}) async {
  final success = await Navigator.of(context).push<bool>(
    MaterialPageRoute<bool>(
      builder: (context) => ReportContentPage(
        api: api,
        targetType: targetType,
        targetId: targetId,
      ),
    ),
  );
  if (success == true && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text(
        'Report submitted for staff review. Reference saved to your account.',
      )),
    );
  }
}
