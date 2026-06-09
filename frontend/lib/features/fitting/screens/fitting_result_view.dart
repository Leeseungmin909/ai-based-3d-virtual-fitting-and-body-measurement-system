import 'package:flutter/material.dart';
import 'package:model_viewer_plus/model_viewer_plus.dart';

import '../../../core/config/api_config.dart';
import '../../../core/errors/ui_error_messages.dart';
import '../models/fitting_result.dart';
import '../services/fitting_service.dart';

/// 피팅 상태와 결과 이미지 또는 GLB 경로를 확인하는 화면이다.
class FittingResultView extends StatefulWidget {
  const FittingResultView({super.key, required this.fittingId});

  final int fittingId;

  @override
  State<FittingResultView> createState() => _FittingResultViewState();
}

class _FittingResultViewState extends State<FittingResultView> {
  final FittingService _fittingService = FittingService();
  late Future<FittingResult> _futureResult;

  @override
  void initState() {
    super.initState();
    _futureResult = _fittingService.fetchResult(widget.fittingId);
  }

  void _refresh() {
    setState(() {
      _futureResult = _fittingService.fetchResult(widget.fittingId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('피팅 결과')),
      body: FutureBuilder<FittingResult>(
        future: _futureResult,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return _ResultState(
              icon: Icons.cloud_off_outlined,
              title: '피팅 결과를 불러오지 못했습니다.',
              message: UiErrorMessages.loadFittingResult(snapshot.error!),
              actionLabel: '다시 조회',
              onAction: _refresh,
            );
          }

          final result = snapshot.data;
          if (result == null) {
            return _ResultState(
              icon: Icons.info_outline,
              title: '결과가 없습니다.',
              message: 'Spring 응답이 비어 있습니다.',
              actionLabel: '다시 조회',
              onAction: _refresh,
            );
          }

          if (result.isFailed) {
            return _ResultState(
              icon: Icons.error_outline,
              title: '피팅 처리 실패',
              message: result.message,
              actionLabel: '다시 조회',
              onAction: _refresh,
            );
          }

          if (!result.ready || result.isPending) {
            return _ResultState(
              icon: Icons.hourglass_empty,
              title: '피팅 처리 중',
              message: result.message,
              actionLabel: '상태 새로고침',
              onAction: _refresh,
            );
          }

          return _ReadyResult(result: result, onRefresh: _refresh);
        },
      ),
    );
  }
}

class _ReadyResult extends StatelessWidget {
  const _ReadyResult({required this.result, required this.onRefresh});

  final FittingResult result;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final avatarGlbUrl = ApiConfig.fileUrl(result.avatarGlbUrl);

    return RefreshIndicator(
      onRefresh: () async => onRefresh(),
      child: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          if (avatarGlbUrl.isNotEmpty)
            ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: SizedBox(
                height: 420,
                child: ModelViewer(
                  key: ValueKey(avatarGlbUrl),
                  src: avatarGlbUrl,
                  alt: '3D 피팅 아바타',
                  cameraControls: true,
                  autoRotate: true,
                  disableZoom: false,
                  backgroundColor: const Color(0xFFF5F5F5),
                ),
              ),
            )
          else
            const _PlaceholderBox(message: '3D 아바타가 아직 없습니다.'),
          const SizedBox(height: 24),
          _ResultInfo(label: '상태', value: result.status),
          _ResultInfo(label: 'AI Job ID', value: result.aiJobId ?? '-'),
          _ResultInfo(label: 'Avatar GLB', value: avatarGlbUrl.isEmpty ? '-' : avatarGlbUrl),
          _ResultInfo(label: 'Result JSON', value: result.resultJsonUrl ?? '-'),
        ],
      ),
    );
  }
}

class _ResultInfo extends StatelessWidget {
  const _ResultInfo({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          SelectableText(value),
        ],
      ),
    );
  }
}

class _PlaceholderBox extends StatelessWidget {
  const _PlaceholderBox({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 280,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(message, style: const TextStyle(color: Colors.grey)),
    );
  }
}

class _ResultState extends StatelessWidget {
  const _ResultState({
    required this.icon,
    required this.title,
    required this.message,
    required this.actionLabel,
    required this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String actionLabel;
  final VoidCallback onAction;

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
            const SizedBox(height: 16),
            OutlinedButton(onPressed: onAction, child: Text(actionLabel)),
          ],
        ),
      ),
    );
  }
}