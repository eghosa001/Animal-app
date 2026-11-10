import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'core/api_client.dart';

/// A private creator upload workflow. Upload never implies public approval.
class VideoUploadPage extends StatefulWidget {
  const VideoUploadPage({required this.api, super.key});

  final ApiClient api;

  @override
  State<VideoUploadPage> createState() => _VideoUploadPageState();
}

class _VideoUploadPageState extends State<VideoUploadPage> {
  final _caption = TextEditingController();
  final _picker = ImagePicker();
  XFile? _video;
  bool _enabled = false;
  bool _loading = true;
  bool _busy = false;
  bool _rights = false;
  bool _animalTopic = false;
  String _notice = '';
  String _error = '';
  int _limitBytes = 200000000;
  List<Map<String, dynamic>> _posts = [];

  @override
  void initState() {
    super.initState();
    _loadCapabilities();
  }

  Future<void> _loadCapabilities() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final settings = await widget.api.getVideoUploadCapabilities();
      if (!mounted) return;
      setState(() {
        _enabled = settings['enabled'] == true;
        _limitBytes = settings['max_file_bytes'] as int;
      });
      if (_enabled) await _refreshPosts();
    } on ApiFailure catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) setState(() =>
          _error = 'Unable to check video upload availability.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _refreshPosts() async {
    try {
      final posts = await widget.api.getMyVideos();
      if (mounted) setState(() => _posts = posts);
    } on ApiFailure catch (error) {
      if (mounted) setState(() => _notice = error.message);
    } catch (_) {
      if (mounted) setState(() =>
          _notice = 'Could not refresh your video status.');
    }
  }

  Future<void> _selectVideo() async {
    if (!_enabled || _busy) return;
    try {
      final selected = await _picker.pickVideo(
        source: ImageSource.gallery,
      );
      if (selected == null) return;
      final path = selected.path.toLowerCase();
      if (!path.endsWith('.mp4') && !path.endsWith('.mov')) {
        throw const ApiFailure('Please select an MP4 or MOV video.');
      }
      final length = await selected.length();
      if (length <= 0 || length > _limitBytes) {
        throw const ApiFailure('Video exceeds the 200 MB upload limit.');
      }
      if (mounted) {
        setState(() {
          _video = selected;
          _notice = '';
          _error = '';
        });
      }
    } on ApiFailure catch (error) {
      if (mounted) setState(() => _error = error.message);
    } catch (_) {
      if (mounted) setState(() =>
          _error = 'Could not read the selected video.');
    }
  }

  Future<void> _upload() async {
    final video = _video;
    final caption = _caption.text.trim();
    if (_busy || !_enabled || video == null) return;
    if (caption.length < 4 || caption.length > 400 ||
        !_rights || !_animalTopic) {
      setState(() =>
          _error = 'Add a caption and confirm video rights and animal content.');
      return;
    }
    final mimeType = video.path.toLowerCase().endsWith('.mov')
        ? 'video/quicktime' : 'video/mp4';
    setState(() {
      _busy = true;
      _error = '';
      _notice = 'Requesting a private upload slot…';
    });
    try {
      final ticket = await widget.api.requestVideoUploadTicket(
        caption: caption,
        rightsAttested: _rights,
        animalTopicAttested: _animalTopic,
      );
      if (!mounted) return;
      setState(() =>
          _notice = 'Uploading video securely. Keep this screen open.');
      await widget.api.uploadVideoToStream(
        uploadUrl: ticket['upload_url'] as String,
        filePath: video.path,
        mimeType: mimeType,
      );
      if (!mounted) return;
      setState(() {
        _notice = 'Video transferred. Processing and staff review are '
            'still required before anyone else can view it.';
        _video = null;
        _caption.clear();
        _rights = false;
        _animalTopic = false;
      });
      await _refreshPosts();
    } on ApiFailure catch (error) {
      if (mounted) {
        setState(() => _error = error.message +
            ' If the upload started, check your video status before retrying.');
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'Could not complete the upload. Check your connection.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void dispose() {
    _caption.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Post an animal video')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                if (_error.isNotEmpty) ...[
                  Text(_error, style: TextStyle(
                    color: Theme.of(context).colorScheme.error,
                  )),
                  const SizedBox(height: 12),
                ],
                if (_notice.isNotEmpty) ...[
                  Text(_notice),
                  const SizedBox(height: 12),
                ],
                if (!_enabled) ...[
                  const Icon(Icons.video_camera_back_outlined, size: 62),
                  const SizedBox(height: 12),
                  Text(
                    'Video posting is not available yet',
                    style: Theme.of(context).textTheme.titleLarge,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Private video processing, safety moderation and '
                    'the delivery provider must be configured before '
                    'creators can submit clips.',
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 18),
                  OutlinedButton(
                    onPressed: _loadCapabilities,
                    child: const Text('Check availability again'),
                  ),
                ] else ...[
                  const Text(
                    'Animal-only clips up to 60 seconds and 200 MB. '
                    'Only upload footage you own or are authorized to share.',
                  ),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: _busy ? null : _selectVideo,
                    icon: const Icon(Icons.video_library_outlined),
                    label: const Text('Choose video'),
                  ),
                  if (_video != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 10),
                      child: Text('Selected: ${_video!.name}'),
                    ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: _caption,
                    enabled: !_busy,
                    minLines: 2,
                    maxLines: 4,
                    maxLength: 400,
                    decoration: const InputDecoration(
                      border: OutlineInputBorder(),
                      labelText: 'Caption',
                      hintText: 'Tell viewers about this animal',
                    ),
                  ),
                  CheckboxListTile(
                    value: _rights,
                    onChanged: _busy
                        ? null : (value) => setState(() => _rights = value ?? false),
                    title: const Text(
                      'I own this video or have permission to upload it.',
                    ),
                  ),
                  CheckboxListTile(
                    value: _animalTopic,
                    onChanged: _busy ? null
                        : (value) => setState(() => _animalTopic = value ?? false),
                    title: const Text(
                      'This is animal-related content and follows community rules.',
                    ),
                  ),
                  const SizedBox(height: 12),
                  FilledButton(
                    onPressed: _busy || _video == null || !_rights || !_animalTopic
                        ? null : _upload,
                    child: Text(_busy
                        ? 'Transferring private video…'
                        : 'Submit video for review'),
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Upload confirmation is not publication. '
                    'No video appears in Home until processing and approval.',
                  ),
                  const SizedBox(height: 24),
                  Row(
                    children: [
                      Expanded(child: Text(
                        'Your recent videos',
                        style: Theme.of(context).textTheme.titleMedium,
                      )),
                      TextButton(
                        onPressed: _busy ? null : _refreshPosts,
                        child: const Text('Refresh'),
                      ),
                    ],
                  ),
                  if (_posts.isEmpty) const Text('No submitted videos yet.'),
                  for (final post in _posts)
                    ListTile(
                      title: Text(post['caption']?.toString() ?? ''),
                      subtitle: Text(
                        post['processed'] == true &&
                                post['state'] == 'pending'
                            ? 'Processed — awaiting staff review'
                            : post['state']?.toString() ?? 'Pending',
                      ),
                    ),
                ],
              ],
            ),
    );
  }
}
