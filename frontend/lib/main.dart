import 'package:flutter/material.dart';
import 'dart:convert'; // JSON 변환용 (새로 추가)
import 'package:http/http.dart' as http; // 통신용 (새로 추가)

double? globalUserHeight; // 내 키
double? globalUserWeight; // 내 몸무게
bool globalHasAvatar = false; // 3D 아바타 생성 여부

class Clothes {
  final int? id;
  final String name;
  final String category;
  final String imageUrl;
  final double totalLength;

  Clothes({
    this.id,
    required this.name,
    required this.category,
    required this.imageUrl,
    required this.totalLength,
  });

  factory Clothes.fromJson(Map<String, dynamic> json) {
    return Clothes(
      id: json['id'],
      name: json['name'] ?? '이름 없음',
      category: json['category'] ?? '미분류',
      imageUrl: json['imageUrl'] ?? json['image_url'] ?? '',
      totalLength: (json['totalLength'] ?? json['total_length'] ?? 0.0).toDouble(),
    );
  }
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '3D Virtual Fitting',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const LoginPage(),
    );
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  bool _isLoading = false;

  // 🚀 구글 로그인 연동 (시연 영상용 쾌속 모드)
  Future<void> _signInWithGoogle() async {
    setState(() => _isLoading = true);

    try {
      // =========================================================
      // [시연용 하드코딩 데이터] 
      // 실제 구글 팝업을 띄우지 않고, 마치 구글에서 정보를 받아온 것처럼
      // 팀장님의 자바 서버로 바로 데이터를 꽂아 넣습니다.
      // =========================================================
      final String mockEmail = "capstone_tester@gmail.com";
      final String mockName = "심사위원";

      // final url = Uri.parse('http://localhost:8080/api/auth/google'); 
      final url = Uri.parse('http://10.0.2.2:8080/api/auth/google');
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {
          'email': mockEmail,
          'name': mockName, 
        },
      );

      if (response.statusCode == 200) {
        // 백엔드에서 인증 완료되면 홈 화면으로 부드럽게 이동
        if (mounted) {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const HomeView()),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('서버 에러: 상태 코드 ${response.statusCode}')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('통신 실패: 자바 서버가 켜져 있는지 확인하세요.')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24.0),
        child: Center( // 화면 정중앙 배치
          child: SingleChildScrollView(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.accessibility_new_rounded, 
                  size: 100, 
                  color: Colors.deepPurple
                ),
                const SizedBox(height: 24),
                const Text(
                  'Fit360', 
                  style: TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: Colors.deepPurple)
                ),
                const SizedBox(height: 8),
                const Text(
                  '나만의 3D 가상 피팅룸', 
                  style: TextStyle(fontSize: 16, color: Colors.grey)
                ),
                const SizedBox(height: 80), // 버튼 위 여백 확보
                
                SizedBox(
                  width: double.infinity,
                  height: 56,
                  child: OutlinedButton.icon(
                    onPressed: _isLoading ? null : _signInWithGoogle,
                    // 구글 아이콘 느낌을 내는 기본 아이콘 사용
                    icon: _isLoading 
                        ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.g_mobiledata, size: 36, color: Colors.black87),
                    label: Text(
                      _isLoading ? '로그인 처리 중...' : 'Google 계정으로 계속하기',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.black87),
                    ),
                    style: OutlinedButton.styleFrom(
                      backgroundColor: Colors.white,
                      side: const BorderSide(color: Colors.black26), // 구글 스타일의 옅은 테두리
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                ),
                
                const SizedBox(height: 30),
                const Text(
                  '로그인 시 Fit360의 이용약관 및 개인정보처리방침에 동의하게 됩니다.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// 회원가입 화면
class SignUpPage extends StatefulWidget {
  const SignUpPage({super.key});

  @override
  State<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends State<SignUpPage> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController = TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('회원가입')),
      body: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24.0),
        child: SingleChildScrollView(
          child: Column(
            children: [
              const SizedBox(height: 40),
              const Text(
                '새 계정 만들기',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.deepPurple),
              ),
              const SizedBox(height: 30),
              TextField(
                controller: _nameController,
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.person_outline),
                  labelText: '이름',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _emailController,
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.email_outlined),
                  labelText: '이메일 주소',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordController,
                obscureText: true,
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.lock_outline),
                  labelText: '비밀번호',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _confirmPasswordController,
                obscureText: true,
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.lock_reset_outlined),
                  labelText: '비밀번호 확인',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
              const SizedBox(height: 30),
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  onPressed: () {
                    // 가입 완료 후 서비스 안내(HomeView)로 이동
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (context) => const HomeView()),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.deepPurple,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: const Text('가입하기', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class HomeView extends StatefulWidget {
  const HomeView({super.key});

  @override
  State<HomeView> createState() => _HomeViewState();
}

class _HomeViewState extends State<HomeView> {
  @override
  void initState() {
    super.initState();
    // 💡 요구사항 4: 화면이 렌더링된 직후 키/몸무게가 없으면 팝업 띄우기
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (globalUserHeight == null || globalUserWeight == null) {
        _showSetupDialog();
      }
    });
  }

  void _showSetupDialog() {
    showDialog(
      context: context,
      barrierDismissible: false, // 바깥을 눌러도 안 꺼지게 강제
      builder: (context) => AlertDialog(
        title: const Text('신체 정보 입력 필요', style: TextStyle(fontWeight: FontWeight.bold)),
        content: const Text('정확한 3D 가상 피팅을 위해\n키와 몸무게를 먼저 설정해주세요.'),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context); // 팝업 닫기
              Navigator.push(context, MaterialPageRoute(builder: (context) => const ProfileEditView())); // 수정 화면으로 이동
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.deepPurple, foregroundColor: Colors.white),
            child: const Text('입력하러 가기'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text('가상피팅 시뮬레이션', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
        centerTitle: false,
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.black54),
            onPressed: () {}, // 로그아웃 로직 생략
          ),
          IconButton(
            icon: const CircleAvatar(radius: 15, backgroundColor: Colors.deepPurple, child: Icon(Icons.person, size: 18, color: Colors.white)),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const ProfileView())),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('반가워요, 홍길동님! 👋', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('원하시는 기능을 선택해주세요.', style: TextStyle(color: Colors.grey, fontSize: 16)),
            const SizedBox(height: 40),
            
            GestureDetector(
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const PhotoUploadView())),
              child: _buildMenuCard(icon: Icons.threed_rotation, title: '3D 메쉬모델 만들기', subtitle: '내 체형과 똑같은 3D 아바타 생성'),
            ),
            const SizedBox(height: 20),
            GestureDetector(
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const ClothingSelectView())),
              child: _buildMenuCard(icon: Icons.checkroom, title: '옷 조회 및 피팅', subtitle: 'DB에 등록된 옷을 둘러보고 입혀보기'),
            ),
            const SizedBox(height: 20),
            // 💡 요구사항 1: 피팅 히스토리 전용 화면으로 직접 이동
            GestureDetector(
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (context) => const FittingHistoryView())),
              child: _buildMenuCard(icon: Icons.history, title: '피팅 히스토리', subtitle: '과거에 진행했던 가상 피팅 결과 모아보기'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuCard({required IconData icon, required String title, required String subtitle}) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20), border: Border.all(color: Colors.deepPurple.shade100)),
      child: Row(
        children: [
          Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: Colors.deepPurple.shade50, shape: BoxShape.circle), child: Icon(icon, size: 40, color: Colors.deepPurple)),
          const SizedBox(width: 20),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)), const SizedBox(height: 6), Text(subtitle, style: const TextStyle(fontSize: 13, color: Colors.grey))])),
          const Icon(Icons.chevron_right, color: Colors.grey),
        ],
      ),
    );
  }
}

// ==========================================
// 💡 1. 프로필(키, 몸무게) 수정 화면 클래스 추가
// ==========================================
class ProfileEditView extends StatefulWidget {
  const ProfileEditView({super.key});

  @override
  State<ProfileEditView> createState() => _ProfileEditViewState();
}

class _ProfileEditViewState extends State<ProfileEditView> {
  final TextEditingController _heightController = TextEditingController();
  final TextEditingController _weightController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // 기존에 저장된 전역 변수 값이 있으면 텍스트 칸에 미리 채워줍니다.
    if (globalUserHeight != null) _heightController.text = globalUserHeight.toString();
    if (globalUserWeight != null) _weightController.text = globalUserWeight.toString();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('프로필 수정', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('기본 정보', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            TextField(
              decoration: const InputDecoration(labelText: '이름', border: OutlineInputBorder()),
              controller: TextEditingController(text: '이승민'), 
            ),
            const SizedBox(height: 12),
            // 💡 이메일은 변경 불가능하도록 회색 처리(enabled: false)
            TextField(
              enabled: false, 
              decoration: const InputDecoration(
                labelText: '이메일 (수정 불가)', 
                border: OutlineInputBorder(),
                filled: true,
                fillColor: Color(0xFFF5F5F5),
              ),
              controller: TextEditingController(text: 'seungmin@example.com'),
            ),
            const SizedBox(height: 32),
            const Text('신체 정보', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            TextField(
              controller: _heightController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: '키 (cm)', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _weightController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: '몸무게 (kg)', border: OutlineInputBorder()),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton(
                onPressed: () {
                  // 💡 입력된 키와 몸무게를 전역 변수에 저장!
                  setState(() {
                    globalUserHeight = double.tryParse(_heightController.text);
                    globalUserWeight = double.tryParse(_weightController.text);
                  });
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('정보가 저장되었습니다.')));
                  
                  // 저장 후 깔끔하게 홈 화면으로 돌려보냅니다.
                  Navigator.pushAndRemoveUntil(
                    context,
                    MaterialPageRoute(builder: (context) => const HomeView()),
                    (route) => false,
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.deepPurple, 
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text('저장 완료', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ),
            )
          ],
        ),
      ),
    );
  }
}

class ProfileView extends StatelessWidget {
  const ProfileView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('마이페이지'),
        // 💡 요구사항 2: actions 배열을 비워서 연필(수정) 아이콘 삭제
        actions: [], 
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const CircleAvatar(radius: 50, backgroundColor: Colors.deepPurple, child: Icon(Icons.person, size: 50, color: Colors.white)),
          const SizedBox(height: 20),
          const Text('홍길동', textAlign: TextAlign.center, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 40),
          
          // 💡 요구사항 3: 설정 버튼 이름 변경 및 라우팅 추가
          ListTile(
            leading: const Icon(Icons.accessibility_new),
            title: const Text('키, 몸무게 수정', style: TextStyle(fontSize: 18)),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.push(context, MaterialPageRoute(builder: (context) => const ProfileEditView()));
            },
          ),
          const Divider(),
        ],
      ),
    );
  }
}

/// 8. 프로필 수정 화면
class EditProfileView extends StatefulWidget {
  const EditProfileView({super.key});

  @override
  State<EditProfileView> createState() => _EditProfileViewState();
}

class _EditProfileViewState extends State<EditProfileView> {
  final _nameController = TextEditingController(text: '홍길동');
  final _emailController = TextEditingController(text: 'hong@example.com');
  final _heightController = TextEditingController(text: '175');
  final _weightController = TextEditingController(text: '70');

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _heightController.dispose();
    _weightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('프로필 수정'),
        actions: [
          IconButton(
            icon: const Icon(Icons.home_outlined),
            onPressed: () => Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (context) => const HomeView()),
              (route) => false,
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('기본 정보', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(labelText: '이름', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(labelText: '이메일', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 32),
            const Text('신체 정보', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            TextField(
              controller: _heightController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: '키 (cm)', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _weightController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: '몸무게 (kg)', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 40),
            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.deepPurple, foregroundColor: Colors.white),
                child: const Text('저장 완료'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 전역 피팅 히스토리 데이터 (데모용)
final List<Map<String, String>> globalHistoryItems = [
  {'name': '베이직 옥스포드 셔츠 (L)', 'date': '2023-10-24', 'status': '적당함'},
  {'name': '슬림핏 데님 팬츠 (M)', 'date': '2023-10-20', 'status': '약간 큼'},
  {'name': '오버사이즈 후드티 (XL)', 'date': '2023-10-15', 'status': '적당함'},
];

/// 9. 피팅 히스토리 화면
class FittingHistoryView extends StatelessWidget {
  const FittingHistoryView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('피팅 히스토리'),
        actions: [
          IconButton(
            icon: const Icon(Icons.home_outlined),
            onPressed: () => Navigator.pushAndRemoveUntil(
              context,
              MaterialPageRoute(builder: (context) => const HomeView()),
              (route) => false,
            ),
          ),
        ],
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: globalHistoryItems.length,
        separatorBuilder: (context, index) => const Divider(),
        itemBuilder: (context, index) {
          final item = globalHistoryItems[index];
          return ListTile(
            leading: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: Colors.grey[200], borderRadius: BorderRadius.circular(8)),
              child: const Icon(Icons.checkroom, color: Colors.deepPurple),
            ),
            title: Text(item['name']!, style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text('피팅 날짜: ${item['date']}'),
            trailing: Text(item['status']!,
                style: TextStyle(
                    color: item['status'] == '적당함' ? Colors.green : Colors.orange,
                    fontWeight: FontWeight.bold)),
          );
        },
      ),
    );
  }
}

class PhotoUploadView extends StatelessWidget {
  const PhotoUploadView({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('3D 메쉬모델 만들기')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 250,
              width: double.infinity,
              decoration: BoxDecoration(color: Colors.deepPurple.shade50, borderRadius: BorderRadius.circular(16)),
              child: const Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.videocam_outlined, size: 60, color: Colors.deepPurple),
                  SizedBox(height: 16),
                  Text('10초 전신 영상을 촬영/업로드하세요', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ],
              ),
            ),
            const SizedBox(height: 30),
            
            // 💡 요구사항 6: 입력칸 삭제하고 현재 설정된 정보만 보여주기
            const Text('적용될 신체 정보 (설정 기준)', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey)),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(12)),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  Text('키: ${globalUserHeight ?? "미입력"} cm', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                  Text('몸무게: ${globalUserWeight ?? "미입력"} kg', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
            
            const Spacer(),
            SizedBox(
              width: double.infinity,
              height: 55,
              child: ElevatedButton(
                onPressed: () {
                  // 💡 영상 업로드 완료 시 상태를 '아바타 있음'으로 변경!
                  globalHasAvatar = true; 
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('3D 아바타가 성공적으로 생성되었습니다!')));
                  Navigator.pop(context); // 홈으로 돌아가기
                },
                style: ElevatedButton.styleFrom(backgroundColor: Colors.deepPurple, foregroundColor: Colors.white),
                child: const Text('3D 모델 생성 시작', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// 3. AI 스캔: 실시간 신체 특징점 추출 및 측정 진행 상태 표시
class AiScanView extends StatefulWidget {
  const AiScanView({super.key});

  @override
  State<AiScanView> createState() => _AiScanViewState();
}

class _AiScanViewState extends State<AiScanView> {
  @override
  void initState() {
    super.initState();
    // 3초 후 다음 화면으로 자동 이동 (데모용)
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        Navigator.push(context, MaterialPageRoute(builder: (context) => const MeshView()));
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('AI 신체 스캔 중...', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 40),
            Stack(
              alignment: Alignment.center,
              children: [
                const SizedBox(width: 200, height: 200, child: CircularProgressIndicator(strokeWidth: 8, color: Colors.deepPurpleAccent)),
                Icon(Icons.person_search, size: 80, color: Colors.white.withOpacity(0.8)),
              ],
            ),
            const SizedBox(height: 40),
            const Text('어깨, 허리, 골반 위치 분석 중...', style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}

/// 4. 3D 메쉬: 생성된 3D 신체 모델 확인 및 측정값 검토
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
              MaterialPageRoute(builder: (context) => const HomeView()),
              (route) => false,
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
              decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(20)),
              child: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.threed_rotation, size: 100, color: Colors.deepPurple),
                    Text('3D 신체 모델 (360도 회전 가능)', style: TextStyle(color: Colors.grey)),
                  ],
                ),
              ),
            ),
          ),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('추정 신체 치수', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const Divider(),
                  _buildMeasureRow('어깨 너비', '44cm'),
                  _buildMeasureRow('가슴 둘레', '98cm'),
                  _buildMeasureRow('허리 둘레', '82cm'),
                  const Spacer(),
                  SizedBox(
                    width: double.infinity,
                    height: 55,
                    child: ElevatedButton(
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => const ClothingSelectView()),
                      ),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.deepPurple, foregroundColor: Colors.white),
                      child: const Text('의류 선택하러 가기'),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMeasureRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [Text(label), Text(value, style: const TextStyle(fontWeight: FontWeight.bold))],
      ),
    );
  }
}

/// 5. 옷 조회 및 피팅: 쇼핑몰 스타일의 깔끔한 카탈로그 화면
class ClothingSelectView extends StatefulWidget {
  const ClothingSelectView({super.key});

  @override
  State<ClothingSelectView> createState() => _ClothingSelectViewState();
}

class _ClothingSelectViewState extends State<ClothingSelectView> {
  late Future<List<Clothes>> futureClothes;
  String _selectedCategory = 'ALL'; 
  final List<String> _categories = ['ALL', 'TOP', 'BOTTOM', 'OUTER'];

  @override
  void initState() {
    super.initState();
    futureClothes = fetchClothes();
  }

  Future<List<Clothes>> fetchClothes() async {
    final String apiUrl = 'http://10.0.2.2:8080/api/clothes';
    // final String apiUrl = 'http://localhost:8080/api/clothes'; 
    try {
      final response = await http.get(Uri.parse(apiUrl));
      if (response.statusCode == 200) {
        List<dynamic> jsonResponse = json.decode(utf8.decode(response.bodyBytes));
        return jsonResponse.map((data) => Clothes.fromJson(data)).toList();
      } else {
        throw Exception('서버 응답 오류: 상태 코드 ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('의류 데이터를 불러오는 데 실패했습니다: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white, // 배경을 흰색으로 깔끔하게
      appBar: AppBar(
        title: const Text('옷 조회 및 피팅', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        scrolledUnderElevation: 0,
      ),
      body: Column(
        children: [
          // 카테고리 탭
          Container(
            height: 60,
            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _categories.length,
              separatorBuilder: (context, index) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final category = _categories[index];
                return ChoiceChip(
                  label: Text(category),
                  selected: _selectedCategory == category,
                  selectedColor: Colors.black, // 무신사 스타일 (블랙/화이트)
                  backgroundColor: Colors.grey[100],
                  showCheckmark: false,
                  labelStyle: TextStyle(
                    color: _selectedCategory == category ? Colors.white : Colors.black87,
                    fontWeight: FontWeight.bold,
                  ),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedCategory = category);
                  },
                );
              },
            ),
          ),
          
          // 쇼핑몰 스타일 옷 목록 그리드
          Expanded(
            child: FutureBuilder<List<Clothes>>(
              future: futureClothes,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator(color: Colors.black));
                } else if (snapshot.hasError) {
                  return Center(child: Text('에러 발생\n${snapshot.error}', textAlign: TextAlign.center));
                } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                  return const Center(child: Text('등록된 옷이 없습니다. DB를 확인해주세요.'));
                }

                List<Clothes> allClothes = snapshot.data!;
                List<Clothes> displayedClothes = _selectedCategory == 'ALL'
                    ? allClothes
                    : allClothes.where((c) => c.category == _selectedCategory).toList();

                if (displayedClothes.isEmpty) {
                  return Center(child: Text('$_selectedCategory 카테고리에 등록된 옷이 없습니다.'));
                }

                return GridView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 0.55, // 이미지가 길게 보이도록 비율 조정
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 24, // 위아래 간격을 넓혀서 답답하지 않게
                  ),
                  itemCount: displayedClothes.length,
                  itemBuilder: (context, index) {
                    final clothes = displayedClothes[index];

                    return GestureDetector(
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => FittingView(selectedClothes: clothes)),
                      ),
                      // Card 위젯을 빼고 Column으로 직접 구성하여 깔끔한 UI 완성
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: Container(
                                width: double.infinity,
                                color: Colors.grey[100],
                                child: Image.network(
                                  clothes.imageUrl,
                                  fit: BoxFit.cover,
                                  errorBuilder: (context, error, stackTrace) => 
                                      const Center(child: Icon(Icons.broken_image, color: Colors.grey)),
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            clothes.category,
                            style: const TextStyle(color: Colors.grey, fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            clothes.name,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14, height: 1.2),
                          ),
                        ],
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

/// 6. 옷 상세 및 가상 피팅 시뮬레이션 진입 화면
class FittingView extends StatefulWidget {
  final Clothes selectedClothes;

  const FittingView({super.key, required this.selectedClothes});

  @override
  State<FittingView> createState() => _FittingViewState();
}

class _FittingViewState extends State<FittingView> {

  // 💡 가상 피팅 시작 로직 (예외 처리 포함 완료!)
  void _startVirtualFitting() {
    // 1. 아바타가 생성되지 않았을 경우 (예외 처리)
    if (globalHasAvatar == false) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('⚠️ 먼저 3D 메쉬모델(아바타)을 생성해야 피팅이 가능합니다.'),
          backgroundColor: Colors.redAccent,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return; // 함수를 여기서 종료하여 피팅 진행을 막습니다.
    }

    // 2. 아바타가 있을 경우 (정상 진행)
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('생성된 3D 모델에 가상 피팅을 시작합니다...'), 
        behavior: SnackBarBehavior.floating,
        backgroundColor: Colors.deepPurple,
      ),
    );
    // 추후 여기에 파이썬(AI) 서버로 피팅 요청을 보내는 코드가 들어갑니다.
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text('옷 상세 정보', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        scrolledUnderElevation: 0,
      ),
      body: Column(
        children: [
          // 큼직하고 시원한 옷 이미지 영역
          Expanded(
            child: Container(
              width: double.infinity,
              color: Colors.grey[50],
              child: Image.network(
                widget.selectedClothes.imageUrl,
                fit: BoxFit.contain,
              ),
            ),
          ),
          
          // 하단 정보 및 피팅 버튼 패널
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 20, offset: const Offset(0, -5))],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.selectedClothes.category, 
                  style: const TextStyle(color: Colors.deepPurple, fontWeight: FontWeight.bold, fontSize: 13)
                ),
                const SizedBox(height: 8),
                Text(
                  widget.selectedClothes.name, 
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, height: 1.3)
                ),
                const SizedBox(height: 16),
                const Divider(),
                const SizedBox(height: 16),
                
                // 옷 실측 정보 표시
                Row(
                  children: [
                    const Icon(Icons.straighten, color: Colors.grey, size: 20),
                    const SizedBox(width: 8),
                    Text('총장: ${widget.selectedClothes.totalLength}cm', style: const TextStyle(fontSize: 16, color: Colors.black87)),
                  ],
                ),
                
                const SizedBox(height: 32),
                
                // 핵심 액션 버튼: 가상 피팅하기
                SizedBox(
                  width: double.infinity,
                  height: 55,
                  child: ElevatedButton(
                    // 버튼을 누르면 위에서 작성한 _startVirtualFitting 함수가 실행됩니다!
                    onPressed: _startVirtualFitting, 
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.black,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text('가상 피팅하기', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  ),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}