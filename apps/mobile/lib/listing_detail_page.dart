import 'package:flutter/material.dart';

import 'core/api_client.dart';

/// Read-only detail view from a moderated social video or the marketplace.
class ListingDetailPage extends StatefulWidget {
  const ListingDetailPage({
    required this.api,
    required this.listingId,
    super.key,
  });
  final ApiClient api;
  final String listingId;

  @override
  State<ListingDetailPage> createState() => _ListingDetailPageState();
}

class _ListingDetailPageState extends State<ListingDetailPage> {
  late Future<AnimalListing> _listing;

  @override
  void initState() {
    super.initState();
    _listing = widget.api.getListing(widget.listingId);
  }

  void _retry() {
    setState(() => _listing = widget.api.getListing(widget.listingId));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Animal details')),
      body: FutureBuilder<AnimalListing>(
        future: _listing,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('This listing is not available.'),
                const SizedBox(height: 10),
                OutlinedButton(onPressed: _retry, child: const Text('Retry')),
              ],
            ));
          }
          final animal = snapshot.data!;
          return ListView(
            children: [
              if (animal.photoUrls.isNotEmpty)
                SizedBox(
                  height: 300,
                  child: PageView.builder(
                    itemCount: animal.photoUrls.length,
                    itemBuilder: (context, index) => Image.network(
                      Uri.parse(apiBaseUrl)
                          .resolve(animal.photoUrls[index]).toString(),
                      fit: BoxFit.cover,
                      errorBuilder: (_, _, _) =>
                          const Center(child: Icon(Icons.pets, size: 58)),
                    ),
                  ),
                )
              else
                const SizedBox(
                  height: 220,
                  child: Center(child: Icon(Icons.pets, size: 70)),
                ),
              Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(animal.title, style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 8),
                    Text(animal.displayPrice,
                        style: Theme.of(context).textTheme.titleLarge),
                    const SizedBox(height: 14),
                    Text('${animal.speciesName} • ${animal.region}'),
                    Text('Animal: ${animal.animalName}'),
                    Text('Seller: ${animal.sellerName}'),
                    const SizedBox(height: 18),
                    Text(animal.description),
                    const SizedBox(height: 24),
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(16),
                        child: Text(
                          'Messaging and protected checkout are not available yet. '
                          'A public listing is not a guarantee of animal health '
                          'or a promise of payment protection.',
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
