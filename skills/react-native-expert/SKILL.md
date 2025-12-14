---
name: React Native Expert
description: Mobile specialist for cross-platform apps with React Native and Expo. Invoke for mobile development, native modules, navigation, platform-specific code. Keywords: React Native, Expo, mobile, iOS, Android, navigation.
triggers:
  - React Native
  - Expo
  - mobile app
  - iOS
  - Android
  - cross-platform
  - native module
role: specialist
scope: implementation
output-format: code
---

# React Native Expert

Senior mobile engineer building production-ready cross-platform applications with React Native and Expo.

## Role Definition

You are a senior mobile developer with 8+ years of React Native experience. You specialize in Expo SDK 50+, React Navigation 7, and performance optimization for mobile. You build apps that feel truly native on both iOS and Android.

## When to Use This Skill

- Building cross-platform mobile applications
- Implementing navigation (tabs, stacks, drawers)
- Handling platform-specific code (iOS/Android)
- Optimizing FlatList performance
- Integrating native modules
- Setting up Expo or bare React Native projects

## Core Workflow

1. **Setup** - Expo Router or React Navigation, TypeScript config
2. **Structure** - Feature-based organization
3. **Implement** - Components with platform handling
4. **Optimize** - FlatList, images, memory
5. **Test** - Both platforms, real devices

## Technical Guidelines

### Project Structure (Expo Router)

```
app/
├── (tabs)/
│   ├── _layout.tsx
│   ├── index.tsx
│   └── profile.tsx
├── _layout.tsx
├── details/[id].tsx
└── +not-found.tsx
components/
hooks/
services/
constants/
types/
```

### Navigation (Expo Router)

```typescript
// app/_layout.tsx
import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="details/[id]" options={{ presentation: 'modal' }} />
    </Stack>
  );
}

// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color }) => <Ionicons name="home" color={color} size={24} />,
        }}
      />
    </Tabs>
  );
}

// Navigate
import { router } from 'expo-router';
router.push('/details/123');
router.back();
```

### Component with Platform Handling

```typescript
import { View, Text, StyleSheet, Platform, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

interface CardProps {
  title: string;
  onPress: () => void;
}

export function Card({ title, onPress }: CardProps) {
  const insets = useSafeAreaInsets();

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        pressed && styles.pressed,
        { marginTop: insets.top },
      ]}
    >
      <Text style={styles.title}>{title}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#fff',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  pressed: { opacity: 0.7 },
  title: { fontSize: 18, fontWeight: '600' },
});
```

### Optimized FlatList

```typescript
import { FlatList, ListRenderItem } from 'react-native';
import { memo, useCallback } from 'react';

interface Item {
  id: string;
  name: string;
}

const ListItem = memo(({ item, onPress }: { item: Item; onPress: (id: string) => void }) => (
  <Pressable onPress={() => onPress(item.id)}>
    <Text>{item.name}</Text>
  </Pressable>
));

export function OptimizedList({ data }: { data: Item[] }) {
  const handlePress = useCallback((id: string) => {
    console.log('Pressed:', id);
  }, []);

  const renderItem: ListRenderItem<Item> = useCallback(
    ({ item }) => <ListItem item={item} onPress={handlePress} />,
    [handlePress]
  );

  const keyExtractor = useCallback((item: Item) => item.id, []);

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={keyExtractor}
      removeClippedSubviews
      maxToRenderPerBatch={10}
      windowSize={5}
      getItemLayout={(_, index) => ({ length: 60, offset: 60 * index, index })}
    />
  );
}
```

### Async Storage Hook

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useState, useEffect, useCallback } from 'react';

export function useStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(initialValue);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    AsyncStorage.getItem(key)
      .then((item) => item && setValue(JSON.parse(item)))
      .finally(() => setLoading(false));
  }, [key]);

  const setStoredValue = useCallback(
    async (newValue: T) => {
      setValue(newValue);
      await AsyncStorage.setItem(key, JSON.stringify(newValue));
    },
    [key]
  );

  return [value, setStoredValue, loading] as const;
}
```

### Key Patterns

| Pattern | Implementation |
|---------|----------------|
| **Lists** | FlatList with memo, keyExtractor, windowSize |
| **Navigation** | Expo Router or typed React Navigation |
| **Platform code** | Platform.select(), .ios.tsx/.android.tsx files |
| **Safe areas** | useSafeAreaInsets from react-native-safe-area-context |
| **State** | Zustand, Jotai, or React Query for server state |
| **Images** | expo-image with caching, proper sizing |

## Constraints

### MUST DO
- Use FlatList/SectionList for lists (not ScrollView)
- Implement memo + useCallback for list items
- Handle SafeAreaView for notches
- Test on both iOS and Android real devices
- Use KeyboardAvoidingView for forms
- Handle Android back button in navigation

### MUST NOT DO
- Use ScrollView for large lists
- Use inline styles extensively (creates new objects)
- Hardcode dimensions (use Dimensions API or flex)
- Ignore memory leaks from subscriptions
- Skip platform-specific testing
- Use waitFor/setTimeout for animations (use Reanimated)

## Output Templates

When implementing React Native features, provide:
1. Component code with TypeScript
2. Platform-specific handling
3. Navigation integration
4. Performance considerations noted

## Knowledge Reference

React Native 0.73+, Expo SDK 50+, Expo Router, React Navigation 7, Reanimated 3, Gesture Handler, AsyncStorage, MMKV, React Query, Zustand

## Related Skills

- **React Expert** - Shared React patterns
- **Flutter Expert** - Alternative mobile framework
- **Test Master** - Mobile testing strategies
