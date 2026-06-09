import 'package:flutter/material.dart';

import '../../../core/errors/ui_error_messages.dart';
import '../../../core/state/user_profile_store.dart';
import '../../clothes/models/clothes.dart';
import '../services/fitting_service.dart';
import 'fitting_result_view.dart';

/// 선택한 옷을 기준으로 피팅 요청을 생성하는 화면이다.
class FittingView extends StatefulWidget {
  const FittingView({super.key, required this.clothes});

  final Clothes clothes;

  @override
  State<FittingView> createState() => _FittingViewState();
}

class _FittingViewState extends State<FittingView> {
  final UserProfileStore _profileStore = UserProfileStore();
  final FittingService _fittingService = FittingService();

  late Future<UserProfile> _profileFuture;
  bool _isCreating = false;

  @override
  void initState() {
    super.initState();
    _profileFuture = _profileStore.load();
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
      body: FutureBuilder<UserProfile>(
        future: _profileFuture,
        builder: (context, snapshot) {
          final profile = snapshot.data ?? const UserProfile();
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