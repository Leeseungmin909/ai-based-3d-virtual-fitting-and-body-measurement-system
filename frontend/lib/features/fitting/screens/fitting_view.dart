import 'package:flutter/material.dart';

import '../../../core/config/api_config.dart';
import '../../../core/errors/ui_error_messages.dart';
import '../../../core/state/user_profile_store.dart';
import '../../clothes/models/clothes.dart';
import '../services/fitting_service.dart';

/// 선택한 옷의 치수를 보여주고 피팅 요청을 생성한다.
class FittingView extends StatefulWidget {
  const FittingView({super.key, required this.selectedClothes});

  final Clothes selectedClothes;

  @override
  State<FittingView> createState() => _FittingViewState();
}

class _FittingViewState extends State<FittingView> {
  final FittingService _fittingService = FittingService();
  final UserProfileStore _profileStore = UserProfileStore();
  bool _isSubmitting = false;

  Future<void> _startFitting() async {
    final profile = await _profileStore.load();
    if (!mounted) return;

    if (!profile.hasAvatar) {
      _showError('먼저 3D 모델을 생성해 주세요.');
      return;
    }

    final id = widget.selectedClothes.id;
    if (id == null) {
      _showError('옷 ID가 없어 피팅 요청을 만들 수 없습니다.');
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      await _fittingService.createHistory(id);
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('피팅 요청이 저장되었습니다.')));
    } catch (e) {
      if (!mounted) return;
      _showError(UiErrorMessages.createFitting(e));
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.redAccent),
    );
  }

  @override
  Widget build(BuildContext context) {
    final clothes = widget.selectedClothes;
    return Scaffold(
      appBar: AppBar(title: const Text('옷 상세 정보')),
      body: Column(
        children: [
          Expanded(
            child: Container(
              width: double.infinity,
              color: Colors.grey[50],
              child: clothes.imageUrl.isEmpty
                  ? const Icon(
                      Icons.image_not_supported,
                      size: 80,
                      color: Colors.grey,
                    )
                  : Image.network(
                      ApiConfig.fileUrl(clothes.imageUrl),
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) => const Icon(
                        Icons.broken_image,
                        size: 80,
                        color: Colors.grey,
                      ),
                    ),
            ),
          ),
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: const BorderRadius.vertical(
                top: Radius.circular(24),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  blurRadius: 20,
                  offset: const Offset(0, -5),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  clothes.category,
                  style: const TextStyle(
                    color: Colors.deepPurple,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  clothes.name,
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 16),
                _DimensionRow(label: '총장', value: clothes.totalLengthCm),
                _DimensionRow(label: '어깨너비', value: clothes.shoulderWidthCm),
                _DimensionRow(label: '가슴너비', value: clothes.chestWidthCm),
                _DimensionRow(label: '소매길이', value: clothes.sleeveLengthCm),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: ElevatedButton(
                    onPressed: _isSubmitting ? null : _startFitting,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.black,
                      foregroundColor: Colors.white,
                    ),
                    child: Text(_isSubmitting ? '요청 중...' : '피팅 요청하기'),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// 옷 치수 한 항목을 라벨과 값 형태로 표시한다.
class _DimensionRow extends StatelessWidget {
  const _DimensionRow({required this.label, required this.value});

  final String label;
  final double? value;

  @override
  Widget build(BuildContext context) {
    if (value == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          const Icon(Icons.straighten, color: Colors.grey, size: 18),
          const SizedBox(width: 8),
          Text('$label: ${value!.toStringAsFixed(1)}cm'),
        ],
      ),
    );
  }
}
