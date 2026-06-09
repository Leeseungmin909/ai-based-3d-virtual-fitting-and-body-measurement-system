import 'package:shared_preferences/shared_preferences.dart';

class UserProfile {
  const UserProfile({
    this.heightCm,
    this.sourceImageUrl,
    this.avatarGlbUrl,
  });

  final double? heightCm;
  final String? sourceImageUrl;
  final String? avatarGlbUrl;

  bool get hasHeight => heightCm != null;
  bool get hasSourceImage => sourceImageUrl != null && sourceImageUrl!.isNotEmpty;
  bool get hasAvatar => avatarGlbUrl != null && avatarGlbUrl!.isNotEmpty;

  UserProfile copyWith({
    double? heightCm,
    String? sourceImageUrl,
    String? avatarGlbUrl,
  }) {
    return UserProfile(
      heightCm: heightCm ?? this.heightCm,
      sourceImageUrl: sourceImageUrl ?? this.sourceImageUrl,
      avatarGlbUrl: avatarGlbUrl ?? this.avatarGlbUrl,
    );
  }
}

/// Flutter 화면 간에 필요한 최소 사용자 정보를 로컬에 캐싱한다.
class UserProfileStore {
  static const _heightKey = 'profile_height_cm';
  static const _sourceImageUrlKey = 'profile_source_image_url';
  static const _avatarGlbUrlKey = 'profile_avatar_glb_url';

  Future<UserProfile> load() async {
    final prefs = await SharedPreferences.getInstance();
    return UserProfile(
      heightCm: prefs.getDouble(_heightKey),
      sourceImageUrl: prefs.getString(_sourceImageUrlKey),
      avatarGlbUrl: prefs.getString(_avatarGlbUrlKey),
    );
  }

  Future<void> saveHeight(double heightCm) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_heightKey, heightCm);
  }

  Future<void> saveSourceImageUrl(String sourceImageUrl) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_sourceImageUrlKey, sourceImageUrl);
  }

  Future<void> saveAvatarGlbUrl(String avatarGlbUrl) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_avatarGlbUrlKey, avatarGlbUrl);
  }

  /// 계정 전환(가입/로그인/로그아웃) 시 이전 사용자 정보가 남지 않도록 비운다.
  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_heightKey);
    await prefs.remove(_sourceImageUrlKey);
    await prefs.remove(_avatarGlbUrlKey);
  }
}