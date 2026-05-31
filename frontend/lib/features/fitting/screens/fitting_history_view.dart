import 'package:flutter/material.dart';

import '../../../core/errors/ui_error_messages.dart';
import '../models/fitting_history_item.dart';
import '../services/fitting_service.dart';

/// Spring API에서 조회한 피팅 기록을 보여준다.
class FittingHistoryView extends StatefulWidget {
  const FittingHistoryView({super.key});

  @override
  State<FittingHistoryView> createState() => _FittingHistoryViewState();
}

class _FittingHistoryViewState extends State<FittingHistoryView> {
  final FittingService _fittingService = FittingService();
  late Future<List<FittingHistoryItem>> _futureHistory;

  @override
  void initState() {
    super.initState();
    _futureHistory = _fittingService.fetchHistory();
  }

  void _reloadHistory() {
    setState(() => _futureHistory = _fittingService.fetchHistory());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('피팅 기록')),
      body: FutureBuilder<List<FittingHistoryItem>>(
        future: _futureHistory,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _HistoryMessage(
              icon: Icons.cloud_off_outlined,
              title: '피팅 기록을 불러올 수 없습니다',
              message: UiErrorMessages.loadFittingHistory(snapshot.error!),
              actionLabel: '다시 시도',
              onAction: _reloadHistory,
            );
          }

          final history = snapshot.data ?? const <FittingHistoryItem>[];
          if (history.isEmpty) {
            return const _HistoryMessage(
              icon: Icons.history_outlined,
              title: '피팅 기록이 없습니다',
              message: '옷을 선택하고 피팅 요청을 만들면 이곳에 기록됩니다.',
            );
          }

          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: history.length,
            separatorBuilder: (context, index) => const Divider(),
            itemBuilder: (context, index) {
              final item = history[index];
              return ListTile(
                leading: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.checkroom, color: Colors.deepPurple),
                ),
                title: Text(
                  item.clothesName,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: Text(item.createdAt ?? '생성 일시 없음'),
                trailing: Text(
                  item.status,
                  style: const TextStyle(
                    color: Colors.deepPurple,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}

/// 피팅 기록 화면의 빈 목록 또는 오류 상태를 보여준다.
class _HistoryMessage extends StatelessWidget {
  const _HistoryMessage({
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
