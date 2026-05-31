import 'package:flutter/material.dart';

import '../../clothes/screens/clothing_select_view.dart';
import '../../home/screens/home_view.dart';

/// ?? ?? 3D ??? ??? ??? ???? ?? ?? ????.
class MeshView extends StatelessWidget {
  const MeshView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('생성된 3D 모델'),
        actions: [
          IconButton(
            icon: const Icon(Icons.home_outlined),
            onPressed: () => Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (_) => const HomeView()),
              (_) => false,
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            flex: 2,
            child: Container(
              margin: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.threed_rotation,
                      size: 100,
                      color: Colors.deepPurple,
                    ),
                    Text('3D 모델 미리보기 영역', style: TextStyle(color: Colors.grey)),
                  ],
                ),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ClothingSelectView()),
                ),
                child: const Text('옷 선택하러 가기'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
