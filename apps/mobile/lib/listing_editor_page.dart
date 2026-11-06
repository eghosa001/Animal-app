import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'core/listing_models.dart';
import 'seller_media_page.dart';

/// Individual-animal editor. Litter and herd inventory modes remain disabled.
class ListingEditorPage extends StatefulWidget {
  const ListingEditorPage({
    required this.api,
    required this.species,
    this.initial,
    this.hasPhotos = false,
    super.key,
  });

  final ApiClient api;
  final List<SpeciesOption> species;
  final Map<String, dynamic>? initial;
  final bool hasPhotos;

  @override
  State<ListingEditorPage> createState() => _ListingEditorPageState();
}

class _ListingEditorPageState extends State<ListingEditorPage> {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _title;
  late final TextEditingController _description;
  late final TextEditingController _price;
  late final TextEditingController _region;
  late final TextEditingController _animalName;
  late final TextEditingController _breed;
  late final TextEditingController _age;
  String _sex = 'unknown';
  int? _speciesId;
  String _error = '';
  bool _saving = false;

  bool get _editing => widget.initial != null;

  @override
  void initState() {
    super.initState();
    final existing = widget.initial ?? {};
    final animalSpecies = existing['species'] as Map<String, dynamic>? ?? {};
    _speciesId = (animalSpecies['id'] as num?)?.toInt();
    _title = TextEditingController(text: existing['title']?.toString() ?? '');
    _description = TextEditingController(text: existing['description']?.toString() ?? '');
    final minor = (existing['price_minor'] as num?)?.toInt();
    _price = TextEditingController(
      text: minor == null ? '' : NairaMoney.formatMinor(minor),
    );
    _region = TextEditingController(text: existing['region']?.toString() ?? '');
    _animalName = TextEditingController(text: existing['animal_name']?.toString() ?? '');
    _breed = TextEditingController(text: existing['breed_label']?.toString() ?? '');
    _age = TextEditingController(
      text: existing['estimated_age_months']?.toString() ?? '',
    );
    _sex = existing['sex']?.toString() ?? 'unknown';
    if (!['male', 'female', 'unknown'].contains(_sex)) {
      _sex = 'unknown';
    }
  }

  @override
  void dispose() {
    _title.dispose();
    _description.dispose();
    _price.dispose();
    _region.dispose();
    _animalName.dispose();
    _breed.dispose();
    _age.dispose();
    super.dispose();
  }

  SpeciesOption? get _selectedSpecies {
    for (final species in widget.species) {
      if (species.id == _speciesId) {
        return species;
      }
    }
    return null;
  }

  String? _lengthValidation(String? text, int min, int max) {
    final value = (text ?? '').trim();
    if (value.length < min || value.length > max) {
      return 'Enter between $min and $max characters';
    }
    return null;
  }

  String? _ageValidation(String? value) {
    final age = value?.trim() ?? '';
    if (age.isEmpty) {
      return null; // Unknown age is not invented.
    }
    final number = int.tryParse(age);
    return number != null && number >= 0 && number <= 1200
        ? null
        : 'Enter an age of 0–1200 months, or leave blank';
  }

  Map<String, dynamic> _requestData() => {
    'title': _title.text.trim(),
    'description': _description.text.trim(),
    'price_minor': NairaMoney.parseMinor(_price.text)!,
    'currency': 'NGN',
    'region': _region.text.trim(),
    'species_id': _speciesId,
    'animal_name': _animalName.text.trim(),
    'breed_label': _breed.text.trim(),
    'sex': _sex,
    'estimated_age_months': _age.text.trim().isEmpty
        ? null
        : int.parse(_age.text.trim()),
  };

  Future<void> _save({required bool addPhotos}) async {
    if (_saving || !_form.currentState!.validate()) {
      return;
    }
    if (_selectedSpecies == null) {
      setState(() => _error = 'Choose an animal category before saving.');
      return;
    }
    setState(() {
      _saving = true;
      _error = '';
    });
    try {
      final saved = await widget.api.saveListingDraft(
        _requestData(),
        listingId: widget.initial?['id']?.toString(),
      );
      if (!mounted) {
        return;
      }
      if (addPhotos) {
        await Navigator.of(context).push<void>(
          MaterialPageRoute(
            builder: (context) => SellerMediaPage(
              api: widget.api,
              initialListingId: saved['id']?.toString(),
            ),
          ),
        );
      }
      if (mounted) {
        Navigator.of(context).pop(true);
      }
    } on ApiFailure catch (error) {
      if (mounted) {
        setState(() => _error = error.message);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Could not save your draft. Check the network and try again.');
      }
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final species = _selectedSpecies;
    return Scaffold(
      appBar: AppBar(title: Text(_editing ? 'Edit animal draft' : 'Create animal listing')),
      body: SafeArea(
        child: Form(
          key: _form,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text('Individual animal', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              const Text(
                'Create a private draft for one animal. Litter, herd and wholesale '
                'inventory require separate verification and are not enabled.',
              ),
              const SizedBox(height: 18),
              DropdownButtonFormField<int>(
                initialValue: _speciesId,
                isExpanded: true,
                decoration: const InputDecoration(
                  labelText: 'Animal category',
                  border: OutlineInputBorder(),
                ),
                items: widget.species.map((item) => DropdownMenuItem(
                  value: item.id,
                  child: Text(item.name, overflow: TextOverflow.ellipsis),
                )).toList(),
                onChanged: widget.hasPhotos || _saving
                    ? null
                    : (value) => setState(() => _speciesId = value),
                validator: (value) => value == null ? 'Choose an animal category' : null,
              ),
              if (widget.hasPhotos)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: Text('Category is locked after photos are uploaded. '
                      'This prevents photos approved for one species being reused for another.'),
                ),
              if (species != null) ...[
                const SizedBox(height: 8),
                Text(species.inputGuidance),
                if (!species.tradeEnabled)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      'Commercial trading is disabled for this category. '
                      'You may save a private draft, but submission is blocked.',
                      style: TextStyle(color: Theme.of(context).colorScheme.error),
                    ),
                  ),
              ],
              const SizedBox(height: 18),
              TextFormField(
                controller: _title,
                maxLength: 140,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(
                  labelText: 'Listing title',
                  border: OutlineInputBorder(),
                ),
                validator: (value) => _lengthValidation(value, 8, 140),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _animalName,
                maxLength: 120,
                decoration: const InputDecoration(
                  labelText: 'Animal name or individual identifier',
                  border: OutlineInputBorder(),
                ),
                validator: (value) => _lengthValidation(value, 2, 120),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _breed,
                maxLength: 120,
                decoration: InputDecoration(
                  labelText: species?.category == 'aquatic'
                      ? 'Variety/strain, if known'
                      : 'Breed or mix (optional)',
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                initialValue: _sex,
                decoration: const InputDecoration(
                  labelText: 'Sex',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'unknown', child: Text('Unknown')),
                  DropdownMenuItem(value: 'male', child: Text('Male')),
                  DropdownMenuItem(value: 'female', child: Text('Female')),
                ],
                onChanged: _saving
                    ? null
                    : (value) => setState(() => _sex = value ?? 'unknown'),
              ),
              const SizedBox(height: 18),
              TextFormField(
                controller: _age,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Estimated age in months (optional)',
                  helperText: 'Leave blank if unknown; do not guess.',
                  border: OutlineInputBorder(),
                ),
                validator: _ageValidation,
              ),
              const SizedBox(height: 18),
              TextFormField(
                controller: _region,
                maxLength: 140,
                decoration: const InputDecoration(
                  labelText: 'General location (city or state)',
                  helperText: 'Never enter your street or home address here.',
                  border: OutlineInputBorder(),
                ),
                validator: (value) => _lengthValidation(value, 2, 140),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _price,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Price in naira (₦)',
                  helperText: 'Example: 25000.00. Payment is disabled in this preview.',
                  border: OutlineInputBorder(),
                ),
                validator: (value) => NairaMoney.parseMinor(value ?? '') == null
                    ? 'Enter a positive price with up to 2 decimal places'
                    : null,
              ),
              const SizedBox(height: 18),
              TextFormField(
                controller: _description,
                maxLength: 4000,
                maxLines: 6,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(
                  labelText: 'Description and truthful condition disclosures',
                  helperText: 'Do not claim verified health or pedigree without evidence.',
                  border: OutlineInputBorder(),
                ),
                validator: (value) => _lengthValidation(value, 20, 4000),
              ),
              const SizedBox(height: 8),
              if (_error.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(
                    _error,
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                  ),
                ),
              FilledButton.icon(
                onPressed: _saving ? null : () => _save(addPhotos: false),
                icon: const Icon(Icons.save_outlined),
                label: Text(_saving ? 'Saving…' : 'Save private draft'),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: _saving ? null : () => _save(addPhotos: true),
                icon: const Icon(Icons.add_photo_alternate_outlined),
                label: const Text('Save and manage photos'),
              ),
              const SizedBox(height: 12),
              const Text(
                'Saving does not publish your animal. Seller approval, eligible '
                'species, a photo, and human moderation are required before it can appear publicly.',
              ),
            ],
          ),
        ),
      ),
    );
  }
}
