import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'core/chat_models.dart';
import 'core/listing_models.dart';
import 'core/offer_models.dart';

class _OfferScreenData {
  const _OfferScreenData({required this.currentUserId, required this.offers});
  final String currentUserId;
  final List<AnimalOfferQuote> offers;
}

/// Verified participants negotiate a price only; checkout is disabled.
class OfferNegotiationPage extends StatefulWidget {
  const OfferNegotiationPage({
    required this.api,
    required this.conversation,
    super.key,
  });
  final ApiClient api;
  final ChatConversation conversation;

  @override
  State<OfferNegotiationPage> createState() => _OfferNegotiationPageState();
}

class _OfferNegotiationPageState extends State<OfferNegotiationPage> {
  final _amount = TextEditingController();
  late Future<_OfferScreenData> _state;
  bool _busy = false;
  String _error = '';
  String? _pendingNonce;
  int? _pendingAmount;

  @override
  void initState() {
    super.initState();
    _state = _fetch();
  }

  Future<_OfferScreenData> _fetch() async {
    final profile = await widget.api.me();
    if (profile == null || profile['id'] == null) {
      throw const ApiFailure('Sign in to review price proposals');
    }
    final offers = await widget.api.getConversationOffers(
      widget.conversation.id,
    );
    return _OfferScreenData(
      currentUserId: profile['id'].toString(), offers: offers,
    );
  }

  void _reload() {
    final next = _fetch();
    setState(() {
      _state = next;
      _error = '';
    });
  }

  Future<void> _propose() async {
    if (_busy || !widget.conversation.canSend) { return; }
    final amount = NairaMoney.parseMinor(_amount.text);
    if (amount == null) {
      setState(() { _error = 'Enter a positive NGN amount, using at most two decimals.'; });
      return;
    }
    if (_pendingAmount != amount || _pendingNonce == null) {
      _pendingAmount = amount;
      _pendingNonce = ApiClient.newChatNonce();
    }
    setState(() {
      _busy = true;
      _error = '';
    });
    try {
      await widget.api.proposeAnimalOffer(
        widget.conversation.id, amount,
        clientNonce: _pendingNonce!,
      );
      if (!mounted) { return; }
      _pendingNonce = null;
      _pendingAmount = null;
      _amount.clear();
      _reload();
    } on ApiFailure catch (error) {
      if (mounted) { setState(() { _error = error.message; }); }
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Offer status uncertain. Retry the same amount to avoid duplicates.';
        });
      }
    } finally {
      if (mounted) { setState(() { _busy = false; }); }
    }
  }

  Future<void> _decide(AnimalOfferQuote offer, String decision) async {
    if (_busy) { return; }
    if (decision == 'accept') {
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Accept this price?'),
          content: Text(
            'You agree to ${offer.amountDisplay} for this specific animal. '
            'No payment is made here. Checkout, protected custody and delivery '
            'confirmation are not available yet.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Agree to price'),
            ),
          ],
        ),
      );
      if (confirmed != true || !mounted) { return; }
    }
    setState(() {
      _busy = true;
      _error = '';
    });
    try {
      await widget.api.decideAnimalOffer(offer.id, decision);
      if (mounted) { _reload(); }
    } on ApiFailure catch (error) {
      if (mounted) { setState(() { _error = error.message; }); }
    } catch (_) {
      if (mounted) {
        setState(() { _error = 'Unable to record the offer decision.'; });
      }
    } finally {
      if (mounted) { setState(() { _busy = false; }); }
    }
  }

  @override
  void dispose() {
    _amount.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Price offers')),
      body: FutureBuilder<_OfferScreenData>(
        future: _state,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('Could not load price offers.'),
                OutlinedButton(
                  onPressed: _reload,
                  child: const Text('Retry'),
                ),
              ],
            ));
          }
          final data = snapshot.data!;
          final hasAccepted = data.offers.any((offer) =>
              offer.status == 'accepted');
          final canPropose = widget.conversation.canSend && !hasAccepted;

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(widget.conversation.listingTitle,
                style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              const Text(
                'An offer is a proposed price, not a payment. '
                'Accepting only records agreement; Anima has not received or '
                'protected any funds. Never pay outside the platform.',
              ),
              const SizedBox(height: 18),
              if (_error.isNotEmpty) ...[
                Text(_error, style: TextStyle(
                  color: Theme.of(context).colorScheme.error,
                )),
                const SizedBox(height: 12),
              ],
              if (hasAccepted)
                const Card(child: Padding(
                  padding: EdgeInsets.all(14),
                  child: Text(
                    'Price agreed. Payment and protected checkout remain unavailable.',
                  ),
                ))
              else if (canPropose) ...[
                TextField(
                  controller: _amount,
                  key: const Key('offer-amount'),
                  enabled: !_busy,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    prefixText: '₦ ',
                    labelText: 'Your proposed price in naira',
                    helperText: 'Maximum is the currently listed price. 72-hour expiry.',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 10),
                FilledButton.icon(
                  key: const Key('submit-offer'),
                  onPressed: _busy ? null : _propose,
                  icon: const Icon(Icons.handshake_outlined),
                  label: Text(_busy ? 'Submitting…' : 'Send price proposal'),
                ),
                const SizedBox(height: 12),
              ],
              Row(children: [
                Expanded(child: Text(
                  'Offer history',
                  style: Theme.of(context).textTheme.titleMedium,
                )),
                TextButton(onPressed: _busy ? null : _reload,
                  child: const Text('Refresh')),
              ]),
              if (data.offers.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 20),
                  child: Text('No price proposals yet.'),
                ),
              for (final offer in data.offers)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(offer.amountDisplay,
                          style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 4),
                        Text('Proposed by ${offer.proposerName}'),
                        const SizedBox(height: 4),
                        Text('Status: ${offer.status}'),
                        if (offer.status == 'pending' &&
                            offer.proposerId != data.currentUserId &&
                            widget.conversation.canSend) ...[
                          const SizedBox(height: 10),
                          Row(children: [
                            FilledButton(
                              onPressed: _busy
                                  ? null : () => _decide(offer, 'accept'),
                              child: const Text('Accept price'),
                            ),
                            const SizedBox(width: 10),
                            OutlinedButton(
                              onPressed: _busy
                                  ? null : () => _decide(offer, 'decline'),
                              child: const Text('Decline'),
                            ),
                          ]),
                          const SizedBox(height: 8),
                          const Text('To counter, submit another price above.'),
                        ],
                      ],
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
