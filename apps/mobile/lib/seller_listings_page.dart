import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'core/listing_models.dart';
import 'listing_editor_page.dart';
import 'seller_media_page.dart';

/// Seller workspace. All listing mutations are re-authorized by the backend.
class SellerListingsPage extends StatefulWidget {
  const SellerListingsPage({
    required this.api,
    this.onOpenAccount,
    super.key,
  });

  final ApiClient api;
  final VoidCallback? onOpenAccount;

  @override
  State<SellerListingsPage> createState() => _SellerListingsPageState();
}

class _SellerListingsPageState extends State<SellerListingsPage> {
  bool _loading = true;
  bool _loggedIn = false;
  String? _sellerStatus;
  String? _busyListing;
  String _error = '';
  String _notice = '';
  List<SpeciesOption> _species = [];
  List<Map<String, dynamic>> _listings = [];
  List<Map<String, dynamic>> _media = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (!mounted) {
      return;
    }
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final account = await widget.api.me();
      if (account == null) {
        if (mounted) {
          setState(() {
            _loggedIn = false;
            _sellerStatus = null;
            _loading = false;
          });
        }
        return;
      }
      final status = account['seller_status']?.toString();
      if (status != 'pending' && status != 'approved') {
        if (mounted) {
          setState(() {
            _loggedIn = true;
            _sellerStatus = status;
            _loading = false;
          });
        }
        return;
      }
      final species = await widget.api.getSpecies();
      final listings = await widget.api.getMyListings();
      final media = await widget.api.getMyMedia();
      if (!mounted) {
        return;
      }
      setState(() {
        _loggedIn = true;
        _sellerStatus = status;
        _species = species;
        _listings = listings;
        _media = media;
        _loading = false;
      });
    } catch (error) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = error is ApiFailure
              ? error.message
              : 'Could not load your listings. Check your connection.';
        });
      }
    }
  }

  List<Map<String, dynamic>> _photosFor(String listingId) {
    return _media.where((asset) =>
      asset['listing']?.toString() == listingId &&
      asset['kind'] == 'listing_photo'
    ).toList();
  }

  Future<void> _openEditor([Map<String, dynamic>? draft]) async {
    final id = draft?['id']?.toString();
    final photos = id == null ? 0 : _photosFor(id).length;
    final updated = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (context) => ListingEditorPage(
          api: widget.api,
          species: _species,
          initial: draft,
          hasPhotos: photos > 0,
        ),
      ),
    );
    if (updated == true) {
      await _load();
    }
  }

  Future<void> _openPhotos(String listingId) async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (context) => SellerMediaPage(
          api: widget.api,
          initialListingId: listingId,
        ),
      ),
    );
    await _load();
  }

  Future<void> _submit(Map<String, dynamic> listing) async {
    final id = listing['id']?.toString();
    if (id == null) {
      return;
    }
    final species = listing['species'] as Map<String, dynamic>? ?? {};
    if (_sellerStatus != 'approved') {
      setState(() => _notice = 'Seller approval is required before submission.');
      return;
    }
    if (species['trade_enabled'] != true) {
      setState(() => _notice = 'This species is not yet approved for trading.');
      return;
    }
    final photos = _photosFor(id);
    if (photos.every((a) => a['state'] != 'pending' && a['state'] != 'approved')) {
      setState(() => _notice = 'Upload an animal photo before submitting.');
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Submit for review?'),
        content: const Text(
          'Staff will review this listing. You cannot change its details '
          'or add photos after submitting. Uploads must pass separate moderation.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Keep editing'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Submit'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }
    setState(() {
      _busyListing = id;
      _notice = '';
    });
    try {
      await widget.api.submitListing(id);
      if (!mounted) {
        return;
      }
      setState(() => _notice = 'Listing submitted for moderator review.');
      await _load();
    } on ApiFailure catch (error) {
      if (mounted) {
        setState(() => _notice = error.message);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _notice = 'Submission failed. Try again when online.');
      }
    } finally {
      if (mounted) {
        setState(() => _busyListing = null);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error.isNotEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(_error, textAlign: TextAlign.center),
            ),
            OutlinedButton(onPressed: _load, child: const Text('Retry')),
          ],
        ),
      );
    }
    if (!_loggedIn || (_sellerStatus != 'pending' && _sellerStatus != 'approved')) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.pets_outlined, size: 52),
              const SizedBox(height: 12),
              Text(
                !_loggedIn
                    ? 'Sign in to create animal listings'
                    : 'Seller application required',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              const Text(
                'Verify your email and apply as a seller in your profile. '
                'Only eligible sellers may create private listing drafts.',
                textAlign: TextAlign.center,
              ),
              if (widget.onOpenAccount != null)
                FilledButton(
                  onPressed: widget.onOpenAccount,
                  child: const Text('Go to profile'),
                ),
              OutlinedButton(onPressed: _load, child: const Text('Refresh')),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        children: [
          Text('Manage animal listings', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 6),
          Text(
            _sellerStatus == 'approved'
                ? 'Seller approved. Each animal and photo still needs listing moderation.'
                : 'Your seller application is pending. You can prepare drafts but cannot publish yet.',
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _species.isEmpty ? null : () => _openEditor(),
            icon: const Icon(Icons.add_circle_outline),
            label: const Text('Create listing'),
          ),
          const SizedBox(height: 8),
          if (_notice.isNotEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Text(_notice),
            ),
          if (_species.isEmpty)
            const Text('No animal categories available. Ask an administrator to seed the catalogue.'),
          if (_listings.isEmpty) ...[
            const SizedBox(height: 26),
            const Center(child: Text('No listings yet. Create a draft to begin.')),
          ],
          for (final item in _listings) _listingCard(item),
        ],
      ),
    );
  }

  Widget _listingCard(Map<String, dynamic> item) {
    final id = item['id']?.toString() ?? '';
    final state = item['status']?.toString() ?? 'unknown';
    final draft = state == 'draft';
    final species = item['species'] as Map<String, dynamic>? ?? {};
    final photos = _photosFor(id);
    final enabled = _busyListing == null;
    final canSubmit = draft && enabled && _sellerStatus == 'approved' &&
        species['trade_enabled'] == true &&
        photos.any((p) => p['state'] == 'pending' || p['state'] == 'approved');

    return Card(
      margin: const EdgeInsets.only(top: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item['title']?.toString() ?? 'Untitled animal',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 6),
            Text('${species['name'] ?? 'Animal'} • ${item['region'] ?? ''}'),
            const SizedBox(height: 4),
            Text('Status: $state • ${photos.length} photo(s)'),
            if (species['trade_enabled'] != true)
              const Text('This category is disabled for trading. Drafts remain private.'),
            if (draft)
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  OutlinedButton.icon(
                    onPressed: enabled ? () => _openEditor(item) : null,
                    icon: const Icon(Icons.edit_outlined),
                    label: const Text('Edit draft'),
                  ),
                  OutlinedButton.icon(
                    onPressed: enabled ? () => _openPhotos(id) : null,
                    icon: const Icon(Icons.photo_library_outlined),
                    label: const Text('Manage photos'),
                  ),
                  FilledButton(
                    onPressed: canSubmit ? () => _submit(item) : null,
                    child: Text(_busyListing == id ? 'Submitting…' : 'Submit for review'),
                  ),
                ],
              )
            else
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: Text('Submitted and published details are locked against seller edits.'),
              ),
          ],
        ),
      ),
    );
  }
}
