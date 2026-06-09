import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/errors/ui_error_messages.dart';
import '../../home/screens/home_view.dart';
import '../../profile/services/user_service.dart';

/// AI 파이프라인에 보낼 전신 사진 1장을 선택하거나 촬영하는 화면이다.
class PhotoUploadView extends StatefulWidget {
  const PhotoUploadView({super.key});

  @override
  State<PhotoUploadView> createState() => _PhotoUploadViewState();
}

class _PhotoUploadViewState extends State<PhotoUploadView> {
  final ImagePicker _picker = ImagePicker();
  final UserService _userService = UserService();

  XFile? _selectedImage;
  Uint8List? _previewBytes;
  bool _isUploading = false;

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(
      source: source,
      imageQuality: 92,
      maxWidth: 1600,
    );
    if (picked == null) return;
    final bytes = await picked.readAsBytes();
    if (!mounted) return;
    setState(() {
      _selectedImage = picked;
      _previewBytes = bytes;
    });
  }

  Future<void> _uploadImage() async {
    final image = _selectedImage;
    if (image == null) {
      _showError('먼저 전신 사진 1장을 선택해 주세요.');
      return;
    }

    setState(() => _isUploading = true);
    try {
      await _userService.uploadSourceImage(image.path);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('전신 사진이 저장되었습니다.')),
      );
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const HomeView()),
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      _showError(UiErrorMessages.uploadSourceImage(e));
    } finally {
      if (mounted) setState(() => _isUploading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.redAccent),
    );
  }

  @override
  Widget build(BuildContext context) {
    final previewBytes = _previewBytes;

    return Scaffold(
      appBar: AppBar(title: const Text('전신 사진 등록')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          AspectRatio(
            aspectRatio: 3 / 4,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.grey.shade300),
              ),
              child: previewBytes == null
                  ? const Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.person_search, size: 56, color: Colors.grey),
                          SizedBox(height: 12),
                          Text('전신이 보이는 사진을 등록해 주세요.'),
                        ],
                      ),
                    )
                  : ClipRRect(
                      borderRadius: BorderRadius.circular(16),
                      // contain: 전신이 잘리지 않도록 전체를 비율 유지하며 표시(업로드 파일은 원본 그대로)
                      child: Image.memory(previewBytes, fit: BoxFit.contain),
                    ),
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _isUploading ? null : () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera_outlined),
                  label: const Text('촬영'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _isUploading ? null : () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('갤러리'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Text(
            '사진 기반 흐름에서는 10초 영상 대신 전신 사진 1장을 Spring 서버에 저장합니다. AI API가 확정되면 이 사진 경로를 AI 처리 요청에 사용합니다.',
            style: TextStyle(color: Colors.grey, height: 1.4),
          ),
          const SizedBox(height: 28),
          SizedBox(
            height: 52,
            child: ElevatedButton(
              onPressed: _isUploading ? null : _uploadImage,
              child: Text(_isUploading ? '업로드 중...' : '사진 업로드'),
            ),
          ),
        ],
      ),
    );
  }
}