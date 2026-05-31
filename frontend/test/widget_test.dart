import 'package:flutter_test/flutter_test.dart';

import 'package:fitting/app.dart';

void main() {
  testWidgets('app starts on login screen', (WidgetTester tester) async {
    await tester.pumpWidget(const VirtualFittingApp());

    expect(find.text('Fit360'), findsOneWidget);
    expect(find.text('Google 계정으로 계속하기'), findsOneWidget);
  });
}
