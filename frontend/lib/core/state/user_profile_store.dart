import 'package:shared_preferences/shared_preferences.dart';

/// ???? ???? ??? ??? ???.
class UserProfile {
  const UserProfile({this.heightCm, this.hasAvatar = false});

  final double? heightCm;
  final bool hasAvatar;

  bool get needsSetup => heightCm == null;
}

/// ??? ? ??? ??? ??? ???? ????.
class UserProfileStore {
  static const _heightKey = 'user_height_cm';
  static const _hasAvatarKey = 'user_has_avatar';

  Future<UserProfile> load() async {
    final prefs = await SharedPreferences.getInstance();
    return UserProfile(
      heightCm: prefs.getDouble(_heightKey),
      hasAvatar: prefs.getBool(_hasAvatarKey) ?? false,
    );
  }

  Future<void> saveHeight(double heightCm) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble(_heightKey, heightCm);
  }

  Future<void> setAvatarReady(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_hasAvatarKey, value);
  }
}
