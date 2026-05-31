import 'package:flutter/material.dart';

import '../../../core/services/token_storage.dart';
import '../../../core/state/user_profile_store.dart';
import '../../auth/screens/login_page.dart';
import '../../clothes/screens/clothing_select_view.dart';
import '../../fitting/screens/fitting_history_view.dart';
import '../../profile/screens/profile_edit_view.dart';
import '../../profile/screens/profile_view.dart';
import '../../scan/screens/photo_upload_view.dart';
import '../../settings/screens/api_settings_view.dart';

/// Home menu screen that routes users to the main features.
class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  final UserProfileStore _profileStore = UserProfileStore();
  final TokenStorage _tokenStorage = TokenStorage();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _showSetupIfNeeded());
  }

  Future<void> _showSetupIfNeeded() async {
    final profile = await _profileStore.load();
    if (!mounted || !profile.needsSetup) return;

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('키 입력 필요'),
        content: const Text('신체 치수 계산과 피팅 기준 생성을 위해 키를 먼저 입력해 주세요.'),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ProfileEditView()),
              );
            },
            child: const Text('입력하러 가기'),
          ),
        ],
      ),
    );
  }

  Future<void> _signOut() async {
    await _tokenStorage.clearToken();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginPage()),
      (_) => false,
    );
  }

  void _openServerSettings() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const ApiSettingsView()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text(
          'Fit360',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.dns_outlined, color: Colors.black54),
            onPressed: _openServerSettings,
          ),
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.black54),
            onPressed: _signOut,
          ),
          IconButton(
            icon: const CircleAvatar(
              radius: 15,
              backgroundColor: Colors.deepPurple,
              child: Icon(Icons.person, size: 18, color: Colors.white),
            ),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ProfileView()),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '사용할 기능을 선택해 주세요.',
              style: TextStyle(color: Colors.grey, fontSize: 16),
            ),
            const SizedBox(height: 32),
            _HomeMenuCard(
              icon: Icons.threed_rotation,
              title: '3D 모델 만들기',
              subtitle: '10초 전신 영상으로 아바타 생성 요청',
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const PhotoUploadView()),
              ),
            ),
            const SizedBox(height: 16),
            _HomeMenuCard(
              icon: Icons.checkroom,
              title: '옷 조회 및 피팅',
              subtitle: 'TOP/BOTTOM 의류를 선택해 피팅 기록 생성',
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ClothingSelectView()),
              ),
            ),
            const SizedBox(height: 16),
            _HomeMenuCard(
              icon: Icons.history,
              title: '피팅 기록',
              subtitle: '서버에 저장된 피팅 요청 기록 확인',
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const FittingHistoryView()),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HomeMenuCard extends StatelessWidget {
  const _HomeMenuCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.deepPurple.shade100),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.deepPurple.shade50,
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 34, color: Colors.deepPurple),
            ),
            const SizedBox(width: 18),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    subtitle,
                    style: const TextStyle(fontSize: 13, color: Colors.grey),
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right, color: Colors.grey),
          ],
        ),
      ),
    );
  }
}
