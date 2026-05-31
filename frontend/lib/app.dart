import 'package:flutter/material.dart';

import 'features/auth/screens/login_page.dart';

/// 앱 공통 테마와 최초 화면을 정의한다.
class VirtualFittingApp extends StatelessWidget {
  const VirtualFittingApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fit360',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        scaffoldBackgroundColor: Colors.white,
      ),
      home: const LoginPage(),
    );
  }
}
