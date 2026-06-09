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

/// 사진 기반 피팅 흐름의 시작 화면이다.
class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  final UserProfileStore _profileStore = UserProfileStore();

  Future<void> _showSetupIfNeeded() async {
    final profile = await _profileStore.load();
    if (!mounted || profile.hasHeight) return;
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('키 입력 필요'),
        content: const Text('신체 치수 계산과 피팅 기준 생성을 위해 키를 먼저 입력해 주세요.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('나중에'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ProfileEditView()),
              );
            },
            child: const Text('키 입력하기'),
          ),
        ],
      ),
    );
  }

  Future<void> _signOut() async {
    await TokenStorage().clearToken();
    await _profileStore.clear();
    if (!mounted) return;
    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(builder: (_) => const LoginPage()),
      (route) => false,
    );
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _showSetupIfNeeded());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Fit360'),
        actions: [
          IconButton(
            tooltip: '마이페이지',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ProfileView()),
            ),
            icon: const Icon(Icons.person_outline),
          ),
          IconButton(
            tooltip: '서버 설정',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ApiSettingsView()),
            ),
            icon: const Icon(Icons.dns_outlined),
          ),
          IconButton(
            tooltip: '로그아웃',
            onPressed: _signOut,
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            '사진 기반 가상 피팅',
            style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            '키와 전신 사진 1장을 등록한 뒤 옷을 선택해 피팅 결과를 확인합니다.',
            style: TextStyle(color: Colors.grey, height: 1.4),
          ),
          const SizedBox(height: 28),
          _HomeActionCard(
            icon: Icons.height,
            title: '키 입력',
            subtitle: '신체 치수와 피팅 기준 생성을 위한 키를 저장합니다.',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ProfileEditView()),
            ),
          ),
          _HomeActionCard(
            icon: Icons.photo_camera_outlined,
            title: '전신 사진 등록',
            subtitle: '사진 1장을 업로드해 AI 처리 입력으로 사용합니다.',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const PhotoUploadView()),
            ),
          ),
          _HomeActionCard(
            icon: Icons.checkroom_outlined,
            title: '옷 조회 및 피팅',
            subtitle: 'TOP/BOTTOM 옷 목록을 확인하고 피팅 요청을 생성합니다.',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ClothingSelectView()),
            ),
          ),
          _HomeActionCard(
            icon: Icons.history_outlined,
            title: '피팅 기록',
            subtitle: '생성된 피팅 요청의 상태와 결과를 확인합니다.',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const FittingHistoryView()),
            ),
          ),
        ],
      ),
    );
  }
}

class _HomeActionCard extends StatelessWidget {
  const _HomeActionCard({
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
    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      child: ListTile(
        leading: Icon(icon, color: Colors.deepPurple),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}