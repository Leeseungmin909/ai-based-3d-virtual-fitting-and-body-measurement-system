import 'package:flutter/material.dart';

import '../../../core/config/api_config.dart';
import '../../../core/errors/ui_error_messages.dart';
import '../../fitting/screens/fitting_view.dart';
import '../models/clothes.dart';
import '../services/clothes_service.dart';

/// ???? ?? ?? ??? ???? ?? ?? ???? ???.
class ClothingSelectView extends StatefulWidget {
  const ClothingSelectView({super.key});

  @override
  State<ClothingSelectView> createState() => _ClothingSelectViewState();
}

class _ClothingSelectViewState extends State<ClothingSelectView> {
  final ClothesService _clothesService = ClothesService();
  late Future<List<Clothes>> _futureClothes;
  String _selectedCategory = 'ALL';
  final List<String> _categories = const ['ALL', 'TOP', 'BOTTOM'];

  @override
  void initState() {
    super.initState();
    _futureClothes = _clothesService.fetchClothes();
  }

  void _reloadClothes() {
    setState(() => _futureClothes = _clothesService.fetchClothes());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('옷 목록 및 피팅')),
      body: Column(
        children: [
          SizedBox(
            height: 58,
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              scrollDirection: Axis.horizontal,
              itemCount: _categories.length,
              separatorBuilder: (context, index) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final category = _categories[index];
                return ChoiceChip(
                  label: Text(category),
                  selected: _selectedCategory == category,
                  selectedColor: Colors.black,
                  backgroundColor: Colors.grey[100],
                  showCheckmark: false,
                  labelStyle: TextStyle(
                    color: _selectedCategory == category
                        ? Colors.white
                        : Colors.black87,
                    fontWeight: FontWeight.bold,
                  ),
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedCategory = category);
                  },
                );
              },
            ),
          ),
          Expanded(
            child: FutureBuilder<List<Clothes>>(
              future: _futureClothes,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  return _MessageState(
                    icon: Icons.cloud_off_outlined,
                    title: '옷 목록을 불러올 수 없습니다',
                    message: UiErrorMessages.loadClothes(snapshot.error!),
                    actionLabel: '다시 시도',
                    onAction: _reloadClothes,
                  );
                }

                final allClothes = snapshot.data ?? const <Clothes>[];
                final clothes = _selectedCategory == 'ALL'
                    ? allClothes
                    : allClothes
                          .where((item) => item.category == _selectedCategory)
                          .toList();

                if (allClothes.isEmpty) {
                  return const _MessageState(
                    icon: Icons.checkroom_outlined,
                    title: '등록된 옷이 없습니다',
                    message: '서버 DB의 clothes 테이블에 옷 데이터를 먼저 추가해 주세요.',
                  );
                }

                if (clothes.isEmpty) {
                  return _MessageState(
                    icon: Icons.filter_alt_off_outlined,
                    title: '해당 카테고리에 옷이 없습니다',
                    message: '$_selectedCategory 카테고리에 표시할 옷 데이터가 없습니다.',
                  );
                }

                return GridView.builder(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 0.56,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 20,
                  ),
                  itemCount: clothes.length,
                  itemBuilder: (context, index) =>
                      _ClothesTile(clothes: clothes[index]),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// ? ?? ?? ??? ?? ??? ????.
class _ClothesTile extends StatelessWidget {
  const _ClothesTile({required this.clothes});

  final Clothes clothes;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => FittingView(selectedClothes: clothes),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Container(
                width: double.infinity,
                color: Colors.grey[100],
                child: clothes.imageUrl.isEmpty
                    ? const Icon(Icons.image_not_supported, color: Colors.grey)
                    : Image.network(
                        ApiConfig.fileUrl(clothes.imageUrl),
                        fit: BoxFit.cover,
                        errorBuilder: (context, error, stackTrace) =>
                            const Icon(Icons.broken_image, color: Colors.grey),
                      ),
              ),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            clothes.category,
            style: const TextStyle(
              color: Colors.grey,
              fontSize: 11,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            clothes.name,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
          ),
        ],
      ),
    );
  }
}

/// ?? ??? ? ?? ??? ? ?? ????? ????.
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
            Icon(icon, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey, height: 1.4),
            ),
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
