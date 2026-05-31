import 'package:flutter/material.dart';

import 'mesh_view.dart';

/// Temporary entry screen for video capture/upload before AI integration.
class AiScanView extends StatefulWidget {
  const AiScanView({super.key});

  @override
  State<AiScanView> createState() => _AiScanViewState();
}

class _AiScanViewState extends State<AiScanView> {
  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const MeshView()),
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'AI 분석 중...',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 40),
            SizedBox(
              width: 200,
              height: 200,
              child: CircularProgressIndicator(
                strokeWidth: 8,
                color: Colors.deepPurpleAccent,
              ),
            ),
            SizedBox(height: 40),
            Text(
              '신체 치수와 아바타 정보를 계산하고 있습니다.',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}
