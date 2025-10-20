---
name: Flutter Expert
description: Expert in Flutter for building cross-platform applications. Use when working with Flutter, Dart, widgets, state management (Provider, Riverpod, Bloc), Material Design, Cupertino, or when the user mentions Flutter, Dart, mobile development, or cross-platform apps.
---

# Flutter Expert

A specialized skill for building high-performance cross-platform applications with Flutter and Dart.

## Instructions

### Core Workflow

1. **Understand requirements**
   - Identify platforms (iOS, Android, Web, Desktop)
   - Determine state management approach
   - Understand UI/UX requirements
   - Identify native integrations needed

2. **Project structure**
   - Organize with feature-based architecture
   - Implement proper state management
   - Set up routing and navigation
   - Configure for multiple platforms

3. **Implement features**
   - Create reusable widgets
   - Implement responsive layouts
   - Handle platform-specific code
   - Optimize performance

4. **Testing and deployment**
   - Write widget, integration, and unit tests
   - Optimize app size and performance
   - Configure platform-specific builds

### Flutter Project Structure

```
lib/
├── main.dart
├── app.dart
├── core/
│   ├── constants/
│   ├── themes/
│   ├── utils/
│   └── extensions/
├── features/
│   ├── auth/
│   │   ├── data/
│   │   ├── domain/
│   │   ├── presentation/
│   │   └── providers/
│   └── home/
├── shared/
│   ├── widgets/
│   ├── models/
│   └── services/
└── routes/
```

### Widget Best Practices

```dart
import 'package:flutter/material.dart';

// Stateless Widget
class CustomButton extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;
  final bool isLoading;

  const CustomButton({
    Key? key,
    required this.label,
    required this.onPressed,
    this.isLoading = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: isLoading ? null : onPressed,
      child: isLoading
          ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : Text(label),
    );
  }
}

// Stateful Widget
class Counter extends StatefulWidget {
  const Counter({Key? key}) : super(key: key);

  @override
  State<Counter> createState() => _CounterState();
}

class _CounterState extends State<Counter> {
  int _count = 0;

  void _increment() {
    setState(() {
      _count++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text('Count: $_count'),
        ElevatedButton(
          onPressed: _increment,
          child: const Text('Increment'),
        ),
      ],
    );
  }
}
```

### State Management (Riverpod)

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

// Provider
final counterProvider = StateProvider<int>((ref) => 0);

// FutureProvider
final userProvider = FutureProvider<User>((ref) async {
  final response = await http.get(Uri.parse('/api/user'));
  return User.fromJson(jsonDecode(response.body));
});

// StateNotifier
class TodosNotifier extends StateNotifier<List<Todo>> {
  TodosNotifier() : super([]);

  void addTodo(Todo todo) {
    state = [...state, todo];
  }

  void removeTodo(String id) {
    state = state.where((todo) => todo.id != id).toList();
  }

  void toggleTodo(String id) {
    state = [
      for (final todo in state)
        if (todo.id == id)
          todo.copyWith(completed: !todo.completed)
        else
          todo,
    ];
  }
}

final todosProvider = StateNotifierProvider<TodosNotifier, List<Todo>>((ref) {
  return TodosNotifier();
});

// Using in Widget
class TodoList extends ConsumerWidget {
  const TodoList({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final todos = ref.watch(todosProvider);

    return ListView.builder(
      itemCount: todos.length,
      itemBuilder: (context, index) {
        final todo = todos[index];
        return ListTile(
          title: Text(todo.title),
          leading: Checkbox(
            value: todo.completed,
            onChanged: (_) {
              ref.read(todosProvider.notifier).toggleTodo(todo.id);
            },
          ),
          trailing: IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () {
              ref.read(todosProvider.notifier).removeTodo(todo.id);
            },
          ),
        );
      },
    );
  }
}
```

### Responsive Design

```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget desktop;

  const ResponsiveLayout({
    Key? key,
    required this.mobile,
    this.tablet,
    required this.desktop,
  }) : super(key: key);

  static bool isMobile(BuildContext context) =>
      MediaQuery.of(context).size.width < 650;

  static bool isTablet(BuildContext context) =>
      MediaQuery.of(context).size.width >= 650 &&
      MediaQuery.of(context).size.width < 1100;

  static bool isDesktop(BuildContext context) =>
      MediaQuery.of(context).size.width >= 1100;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 1100) {
          return desktop;
        } else if (constraints.maxWidth >= 650) {
          return tablet ?? mobile;
        } else {
          return mobile;
        }
      },
    );
  }
}
```

### Navigation (GoRouter)

```dart
import 'package:go_router/go_router.dart';

final goRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
    GoRoute(
      path: '/details/:id',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        return DetailsScreen(id: id);
      },
    ),
    GoRoute(
      path: '/profile',
      builder: (context, state) => const ProfileScreen(),
    ),
  ],
  redirect: (context, state) {
    // Add auth guard logic here
    final isLoggedIn = false; // Check auth state
    if (!isLoggedIn && state.location != '/login') {
      return '/login';
    }
    return null;
  },
);

// In main.dart
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      routerConfig: goRouter,
      theme: ThemeData(primarySwatch: Colors.blue),
    );
  }
}

// Navigate
context.go('/details/123');
context.push('/profile');
```

### API Integration

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  static const baseUrl = 'https://api.example.com';

  Future<List<User>> getUsers() async {
    final response = await http.get(Uri.parse('$baseUrl/users'));

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(response.body);
      return data.map((json) => User.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load users');
    }
  }

  Future<User> createUser(User user) async {
    final response = await http.post(
      Uri.parse('$baseUrl/users'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(user.toJson()),
    );

    if (response.statusCode == 201) {
      return User.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to create user');
    }
  }
}

// With Riverpod
final apiServiceProvider = Provider((ref) => ApiService());

final usersProvider = FutureProvider<List<User>>((ref) async {
  final apiService = ref.read(apiServiceProvider);
  return apiService.getUsers();
});
```

### Testing

```dart
// Widget Test
void main() {
  testWidgets('Counter increments', (WidgetTester tester) async {
    await tester.pumpWidget(const MaterialApp(home: Counter()));

    expect(find.text('Count: 0'), findsOneWidget);

    await tester.tap(find.text('Increment'));
    await tester.pump();

    expect(find.text('Count: 1'), findsOneWidget);
  });

  // Unit Test
  test('TodosNotifier adds todo', () {
    final notifier = TodosNotifier();
    final todo = Todo(id: '1', title: 'Test', completed: false);

    notifier.addTodo(todo);

    expect(notifier.state.length, 1);
    expect(notifier.state.first.title, 'Test');
  });

  // Integration Test
  testWidgets('Full app test', (WidgetTester tester) async {
    await tester.pumpWidget(MyApp());

    expect(find.text('Home'), findsOneWidget);

    await tester.tap(find.text('Go to Profile'));
    await tester.pumpAndSettle();

    expect(find.text('Profile'), findsOneWidget);
  });
}
```

## Critical Rules

### Always Do
- Use const constructors when possible
- Implement proper keys for lists
- Handle async operations properly
- Use BuildContext appropriately
- Implement error handling
- Test on all target platforms
- Optimize widget rebuilds
- Use proper state management
- Follow Material/Cupertino guidelines
- Profile performance

### Never Do
- Never build widgets in build method
- Never mutate state directly
- Never ignore platform differences
- Never skip const constructors
- Never create unnecessary StatefulWidgets
- Never ignore memory leaks
- Never block the UI thread
- Never hardcode sizes

## Knowledge Base

- **Flutter Core**: Widgets, State Management, Navigation
- **Dart**: Language features, async/await, null safety
- **State Management**: Provider, Riverpod, Bloc, GetX
- **UI**: Material Design, Cupertino, Custom painters
- **Platform**: iOS, Android, Web, Desktop
- **Testing**: Widget tests, Integration tests, Unit tests
- **Performance**: Profiling, optimization techniques
- **Native**: Platform channels, method channels

## Integration with Other Skills

- **Works with**: Fullstack Guardian, Test Master
- **Complements**: React Native Expert (alternative mobile)

## Best Practices Summary

1. **Widgets**: Use const, proper keys, avoid rebuilds
2. **State**: Choose appropriate state management
3. **Performance**: Profile and optimize
4. **Platform**: Handle platform differences
5. **Testing**: Comprehensive test coverage
6. **Navigation**: Type-safe routing
7. **API**: Proper error handling
8. **UI**: Follow platform guidelines
9. **Code**: Clean, maintainable, documented
10. **Build**: Optimize app size
