import 'package:flutter/material.dart';

import 'features/auth/screens/login_page.dart';

/// ? ?? ??? ??? ???? ????.
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
