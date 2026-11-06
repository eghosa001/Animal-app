import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'core/api_client.dart';

/// A deliberately narrow workflow: draft listing photos and private seller evidence.
/// It does not imply a verified identity, approved animal, or active sale.
class SellerMediaPage extends StatefulWidget {
  const SellerMediaPage({required this.api, super.key});

  final ApiClient api;

  @override
  State<SellerMediaPage> createState() => _SellerMediaPageState();
}

class _SellerMediaPageState extends State<SellerMediaPage> {
  final ImagePicker _picker = ImagePicker();
  List<Map<String, dynamic>> _drafts = [];
  List<Map<String, dynamic>> _uploaded = [];
  String _mode = 'listing_photo';
  String _evidenceType = 'identity';
  String? _listingId;
  XFile? _selectedImage;
  String? _selectedMimeType;
  String _message = '';
  bool _error = false;
  bool _busy = false;
  bool _loading = true;
  bool _consent = false;

  @override
  void initState() {
    super.initState();
    _load();
    _recoverLostAndroidPhoto();
  }

  Future<void> _recoverLostAndroidPhoto() async {
    try {
      final result = await _picker.retrieveLostData();
      if (!mounted || result.isEmpty || result.files == null || result.files!.isEmpty) {
        return;
      }
      await _usePickedFile(result.files!.first);
    } catch (_) {
      // This may be unavailable on iOS, an emulator, or widget tests.
    }
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() => _loading = true);
    }
    try {
      final listings = await widget.api.getMyListings();
      final assets = await widget.api.getMyMedia();
      if (!mounted) {
        return;
      }
      final drafts = listings.where((item) => item['status'] == 'draft').toList();
      setState(() {
        _drafts = drafts;
        _uploaded = assets;
        if (!_drafts.any((item) => item['id'] == _listingId)) {
          _listingId = null;
        }
        _loading = false;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _loading = false;
        _error = true;
        _message = error is ApiFailure ? error.message : 'Could not load your seller uploads.';
      });
    }
  }

  void _changeMode(String mode) {
    setState(() {
      _mode = mode;
      _selectedImage = null;
      _selectedMimeType = null;
      _message = '';
      _error = false;
    });
  }

  Future<void> _usePickedFile(XFile file) async {
    String? mimeType = file.mimeType?.toLowerCase();
    if (mimeType != 'image/jpeg' && mimeType != 'image/png') {
      final name = file.name.toLowerCase();
      if (name.endsWith('.jpg') || name.endsWith('.jpeg')) {
        mimeType = 'image/jpeg';
      } else if (name.endsWith('.png')) {
        mimeType = 'image/png';
      }
    }
    if (mimeType != 'image/jpeg' && mimeType != 'image/png') {
      if (mounted) {
        setState(() {
          _error = true;
          _message = 'Select a JPEG or PNG photo. HEIC and PDF are not supported yet.';
        });
      }
      return;
    }
    final bytes = await file.length();
    final limit = _mode == 'seller_evidence' ? 5 * 1024 * 1024 : 8 * 1024 * 1024;
    if (bytes <= 0 || bytes > limit) {
      if (mounted) {
        setState(() {
          _error = true;
          _message = 'This image is empty or exceeds the upload size limit.';
        });
      }
      return;
    }
    if (!mounted) {
      return;
    }
    setState(() {
      _selectedImage = file;
      _selectedMimeType = mimeType;
      _message = '';
      _error = false;
    });
  }

  Future<void> _pickPhoto() async {
    try {
      final image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 2400,
        maxHeight: 2400,
        imageQuality: 86,
        requestFullMetadata: false,
      );
      if (image != null) {
        await _usePickedFile(image);
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = true;
          _message = 'Could not open the photo library. Check photo permissions.';
        });
      }
    }
  }

  Future<void> _upload() async {
    final image = _selectedImage;
    final mimeType = _selectedMimeType;
    if (image == null || mimeType == null || _busy) {
      return;
    }
    if (_mode == 'listing_photo' && _listingId == null) {
      setState(() {
        _error = true;
        _message = 'Choose your draft listing first.';
      });
      return;
    }
    if (_mode == 'seller_evidence' && !_consent) {
      setState(() {
        _error = true;
        _message = 'Confirm private verification processing before uploading.';
      });
      return;
    }
    setState(() {
      _busy = true;
      _message = '';
      _error = false;
    });
    try {
      await widget.api.uploadPrivateImage(
        path: image.path,
        mimeType: mimeType,
        listingId: _mode == 'listing_photo' ? _listingId : null,
        evidenceType: _mode == 'seller_evidence' ? _evidenceType : null,
        consent: _consent,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _selectedImage = null;
        _selectedMimeType = null;
        _consent = false;
        _message = _mode == 'seller_evidence'
            ? 'Private evidence received. It still requires human verification.'
            : 'Photo received. It will remain private until approved for a live listing.';
      });
      await _load();
    } on ApiFailure catch (error) {
      if (mounted) {
        setState(() {
          _error = true;
          _message = error.message;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = true;
          _message = 'Upload failed. Check your connection and retry.';
        });
      }
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final evidence = _mode == 'seller_evidence';
    return Scaffold(
      appBar: AppBar(title: const Text('Seller media')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text('Upload securely', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            const Text('Animal photos and verification evidence are stored privately. Publication and seller verification require separate staff reviews.'),
            const SizedBox(height: 18),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'listing_photo', label: Text('Animal photos'), icon: Icon(Icons.pets_outlined)),
                ButtonSegment(value: 'seller_evidence', label: Text('Verification'), icon: Icon(Icons.verified_user_outlined)),
              ],
              selected: {_mode},
              onSelectionChanged: (selection) => _changeMode(selection.first),
            ),
            const SizedBox(height: 18),
            if (_loading) const LinearProgressIndicator(),
            if (!evidence) ...[
              Text('Choose an existing draft', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 6),
              if (_drafts.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Text('You have no draft listings yet. Draft creation is being developed separately; photos can be attached once a draft exists.'),
                )
              else
                DropdownButton<String>(
                  isExpanded: true,
                  value: _listingId,
                  hint: const Text('Select draft listing'),
                  items: _drafts.map((item) {
                    return DropdownMenuItem<String>(
                      value: item['id'] as String,
                      child: Text(item['title']?.toString() ?? 'Untitled draft'),
                    );
                  }).toList(),
                  onChanged: _busy ? null : (value) => setState(() => _listingId = value),
                ),
              const Text('JPEG/PNG only, maximum 8 MB. A moderator must approve the photo before the listing can show it publicly.'),
            ] else ...[
              Text('Verification document category', style: Theme.of(context).textTheme.titleMedium),
              DropdownButton<String>(
                value: _evidenceType,
                isExpanded: true,
                items: const [
                  DropdownMenuItem(value: 'identity', child: Text('Identity document photo')),
                  DropdownMenuItem(value: 'business', child: Text('Business registration')),
                  DropdownMenuItem(value: 'license', child: Text('Breeder or trade licence')),
                  DropdownMenuItem(value: 'other', child: Text('Other verification evidence')),
                ],
                onChanged: _busy ? null : (value) => setState(() => _evidenceType = value ?? 'identity'),
              ),
              const Text('Choose an image of the required document. JPEG/PNG, maximum 5 MB. PDFs are not supported yet.'),
              const SizedBox(height: 8),
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                value: _consent,
                onChanged: _busy ? null : (value) => setState(() => _consent = value ?? false),
                title: const Text('I understand this image is private and will be processed to review my seller application.'),
              ),
              const Text('Do not upload images containing unrelated people or information that is not needed for verification.'),
            ],
            const SizedBox(height: 20),
            OutlinedButton.icon(
              onPressed: _busy ? null : _pickPhoto,
              icon: const Icon(Icons.photo_library_outlined),
              label: const Text('Choose a photo'),
            ),
            if (_selectedImage != null) ...[
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.file(
                  File(_selectedImage!.path),
                  height: 180,
                  fit: BoxFit.contain,
                  errorBuilder: (_, _, _) => const Text('Preview unavailable'),
                ),
              ),
              const SizedBox(height: 6),
              Text(_selectedImage!.name, maxLines: 1, overflow: TextOverflow.ellipsis),
            ],
            const SizedBox(height: 14),
            FilledButton.icon(
              onPressed: _busy || _selectedImage == null || (evidence && !_consent) ||
                  (!evidence && _listingId == null)
                  ? null
                  : _upload,
              icon: const Icon(Icons.cloud_upload_outlined),
              label: Text(_busy ? 'Uploading…' : 'Upload for review'),
            ),
            if (_message.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                _message,
                style: TextStyle(color: _error ? Theme.of(context).colorScheme.error : null),
              ),
            ],
            const SizedBox(height: 25),
            Text('Your uploaded files', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (_uploaded.isEmpty && !_loading)
              const Text('No uploaded images yet.')
            else
              for (final asset in _uploaded)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(asset['kind'] == 'seller_evidence' ? Icons.lock_outline : Icons.image_outlined),
                  title: Text(asset['kind'] == 'seller_evidence'
                      ? 'Private ${asset['evidence_type'] ?? 'verification'} image'
                      : 'Animal listing photograph'),
                  subtitle: Text('Status: ${asset['state'] ?? 'pending review'}'),
                  trailing: const Icon(Icons.shield_outlined),
                ),
            OutlinedButton(
              onPressed: _busy || _loading ? null : _load,
              child: const Text('Refresh upload status'),
            ),
          ],
        ),
      ),
    );
  }
}
