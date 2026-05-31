import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/state/user_profile_store.dart';

/// ???? ??? ???? ?? ??? ?? ????.
class PhotoUploadView extends StatefulWidget {
  const PhotoUploadView({super.key});

  @override
  State<PhotoUploadView> createState() => _PhotoUploadViewState();
}

class _PhotoUploadViewState extends State<PhotoUploadView> {
  final ImagePicker _picker = ImagePicker();
  final UserProfileStore _profileStore = UserProfileStore();
  XFile? _selectedVideo;
  bool _isSaving = false;

  Future<void> _pickVideo() async {
    final video = await _picker.pickVideo(source: ImageSource.gallery);
    if (video == null) return;
    setState(() => _selectedVideo = video);
  }

  Future<void> _markAvatarReady() async {
    if (_selectedVideo == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('먼저 10초 전신 영상을 선택해 주세요.'),
          backgroundColor: Colors.redAccent,
        ),
      );
      return;
    }

    setState(() => _isSaving = true);
    await _profileStore.setAvatarReady(true);
    if (!mounted) return;
    setState(() => _isSaving = false);
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('테스트용 아바타 상태를 생성됨으로 변경했습니다.')));
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('3D 모델 만들기')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            GestureDetector(
              onTap: _pickVideo,
              child: Container(
                height: 230,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: _selectedVideo == null
                      ? Colors.deepPurple.shade50
                      : Colors.green.shade50,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: _selectedVideo == null
                        ? Colors.deepPurple.shade200
                        : Colors.green.shade300,
                    width: 2,
                  ),
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      _selectedVideo == null
                          ? Icons.videocam_outlined
                          : Icons.check_circle,
                      size: 58,
                      color: _selectedVideo == null
                          ? Colors.deepPurple
                          : Colors.green,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      _selectedVideo == null ? '10초 전신 영상 선택' : '영상 선택 완료',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _selectedVideo?.name ??
                          '현재 단계에서는 서버 업로드 없이 로컬 선택만 처리합니다.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: Colors.grey, fontSize: 13),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'AI 서비스 API가 확정되면 이 화면에서 영상 업로드와 job 상태 조회를 연결합니다.',
              style: TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _isSaving ? null : _markAvatarReady,
                child: Text(_isSaving ? '처리 중...' : '테스트용 생성 완료 처리'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
