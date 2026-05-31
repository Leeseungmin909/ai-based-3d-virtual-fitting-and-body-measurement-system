import 'package:flutter/material.dart';

import '../../../core/config/api_config.dart';

/// ??/?? ??? ?? Spring API ?? ??? ??? ????.
class ApiSettingsView extends StatefulWidget {
  const ApiSettingsView({super.key});

  @override
  State<ApiSettingsView> createState() => _ApiSettingsViewState();
}

class _ApiSettingsViewState extends State<ApiSettingsView> {
  late final TextEditingController _baseUrlController;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _baseUrlController = TextEditingController(text: ApiConfig.baseUrl);
  }

  @override
  void dispose() {
    _baseUrlController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() => _isSaving = true);
    try {
      await ApiConfig.updateBaseUrl(_baseUrlController.text);
      if (!mounted) return;
      _baseUrlController.text = ApiConfig.baseUrl;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('서버 주소가 저장되었습니다: ${ApiConfig.baseUrl}')),
      );
      setState(() {});
    } on FormatException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message), backgroundColor: Colors.redAccent),
      );
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  Future<void> _reset() async {
    setState(() => _isSaving = true);
    await ApiConfig.resetBaseUrl();
    if (!mounted) return;
    _baseUrlController.text = ApiConfig.baseUrl;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('기본 서버 주소로 복구했습니다: ${ApiConfig.baseUrl}')),
    );
    setState(() => _isSaving = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('서버 주소 설정')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          const Text(
            'Spring Boot API 서버 주소',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _baseUrlController,
            keyboardType: TextInputType.url,
            autocorrect: false,
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              labelText: 'Base URL',
              hintText: 'http://192.168.0.10:8080',
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '현재 적용 주소: ${ApiConfig.baseUrl}\nAndroid 에뮬레이터에서 PC의 로컬 Spring 서버는 보통 http://10.0.2.2:8080 입니다.',
            style: const TextStyle(
              fontSize: 13,
              color: Colors.grey,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            height: 52,
            child: ElevatedButton(
              onPressed: _isSaving ? null : _save,
              child: Text(_isSaving ? '저장 중...' : '저장'),
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: _isSaving ? null : _reset,
            child: const Text('기본값으로 복구'),
          ),
        ],
      ),
    );
  }
}
