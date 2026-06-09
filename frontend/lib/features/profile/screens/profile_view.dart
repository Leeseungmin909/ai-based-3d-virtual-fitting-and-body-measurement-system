import 'package:flutter/material.dart';

import '../../../core/config/api_config.dart';
import '../../../core/state/user_profile_store.dart';
import 'profile_edit_view.dart';

/// 현재 저장된 사용자 프로필 정보를 보여준다.
class ProfileView extends StatelessWidget {
  const ProfileView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('마이페이지')),
      body: FutureBuilder<UserProfile>(
        future: UserProfileStore().load(),
        builder: (context, snapshot) {
          final profile = snapshot.data;
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const CircleAvatar(
                radius: 48,
                backgroundColor: Colors.deepPurple,
                child: Icon(Icons.person, size: 48, color: Colors.white),
              ),
              const SizedBox(height: 24),
              ListTile(
                leading: const Icon(Icons.height),
                title: const Text('키'),
                subtitle: Text(
                  profile?.heightCm == null
                      ? '미입력'
                      : '${profile!.heightCm!.toStringAsFixed(1)} cm',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ProfileEditView()),
                ),
              ),
              const Divider(),
              ListTile(
                leading: const Icon(Icons.photo_camera_outlined),
                title: const Text('원본 사진'),
                subtitle: Text(profile?.hasSourceImage == true ? '등록됨' : '미등록'),
              ),
              if (profile?.hasSourceImage == true) ...[
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.network(
                    ApiConfig.fileUrl(profile!.sourceImageUrl),
                    height: 220,
                    fit: BoxFit.cover,
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}