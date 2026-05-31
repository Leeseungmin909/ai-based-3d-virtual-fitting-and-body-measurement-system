import 'package:flutter/material.dart';

import 'app.dart';
import 'core/config/api_config.dart';

/// Flutter ? ?? ?? ??? API baseUrl? ?? ????.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiConfig.load();
  runApp(const VirtualFittingApp());
}
