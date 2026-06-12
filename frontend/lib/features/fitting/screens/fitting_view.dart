import 'package:flutter/material.dart';

import '../../../core/errors/ui_error_messages.dart';
import '../../../core/state/user_profile_store.dart';
import '../../clothes/models/clothes.dart';
import '../../profile/services/user_service.dart';
import '../services/fitting_service.dart';
import 'fitting_result_view.dart';

/// 선택한 옷을 기준으로 피팅 요청을 생성하는 화면이다.
class FittingView extends StatefulWidget {
  const FittingView({super.key, required this.clothes});

  final Clothes clothes;

  @override
  State<FittingView> createState() => _FittingViewState();
}

/// 피팅 전에 필요한 사용자 정보(키·사진·체형 치수)를 한 번에 담는다.
class _FittingPrereq {
  const _FittingPrereq(this.profile, this.measurement);
  final UserProfile profile;
  final BodyMeasurement? measurement;
}

/// 착용 가능 여부 상태.
enum _WearState { possible, impossible, unknown }

class _WearResult {
  const _WearResult(this.state, this.message);
  final _WearState state;
  final String message;
}

class _FittingViewState extends State<FittingView> {
  final UserProfileStore _profileStore = UserProfileStore();
  final UserService _userService = UserService();
  final FittingService _fittingService = FittingService();

  late Future<_FittingPrereq> _prereqFuture;
  bool _isCreating = false;

  @override
  void initState() {
    super.initState();
    _prereqFuture = _loadPrereq();
  }

  Future<_FittingPrereq> _loadPrereq() async {
    final profile = await _profileStore.load();
    final measurement = await _userService.fetchMyMeasurements();
    return _FittingPrereq(profile, measurement);
  }

  /// 옷 실측 사이즈와 사용자 체형 치수를 비교해 착용 가능 여부를 판단한다.
  _WearResult _evaluateWearable(Clothes c, BodyMeasurement? m) {
    final isTop = c.category == 'TOP';
    final isBottom = c.category == 'BOTTOM';

    if (m == null || (isTop && !m.hasTopMeasurements) || (isBottom && !m.hasBottomMeasurements)) {
      return const _WearResult(_WearState.unknown, '체형을 측정한 뒤 확인할 수 있습니다.');
    }

    String? reason;
    if (isTop) {
      reason = _compare('어깨너비', c.shoulderWidthCm, m.shoulderWidthCm) ??
          _compare('가슴단면', c.chestWidthCm, m.chestWidthCm);
    } else if (isBottom) {
      reason = _compare('허리너비', c.waistWidthCm, m.waistWidthCm) ??
          _compare('엉덩이너비', c.hipWidthCm, m.hipWidthCm);
    } else {
      return const _WearResult(_WearState.unknown, '치수 정보가 없어 판단할 수 없습니다.');
    }

    if (reason != null) {
      return _WearResult(_WearState.impossible, '체형보다 작아 착용할 수 없습니다. ($reason)');
    }
    return const _WearResult(_WearState.possible, '체형에 맞아 착용할 수 있습니다.');
  }

  /// 옷 치수가 체형보다 작으면 사유 문자열을, 아니면 null을 반환한다.
  String? _compare(String label, double? clothesCm, double? bodyCm) {
    if (clothesCm != null && bodyCm != null && clothesCm < bodyCm) {
      return '$label 옷 ${clothesCm.toStringAsFixed(1)}cm < 체형 ${bodyCm.toStringAsFixed(1)}cm';
    }
    return null;
  }

  Future<void> _createFitting(UserProfile profile) async {
    if (!profile.hasHeight) {
      _showError('피팅 전에 키를 먼저 입력해 주세요.');
      return;
    }
    if (!profile.hasSourceImage) {
      _showError('피팅 전에 전신 사진 1장을 먼저 등록해 주세요.');
      return;
    }
    final clothesId = widget.clothes.id;
    if (clothesId == null) {
      _showError('옷 ID가 없어 피팅 요청을 만들 수 없습니다.');
      return;
    }

    setState(() => _isCreating = true);
    try {
      final created = await _fittingService.createHistory(clothesId: clothesId);
      if (!mounted) return;
      final fittingId = created.fittingId;
      if (fittingId == null) {
        _showError('피팅 기록 ID가 응답에 없습니다.');
        return;
      }
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => FittingResultView(fittingId: fittingId)),
      );
    } catch (e) {
      if (!mounted) return;
      _showError(UiErrorMessages.createFitting(e));
    } finally {
      if (mounted) setState(() => _isCreating = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.redAccent),
    );
  }

  @override
  Widget build(BuildContext context) {
    final clothes = widget.clothes;

    return Scaffold(
      appBar: AppBar(title: const Text('피팅 요청')),
      body: FutureBuilder<_FittingPrereq>(
        future: _prereqFuture,
        builder: (context, snapshot) {
          final prereq = snapshot.data;
          final profile = prereq?.profile ?? const UserProfile();
          final wear = _evaluateWearable(clothes, prereq?.measurement);
          final loading = snapshot.connectionState == ConnectionState.waiting;

          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Text(
                clothes.name,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                clothes.category,
                style: TextStyle(color: Colors.grey.shade700),
              ),
              const SizedBox(height: 24),
              _ChecklistTile(
                checked: profile.hasHeight,
                title: '키 입력',
                subtitle: profile.heightCm == null
                    ? '마이페이지에서 키를 입력해야 합니다.'
                    : '${profile.heightCm!.toStringAsFixed(1)} cm',
              ),
              _ChecklistTile(
                checked: profile.hasSourceImage,
                title: '전신 사진 등록',
                subtitle: profile.hasSourceImage
                    ? '사진이 등록되어 있습니다.'
                    : '사진 기반 AI 처리를 위해 전신 사진이 필요합니다.',
              ),
              _WearabilityTile(
                state: loading ? _WearState.unknown : wear.state,
                title: '착용 가능 여부',
                subtitle: loading ? '체형과 옷 치수를 확인하는 중...' : wear.message,
              ),
              const SizedBox(height: 24),
              const Text(
                '옷 치수',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              _DimensionRow(label: '총장', value: clothes.totalLengthCm),
              _DimensionRow(label: '어깨너비', value: clothes.shoulderWidthCm),
              _DimensionRow(label: '가슴너비', value: clothes.chestWidthCm),
              _DimensionRow(label: '소매길이', value: clothes.sleeveLengthCm),
              _DimensionRow(label: '허리너비', value: clothes.waistWidthCm),
              _DimensionRow(label: '엉덩이너비', value: clothes.hipWidthCm),
              _DimensionRow(label: '허벅지너비', value: clothes.thighWidthCm),
              _DimensionRow(label: '밑위', value: clothes.crotchCm),
              const SizedBox(height: 28),
              SizedBox(
                height: 52,
                child: ElevatedButton(
                  onPressed: _isCreating ? null : () => _createFitting(profile),
                  child: Text(_isCreating ? '요청 생성 중...' : '피팅 요청 생성'),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _ChecklistTile extends StatelessWidget {
  const _ChecklistTile({
    required this.checked,
    required this.title,
    required this.subtitle,
  });

  final bool checked;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(
        checked ? Icons.check_circle : Icons.error_outline,
        color: checked ? Colors.green : Colors.orange,
      ),
      title: Text(title),
      subtitle: Text(subtitle),
    );
  }
}

/// 착용 가능(초록)/불가능(빨강)/판단불가(회색)을 표시하는 타일이다.
class _WearabilityTile extends StatelessWidget {
  const _WearabilityTile({
    required this.state,
    required this.title,
    required this.subtitle,
  });

  final _WearState state;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final (icon, color) = switch (state) {
      _WearState.possible => (Icons.check_circle, Colors.green),
      _WearState.impossible => (Icons.cancel, Colors.redAccent),
      _WearState.unknown => (Icons.help_outline, Colors.grey),
    };
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(icon, color: color),
      title: Text(
        title,
        style: TextStyle(
          fontWeight: FontWeight.w600,
          color: state == _WearState.unknown ? null : color,
        ),
      ),
      subtitle: Text(subtitle),
    );
  }
}

class _DimensionRow extends StatelessWidget {
  const _DimensionRow({required this.label, required this.value});

  final String label;
  final double? value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value == null ? '-' : '${value!.toStringAsFixed(1)} cm'),
        ],
      ),
    );
  }
}
