import 'package:flutter/material.dart';

import '../../../core/errors/ui_error_messages.dart';
import '../../../core/state/user_profile_store.dart';
import '../../home/screens/home_view.dart';
import '../services/user_service.dart';

/// 키 정보를 수정하고 Spring API로 저장하는 화면이다.
class ProfileEditView extends StatefulWidget {
  const ProfileEditView({super.key});

  @override
  State<ProfileEditView> createState() => _ProfileEditViewState();
}

class _ProfileEditViewState extends State<ProfileEditView> {
  final TextEditingController _heightController = TextEditingController();
  final UserProfileStore _profileStore = UserProfileStore();
  final UserService _userService = UserService();
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    final profile = await _profileStore.load();
    if (!mounted || profile.heightCm == null) return;
    _heightController.text = profile.heightCm!.toStringAsFixed(1);
  }

  @override
  void dispose() {
    _heightController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final height = double.tryParse(_heightController.text.trim());
    if (height == null || height < 100 || height > 230) {
      _showError('키는 100cm에서 230cm 사이로 입력해 주세요.');
      return;
    }

    setState(() => _isSaving = true);
    try {
      await _userService.updateMyHeight(height);
      await _profileStore.saveHeight(height);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('신체 정보가 저장되었습니다.')));
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const HomeView()),
        (_) => false,
      );
    } catch (e) {
      if (!mounted) return;
      _showError(UiErrorMessages.saveHeight(e));
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.redAccent),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('프로필 설정')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '신체 정보',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _heightController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: '키(cm)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              '현재는 키를 먼저 저장하고, 이후 AI 결과 JSON이 준비되면 세부 신체 치수를 갱신합니다.',
              style: TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: _isSaving ? null : _save,
                child: Text(_isSaving ? '저장 중...' : '저장'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
