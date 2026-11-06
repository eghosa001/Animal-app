import 'package:flutter/material.dart';

import 'core/api_client.dart';

/// An email recovery code is never passed in a link or stored on the device.
class PasswordRecoveryPage extends StatefulWidget {
  const PasswordRecoveryPage({
    required this.api,
    this.initialEmail = '',
    super.key,
  });

  final ApiClient api;
  final String initialEmail;

  @override
  State<PasswordRecoveryPage> createState() => _PasswordRecoveryPageState();
}

class _PasswordRecoveryPageState extends State<PasswordRecoveryPage> {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _email;
  final TextEditingController _code = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _confirm = TextEditingController();
  bool _codeStep = false;
  bool _busy = false;
  bool _showPassword = false;
  String _message = '';
  bool _error = false;

  @override
  void initState() {
    super.initState();
    _email = TextEditingController(text: widget.initialEmail);
  }

  @override
  void dispose() {
    _email.dispose();
    _code.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  String? _validateEmail(String? text) {
    final email = (text ?? '').trim();
    if (email.length > 254 || !RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(email)) {
      return 'Enter a valid email address';
    }
    return null;
  }

  Future<void> _requestCode() async {
    if (_busy || !_form.currentState!.validate()) {
      return;
    }
    setState(() {
      _busy = true;
      _error = false;
      _message = '';
    });
    try {
      await widget.api.requestPasswordReset(_email.text);
      if (!mounted) return;
      setState(() {
        _codeStep = true;
        _message = 'If an active account exists, a recovery code will be emailed. '
            'The code expires in 20 minutes. Repeated requests may be limited.';
      });
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
          _message = 'Could not connect. Check your internet and try again.';
        });
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _confirmCode() async {
    if (_busy || !_form.currentState!.validate()) {
      return;
    }
    setState(() {
      _busy = true;
      _error = false;
      _message = '';
    });
    try {
      await widget.api.confirmPasswordReset(
        email: _email.text,
        code: _code.text,
        newPassword: _password.text,
      );
      if (!mounted) return;
      // The backend invalidates every previously issued session.
      Navigator.of(context).pop(true);
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
          _message = 'Could not reset the password. Check the connection and retry.';
        });
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Recover your account')),
      body: SafeArea(
        child: Form(
          key: _form,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const Icon(Icons.lock_reset_outlined, size: 48),
              const SizedBox(height: 12),
              Text(
                _codeStep ? 'Enter your recovery code' : 'Reset your password',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              Text(
                _codeStep
                    ? 'Check your email. You can paste the recovery code below.'
                    : 'Enter your registered email. For privacy, we will not confirm whether that address has an account.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              TextFormField(
                key: const Key('recovery-email'),
                controller: _email,
                readOnly: _busy || _codeStep,
                autocorrect: false,
                keyboardType: TextInputType.emailAddress,
                autofillHints: const [AutofillHints.email],
                decoration: const InputDecoration(
                  labelText: 'Email address',
                  border: OutlineInputBorder(),
                ),
                validator: _validateEmail,
              ),
              if (_codeStep) ...[
                const SizedBox(height: 18),
                TextFormField(
                  key: const Key('recovery-code'),
                  controller: _code,
                  autocorrect: false,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Recovery code',
                    helperText: 'Enter the code from your email, without spaces.',
                    border: OutlineInputBorder(),
                  ),
                  validator: (text) => (text ?? '').trim().isEmpty
                      ? 'Enter your recovery code'
                      : (text!.trim().length > 256 ? 'Invalid code length' : null),
                ),
                const SizedBox(height: 18),
                TextFormField(
                  key: const Key('recovery-new-password'),
                  controller: _password,
                  obscureText: !_showPassword,
                  autofillHints: const [AutofillHints.newPassword],
                  decoration: InputDecoration(
                    labelText: 'New password',
                    border: const OutlineInputBorder(),
                    suffixIcon: IconButton(
                      tooltip: _showPassword ? 'Hide password' : 'Show password',
                      onPressed: () => setState(() => _showPassword = !_showPassword),
                      icon: Icon(_showPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                    ),
                  ),
                  validator: (text) => (text ?? '').length < 10
                      ? 'Use at least 10 characters'
                      : null,
                ),
                const SizedBox(height: 18),
                TextFormField(
                  key: const Key('recovery-password-confirmation'),
                  controller: _confirm,
                  obscureText: !_showPassword,
                  autofillHints: const [AutofillHints.newPassword],
                  decoration: const InputDecoration(
                    labelText: 'Confirm new password',
                    border: OutlineInputBorder(),
                  ),
                  validator: (text) {
                    if (text != _password.text) {
                      return 'Passwords do not match';
                    }
                    return null;
                  },
                ),
              ],
              if (_message.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text(
                  _message,
                  style: TextStyle(
                    color: _error ? Theme.of(context).colorScheme.error : null,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
              const SizedBox(height: 20),
              FilledButton.icon(
                key: const Key('recovery-primary-action'),
                onPressed: _busy ? null : (_codeStep ? _confirmCode : _requestCode),
                icon: Icon(_codeStep ? Icons.lock_open_outlined : Icons.mail_outline),
                label: Text(
                  _busy ? 'Processing…' : (_codeStep ? 'Update password' : 'Send recovery code'),
                ),
              ),
              if (_codeStep) ...[
                TextButton(
                  onPressed: _busy ? null : () => setState(() {
                    _codeStep = false;
                    _code.clear();
                    _password.clear();
                    _confirm.clear();
                    _message = '';
                    _error = false;
                  }),
                  child: const Text('Request another code or change email'),
                ),
                const Text(
                  'A successful reset signs out previous sessions. Sign in again with the new password.',
                  textAlign: TextAlign.center,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
