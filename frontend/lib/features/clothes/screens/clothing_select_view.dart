import 'package:flutter/material.dart';

import '../../../core/config/api_config.dart';
import '../../../core/errors/ui_error_messages.dart';
import '../../fitting/screens/fitting_view.dart';
import '../models/clothes.dart';
import '../services/clothes_service.dart';

/// Spring에서 옷 목록을 불러오고 선택한 옷을 피팅 화면으로 넘긴다.
class ClothingSelectView extends StatefulWidget {
  const ClothingSelectView({super.key});

  @override
  State<ClothingSelectView> createState() => _ClothingSelectViewState();
}

class _ClothingSelectViewState extends State<ClothingSelectView> {
  final ClothesService _clothesService = ClothesService();
  late Future<List<Clothes>> _futureClothes;

  @override
  void initState() {
    super.initState();
    _futureClothes = _clothesService.fetchClothes();
  }

  void _reload() {
    setState(() => _futureClothes = _clothesService.fetchClothes());
  }

  void _openFitting(Clothes clothes) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => FittingView(clothes: clothes)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('옷 선택')),
      body: FutureBuilder<List<Clothes>>(
        future: _futureClothes,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _MessageState(
              icon: Icons.cloud_off_outlined,
              title: '옷 목록을 불러오지 못했습니다.',
              message: UiErrorMessages.loadClothes(snapshot.error!),
              actionLabel: '다시 시도',
              onAction: _reload,
            );
          }
          final clothes = snapshot.data ?? const <Clothes>[];
          if (clothes.isEmpty) {
            return const _MessageState(
              icon: Icons.checkroom_outlined,
              title: '등록된 옷이 없습니다.',
              message: 'Spring DB에 옷 데이터를 먼저 등록해 주세요.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: clothes.length,
            separatorBuilder: (context, separatorIndex) => const SizedBox(height: 12),
            itemBuilder: (context, index) => _ClothesCard(
              clothes: clothes[index],
              onTap: () => _openFitting(clothes[index]),
            ),
          );
        },
      ),
    );
  }
}

class _ClothesCard extends StatelessWidget {
  const _ClothesCard({required this.clothes, required this.onTap});

  final Clothes clothes;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final imageUrl = ApiConfig.fileUrl(clothes.imageUrl);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Row(
          children: [
            SizedBox(
              width: 108,
              height: 108,
              child: imageUrl.isEmpty
                  ? const ColoredBox(
                      color: Color(0xFFEFEFEF),
                      child: Icon(Icons.image_not_supported_outlined),
                    )
                  : Image.network(
                      imageUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) => const ColoredBox(
                        color: Color(0xFFEFEFEF),
                        child: Icon(Icons.broken_image_outlined),
                      ),
                    ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      clothes.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      clothes.category,
                      style: TextStyle(color: Colors.grey.shade700),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '가슴 ${_cm(clothes.chestWidthCm)} · 총장 ${_cm(clothes.totalLengthCm)}',
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ),
            const Padding(
              padding: EdgeInsets.only(right: 12),
              child: Icon(Icons.chevron_right),
            ),
          ],
        ),
      ),
    );
  }

  String _cm(double? value) => value == null ? '-' : '${value.toStringAsFixed(1)}cm';
}

class _MessageState extends StatelessWidget {
  const _MessageState({
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 56, color: Colors.grey),
            const SizedBox(height: 16),
            Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: 16),
              OutlinedButton(onPressed: onAction, child: Text(actionLabel!)),
            ],
          ],
        ),
      ),
    );
  }
}