import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'password_recovery_page.dart';
import 'revoke_sessions_page.dart';
import 'seller_media_page.dart';
import 'seller_listings_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const AnimaApp());
}

class AnimaApp extends StatelessWidget {
  const AnimaApp({super.key});

  @override
  Widget build(BuildContext context) {
    const seed = Color(0xFF18754A);
    return MaterialApp(
      title: 'Anima',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: seed),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: seed,
        brightness: Brightness.dark,
      ),
      home: const AppShell(),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  final ApiClient _api = ApiClient();
  int _selected = 0;

  @override
  void dispose() {
    _api.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    Widget body;
    switch (_selected) {
      case 0:
        body = HomePage(
          openMarket: () => setState(() => _selected = 1),
          openAccount: () => setState(() => _selected = 4),
        );
      case 1:
        body = MarketplacePage(api: _api);
      case 2:
        body = SellerListingsPage(
          api: _api,
          onOpenAccount: () => setState(() => _selected = 4),
        );
      case 3:
        body = const UpcomingPage(
          icon: Icons.forum_outlined,
          title: 'Buyer and seller messages',
          message: 'Secure listing-linked chat and negotiated offers are planned for the next milestone.',
        );
      default:
        body = AccountPage(api: _api);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Anima')),
      body: SafeArea(child: body),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selected,
        onDestinationSelected: (value) => setState(() => _selected = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.pets_outlined), selectedIcon: Icon(Icons.pets), label: 'Market'),
          NavigationDestination(icon: Icon(Icons.add_box_outlined), selectedIcon: Icon(Icons.add_box), label: 'Create'),
          NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Chats'),
          NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({required this.openMarket, required this.openAccount, super.key});
  final VoidCallback openMarket;
  final VoidCallback openAccount;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const SizedBox(height: 18),
        const Icon(Icons.pets, size: 64),
        const SizedBox(height: 18),
        Text('One community for animals', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 10),
        const Text('Discover animal listings and connect with verified sellers. Social videos and messaging are being built.'),
        const SizedBox(height: 20),
        FilledButton.icon(
          onPressed: openMarket,
          icon: const Icon(Icons.search),
          label: const Text('Browse marketplace'),
        ),
        OutlinedButton.icon(
          onPressed: openAccount,
          icon: const Icon(Icons.person_add_outlined),
          label: const Text('Create an account'),
        ),
        const SizedBox(height: 30),
        const Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Development preview', style: TextStyle(fontWeight: FontWeight.bold)),
                SizedBox(height: 8),
                Text('No payment protection or video content is available in this build. All sales remain disabled until regulated payment and welfare checks are approved.'),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class MarketplacePage extends StatefulWidget {
  const MarketplacePage({required this.api, super.key});
  final ApiClient api;

  @override
  State<MarketplacePage> createState() => _MarketplacePageState();
}

class _MarketplacePageState extends State<MarketplacePage> {
  late Future<List<AnimalListing>> _result;

  @override
  void initState() {
    super.initState();
    _result = widget.api.getListings();
  }

  void _retry() {
    setState(() => _result = widget.api.getListings());
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<AnimalListing>>(
      future: _result,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text('Unable to connect to the marketplace API.'),
                  const SizedBox(height: 12),
                  OutlinedButton(onPressed: _retry, child: const Text('Retry')),
                ],
              ),
            ),
          );
        }
        final listings = snapshot.data ?? [];
        if (listings.isEmpty) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                'No approved animal listings yet. Sellers and animal categories must pass review before they appear here.',
                textAlign: TextAlign.center,
              ),
            ),
          );
        }
        return RefreshIndicator(
          onRefresh: () async {
            final next = widget.api.getListings();
            setState(() => _result = next);
            await next;
          },
          child: ListView.builder(
            padding: const EdgeInsets.all(12),
            itemCount: listings.length,
            itemBuilder: (context, index) {
              final item = listings[index];
              return Card(
                child: ListTile(
                  leading: item.photoUrls.isEmpty
                      ? const Icon(Icons.pets_outlined, size: 34)
                      : ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(
                            Uri.parse(apiBaseUrl).resolve(item.photoUrls.first).toString(),
                            width: 56,
                            height: 56,
                            fit: BoxFit.cover,
                            errorBuilder: (context, error, stackTrace) =>
                                const Icon(Icons.pets_outlined, size: 34),
                          ),
                        ),
                  title: Text(item.title),
                  subtitle: Text('${item.speciesName} • ${item.region}\nSeller: ${item.sellerName}'),
                  isThreeLine: true,
                  trailing: Text(item.displayPrice, style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
              );
            },
          ),
        );
      },
    );
  }
}

class UpcomingPage extends StatelessWidget {
  const UpcomingPage({required this.icon, required this.title, required this.message, super.key});
  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(30),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 58),
            const SizedBox(height: 18),
            Text(title, style: Theme.of(context).textTheme.titleLarge, textAlign: TextAlign.center),
            const SizedBox(height: 10),
            Text(message, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

class AccountPage extends StatefulWidget {
  const AccountPage({required this.api, super.key});
  final ApiClient api;

  @override
  State<AccountPage> createState() => _AccountPageState();
}

class _AccountPageState extends State<AccountPage> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _name = TextEditingController();
  final _token = TextEditingController();
  final _business = TextEditingController();
  Map<String, dynamic>? _profile;
  bool _register = false;
  bool _busy = false;
  bool _adultConfirmed = false;
  String _message = '';

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final profile = await widget.api.me();
      if (mounted) { setState(() => _profile = profile); }
    } catch (_) {
      // Expired sessions are handled by the API client on the next login.
    }
  }

  Future<void> _act(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _message = '';
    });
    try {
      await action();
    } on ApiFailure catch (error) {
      if (mounted) { setState(() => _message = error.message); }
    } catch (_) {
      if (mounted) { setState(() => _message = 'Network error. Please try again.'); }
    } finally {
      if (mounted) { setState(() => _busy = false); }
    }
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _name.dispose();
    _token.dispose();
    _business.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final profile = _profile;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text('Your account', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 12),
        if (profile == null) ...[
          Wrap(
            spacing: 12,
            children: [
              ChoiceChip(label: const Text('Sign in'), selected: !_register, onSelected: (_) => setState(() => _register = false)),
              ChoiceChip(label: const Text('Register'), selected: _register, onSelected: (_) => setState(() => _register = true)),
            ],
          ),
          const SizedBox(height: 14),
          Form(
            key: _formKey,
            child: Column(
              children: [
                if (_register) TextFormField(
                  controller: _name,
                  decoration: const InputDecoration(labelText: 'Display name'),
                  validator: (value) => value == null || value.trim().length < 2 ? 'Enter your name' : null,
                ),
                TextFormField(
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(labelText: 'Email'),
                  validator: (value) => value == null || !value.contains('@') ? 'Enter a valid email' : null,
                ),
                TextFormField(
                  controller: _password,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Password'),
                  validator: (value) => value == null || value.length < 10 ? 'Use at least 10 characters' : null,
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: _busy ? null : () {
              if (!_formKey.currentState!.validate()) { return; }
              _act(() async {
                if (_register) {
                  await widget.api.register(email: _email.text.trim(), displayName: _name.text.trim(), password: _password.text);
                  if (mounted) { setState(() => _message = 'Account registered. Check your email for a verification token; then sign in.'); }
                } else {
                  await widget.api.login(_email.text.trim(), _password.text);
                  final profile = await widget.api.me();
                  if (mounted) { setState(() => _profile = profile); }
                }
              });
            },
            child: Text(_register ? 'Register' : 'Sign in'),
          ),
          if (!_register)
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: _busy
                    ? null
                    : () async {
                        final recovered = await Navigator.of(context).push<bool>(
                          MaterialPageRoute(
                            builder: (context) => PasswordRecoveryPage(
                              api: widget.api,
                              initialEmail: _email.text.trim(),
                            ),
                          ),
                        );
                        if (recovered == true && mounted) {
                          setState(() {
                            _password.clear();
                            _message = 'Password updated. Sign in with your new password.';
                          });
                        }
                      },
                child: const Text('Forgot password?'),
              ),
            ),
          const SizedBox(height: 16),
          TextField(controller: _token, decoration: const InputDecoration(labelText: 'Email verification token')),
          const SizedBox(height: 8),
          OutlinedButton(
            onPressed: _busy ? null : () => _act(() async {
              await widget.api.verifyEmail(_email.text.trim(), _token.text.trim());
              if (mounted) { setState(() => _message = 'Email verified. You may now sign in.'); }
            }),
            child: const Text('Verify email'),
          ),
          OutlinedButton(
            onPressed: _busy ? null : () => _act(() async {
              await widget.api.resendVerification(_email.text.trim());
              if (mounted) { setState(() => _message =
                'If verification is still needed, a new code will be emailed. Repeated requests may be limited.'); }
            }),
            child: const Text('Resend verification code'),
          ),
        ] else ...[
          ListTile(title: Text(profile['display_name']?.toString() ?? ''), subtitle: Text(profile['email']?.toString() ?? '')),
          ListTile(
            leading: Icon(profile['email_verified'] == true ? Icons.verified : Icons.warning_amber_outlined),
            title: Text(profile['email_verified'] == true ? 'Email verified' : 'Email not verified'),
            subtitle: Text('Seller status: ${profile['seller_status'] ?? 'Not applied'}'),
          ),
          if (profile['email_verified'] != true) ...[
            TextField(
              controller: _token,
              decoration: const InputDecoration(labelText: 'Email verification token'),
            ),
            OutlinedButton(
              onPressed: _busy ? null : () => _act(() async {
                await widget.api.verifyEmail(profile['email']?.toString() ?? '', _token.text.trim());
                await _loadProfile();
                if (mounted) { setState(() => _message = 'Your email is verified.'); }
              }),
              child: const Text('Verify email'),
            ),
            OutlinedButton(
              onPressed: _busy ? null : () => _act(() async {
                await widget.api.resendVerification(profile['email']?.toString() ?? '');
                if (mounted) { setState(() => _message =
                  'If verification is still needed, a new code will be emailed. Repeated requests may be limited.'); }
              }),
              child: const Text('Resend verification code'),
            ),
          ],
          if (profile['seller_status'] == null && profile['email_verified'] == true) ...[
            TextField(controller: _business, decoration: const InputDecoration(labelText: 'Breeder or seller business name')),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('I confirm I am an adult and eligible to apply as a seller'),
              value: _adultConfirmed,
              onChanged: _busy ? null : (checked) => setState(() => _adultConfirmed = checked ?? false),
            ),
            const SizedBox(height: 10),
            FilledButton(
              onPressed: _busy || !_adultConfirmed ? null : () => _act(() async {
                await widget.api.applyAsSeller(_business.text.trim(), adultAttested: _adultConfirmed);
                await _loadProfile();
                if (mounted) { setState(() => _message = 'Application submitted for staff review. Approval is not automatic.'); }
              }),
              child: const Text('Apply to become a seller (adults only)'),
            ),
          ],
          if (profile['seller_status'] == 'pending' || profile['seller_status'] == 'approved') ...[
            FilledButton.icon(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (context) => SellerListingsPage(api: widget.api),
                ),
              ),
              icon: const Icon(Icons.pets_outlined),
              label: const Text('Manage animal listings'),
            ),
            OutlinedButton.icon(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (context) => SellerMediaPage(api: widget.api),
                ),
              ),
              icon: const Icon(Icons.cloud_upload_outlined),
              label: const Text('Upload animal photos or verification'),
            ),
          ],
          OutlinedButton.icon(
            onPressed: _busy ? null : () async {
              final revoked = await Navigator.of(context).push<bool>(
                MaterialPageRoute<bool>(
                  builder: (context) => RevokeSessionsPage(api: widget.api),
                ),
              );
              if (revoked == true && mounted) {
                setState(() {
                  _profile = null;
                  _password.clear();
                  _message = 'Signed out of all devices. Sign in again to continue.';
                });
              }
            },
            icon: const Icon(Icons.phonelink_lock_outlined),
            label: const Text('Sign out on all devices'),
          ),
          OutlinedButton(
            onPressed: _busy ? null : () => _act(() async {
              await widget.api.logout();
              if (mounted) { setState(() => _profile = null); }
            }),
            child: const Text('Sign out'),
          ),
        ],
        if (_busy) const LinearProgressIndicator(),
        if (_message.isNotEmpty) Padding(
          padding: const EdgeInsets.only(top: 16),
          child: Text(_message),
        ),
      ],
    );
  }
}
