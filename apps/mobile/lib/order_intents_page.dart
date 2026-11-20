import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'core/order_intent_models.dart';

/// User-scoped, nonfinancial checkout request history.
class OrderIntentsPage extends StatefulWidget {
  const OrderIntentsPage({required this.api, super.key});
  final ApiClient api;

  @override
  State<OrderIntentsPage> createState() => _OrderIntentsPageState();
}

class _OrderIntentsPageState extends State<OrderIntentsPage> {
  late Future<List<OrderIntentReceipt>> _requests;
  String _error = '';
  String? _busyId;

  @override
  void initState() {
    super.initState();
    _requests = widget.api.getMyOrderIntents();
  }

  void _refresh() {
    final updated = widget.api.getMyOrderIntents();
    setState(() {
      _requests = updated;
      _error = '';
    });
  }

  Future<void> _cancel(OrderIntentReceipt request) async {
    if (_busyId != null || request.status != 'awaiting_partner') { return; }
    var cancellationReason = '';
    final reason = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Cancel this order request?'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'No money was collected and no animal was reserved. '
              'Cancelling does not issue a refund or change the listing.',
            ),
            const SizedBox(height: 12),
            TextField(
              key: const Key('cancel-order-reason'),
              onChanged: (value) => cancellationReason = value,
              maxLength: 240,
              minLines: 2,
              maxLines: 3,
              decoration: const InputDecoration(
                hintText: 'Reason (at least 20 characters)',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Keep request'),
          ),
          FilledButton(
            key: const Key('confirm-cancel-request'),
            onPressed: () => Navigator.of(dialogContext).pop(
              cancellationReason.trim(),
            ),
            child: const Text('Cancel request'),
          ),
        ],
      ),
    );
    if (!mounted || reason == null) { return; }
    if (reason.length < 20 || reason.length > 240) {
      setState(() {
        _error = 'Explain the cancellation in 20–240 characters.';
      });
      return;
    }
    setState(() {
      _busyId = request.id;
      _error = '';
    });
    try {
      await widget.api.cancelUnfundedOrderIntent(request.id, reason);
      if (mounted) { _refresh(); }
    } on ApiFailure catch (error) {
      if (mounted) { setState(() { _error = error.message; }); }
    } catch (_) {
      if (mounted) {
        setState(() { _error = 'Cancellation could not be confirmed. Retry.'; });
      }
    } finally {
      if (mounted) { setState(() { _busyId = null; }); }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Order requests')),
      body: FutureBuilder<List<OrderIntentReceipt>>(
        future: _requests,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('Could not load private order requests.'),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: _refresh,
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
            );
          }
          final requests = snapshot.data ?? [];
          return RefreshIndicator(
            onRefresh: () async {
              _refresh();
              await _requests;
            },
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              children: [
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text(
                      'Checkout is not live. These are records of agreed '
                      'prices only: Anima has not collected money, reserved '
                      'an animal or secured delivery. Do not make '
                      'off-platform transfers.',
                    ),
                  ),
                ),
                if (_error.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    child: Text(_error, style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    )),
                  ),
                if (requests.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 38),
                    child: Center(child: Text(
                      'No order requests yet. An accepted buyer offer '
                      'can be prepared here without payment.',
                      textAlign: TextAlign.center,
                    )),
                  ),
                for (final item in requests)
                  Card(
                    key: ValueKey(item.id),
                    child: Padding(
                      padding: const EdgeInsets.all(15),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item.listingTitle,
                            style: Theme.of(context).textTheme.titleMedium),
                          const SizedBox(height: 6),
                          Text('${item.animalName} • ${item.region}'),
                          Text(item.priceDisplay,
                            style: Theme.of(context).textTheme.titleMedium),
                          const SizedBox(height: 6),
                          Text(item.statusLabel),
                          const SizedBox(height: 6),
                          const Text('No payment received • No reservation'),
                          if (item.status == 'awaiting_partner') ...[
                            const SizedBox(height: 12),
                            OutlinedButton.icon(
                              key: const Key('cancel-intent'),
                              onPressed: _busyId != null
                                  ? null : () => _cancel(item),
                              icon: const Icon(Icons.cancel_outlined),
                              label: const Text('Cancel request'),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
