import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'seller_listings_page.dart';
import 'video_upload_page.dart';

/// One Create tab for animal community videos and eligible marketplace listings.
class CreateHubPage extends StatelessWidget {
  const CreateHubPage({
    required this.api,
    required this.onOpenAccount,
    super.key,
  });

  final ApiClient api;
  final VoidCallback onOpenAccount;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text('Create', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        const Text(
          'Share animal moments with the community, or prepare a listing '
          'for a permitted animal. Every public post needs review.',
        ),
        const SizedBox(height: 24),
        Card(
          child: ListTile(
            contentPadding: const EdgeInsets.all(14),
            leading: const Icon(Icons.movie_creation_outlined, size: 35),
            title: const Text('Post an animal video'),
            subtitle: const Text(
              'Choose your own short clip and submit it for safety review.',
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (context) => VideoUploadPage(api: api),
              ),
            ),
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: ListTile(
            contentPadding: const EdgeInsets.all(14),
            leading: const Icon(Icons.pets_outlined, size: 35),
            title: const Text('List or manage an animal'),
            subtitle: const Text(
              'Create drafts, add photos and request seller listing approval.',
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (context) => Scaffold(
                  appBar: AppBar(title: const Text('Animal listings')),
                  body: SellerListingsPage(
                    api: api,
                    onOpenAccount: () {
                      Navigator.of(context).pop();
                      onOpenAccount();
                    },
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
