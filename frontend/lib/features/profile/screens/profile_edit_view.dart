import 'package:flutter/material.dart';

import '../../../core/errors/ui_error_messages.dart';
import '../../../core/state/user_profile_store.dart';
import '../../home/screens/home_view.dart';
import '../services/user_service.dart';

/// 피팅과 신체 치수 계산에 필요한 키를 저장하는 화면이다.
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
    if (!mounted) return;
    final height = profile.heightCm;
    if (height != null) {
      _heightController.text = height.toStringAsFixed(1);
    }
  }

  Future<void> _save() async {
    final height = double.tryParse(_heightController.text.trim());
    if (height == null || height < 100 || height > 230) {
      _showError('키는 100cm부터 230cm 사이로 입력해 주세요.');
      return;
    }

    setState(() => _isSaving = true);
    try {
      await _userService.saveHeight(height);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('신체 정보가 저장되었습니다.')),
      );
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const HomeView()),
        (route) => false,
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
  void dispose() {
    _heightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('신체 정보 입력')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          const Text(
            '키 정보',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _heightController,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              labelText: '키(cm)',
              suffixText: 'cm',
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            '입력한 키는 AI 결과 스케일 보정과 피팅 기준 생성에 사용됩니다.',
            style: TextStyle(color: Colors.grey, height: 1.4),
          ),
          const SizedBox(height: 32),
          SizedBox(
            height: 52,
            child: ElevatedButton(
              onPressed: _isSaving ? null : _save,
              child: Text(_isSaving ? '저장 중...' : '저장'),
            ),
          ),
        ],
      ),
    );
  }
}