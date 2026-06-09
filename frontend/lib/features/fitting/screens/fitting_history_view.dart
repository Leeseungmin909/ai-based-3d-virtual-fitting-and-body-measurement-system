import 'package:flutter/material.dart';

import '../../../core/errors/ui_error_messages.dart';
import '../models/fitting_history_item.dart';
import '../services/fitting_service.dart';
import 'fitting_result_view.dart';

/// 사용자의 피팅 요청 기록을 보여준다.
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

  void _openResult(FittingHistoryItem item) {
    final id = item.id;
    if (id == null) return;
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => FittingResultView(fittingId: id)),
    );
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
            return _MessageState(
              icon: Icons.cloud_off_outlined,
              title: '피팅 기록을 불러오지 못했습니다.',
              message: UiErrorMessages.loadFittingHistory(snapshot.error!),
              actionLabel: '다시 시도',
              onAction: _reloadHistory,
            );
          }

          final history = snapshot.data ?? const <FittingHistoryItem>[];
          if (history.isEmpty) {
            return const _MessageState(
              icon: Icons.history_outlined,
              title: '피팅 기록이 없습니다.',
              message: '옷을 선택하고 피팅 요청을 먼저 생성해 주세요.',
            );
          }

          return RefreshIndicator(
            onRefresh: () async => _reloadHistory(),
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: history.length,
              separatorBuilder: (context, separatorIndex) => const Divider(),
              itemBuilder: (context, index) {
                final item = history[index];
                final createdAt = item.createdAt ?? '날짜 없음';
                return ListTile(
                  leading: const Icon(Icons.checkroom_outlined),
                  title: Text(item.clothesName),
                  subtitle: Text('${item.status} · $createdAt'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _openResult(item),
                );
              },
            ),
          );
        },
      ),
    );
  }
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