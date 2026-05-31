import 'package:flutter/material.dart';

import 'app.dart';
import 'core/config/api_config.dart';

/// Flutter 앱 시작 전에 저장된 API 서버 주소를 불러온다.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiConfig.load();
  runApp(const VirtualFittingApp());
}
