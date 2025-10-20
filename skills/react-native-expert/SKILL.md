---
name: React Native Expert
description: Expert in React Native for building cross-platform mobile applications. Use when working with React Native, Expo, mobile development, native modules, navigation, or when the user mentions React Native, mobile apps, iOS, Android, Expo, or cross-platform development.
---

# React Native Expert

A specialized skill for building production-ready cross-platform mobile applications with React Native and Expo.

## Instructions

### Core Workflow

1. **Understand requirements**
   - Identify if using Expo or bare React Native
   - Determine platform-specific needs (iOS/Android)
   - Understand navigation requirements
   - Identify native module needs

2. **Project setup**
   - Choose between Expo and bare React Native
   - Set up navigation (React Navigation)
   - Configure TypeScript
   - Set up state management

3. **Implement features**
   - Create reusable components
   - Implement platform-specific code when needed
   - Handle device capabilities (camera, location, etc.)
   - Optimize performance for mobile

4. **Testing and deployment**
   - Test on both iOS and Android
   - Optimize app size and performance
   - Configure app deployment (App Store, Google Play)

### React Native Project Structure (Expo)

```
myapp/
├── app/                    # App directory (Expo Router)
│   ├── (tabs)/
│   │   ├── index.tsx
│   │   └── profile.tsx
│   ├── _layout.tsx
│   └── +not-found.tsx
├── components/
│   ├── common/
│   └── features/
├── hooks/
│   ├── useAuth.ts
│   └── useAsync.ts
├── services/
│   └── api.ts
├── constants/
│   ├── Colors.ts
│   └── Layout.ts
├── utils/
│   └── storage.ts
├── types/
│   └── index.ts
├── app.json
└── package.json
```

### Component Patterns

```typescript
import { View, Text, StyleSheet, Platform, Pressable } from 'react-native';
import { FC } from 'react';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

export const Button: FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
}) => {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.button,
        variant === 'primary' ? styles.primaryButton : styles.secondaryButton,
        pressed && styles.pressed,
        disabled && styles.disabled,
      ]}
    >
      <Text style={[
        styles.text,
        variant === 'primary' ? styles.primaryText : styles.secondaryText
      ]}>
        {title}
      </Text>
    </Pressable>
  );
};

const styles = StyleSheet.create({
  button: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
      },
      android: {
        elevation: 5,
      },
    }),
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#E5E5EA',
  },
  pressed: {
    opacity: 0.7,
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    fontSize: 16,
    fontWeight: '600',
  },
  primaryText: {
    color: '#FFFFFF',
  },
  secondaryText: {
    color: '#000000',
  },
});
```

### Navigation (React Navigation)

```typescript
// app/_layout.tsx (Expo Router)
import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="details/[id]" options={{ title: 'Details' }} />
    </Stack>
  );
}

// Or with React Navigation
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

type RootStackParamList = {
  Home: undefined;
  Profile: { userId: string };
  Details: { itemId: number };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Profile" component={ProfileScreen} />
        <Stack.Screen name="Details" component={DetailsScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

// Type-safe navigation
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useNavigation } from '@react-navigation/native';

type ProfileScreenNavigationProp = NativeStackNavigationProp<
  RootStackParamList,
  'Profile'
>;

const ProfileScreen = () => {
  const navigation = useNavigation<ProfileScreenNavigationProp>();

  const handlePress = () => {
    navigation.navigate('Details', { itemId: 42 });
  };

  return <Button title="Go to Details" onPress={handlePress} />;
};
```

### Platform-Specific Code

```typescript
import { Platform, StyleSheet } from 'react-native';

// Platform check
if (Platform.OS === 'ios') {
  // iOS-specific code
} else if (Platform.OS === 'android') {
  // Android-specific code
}

// Platform.select
const styles = StyleSheet.create({
  container: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
      },
      android: {
        elevation: 5,
      },
    }),
  },
});

// Platform-specific files
// Component.ios.tsx
// Component.android.tsx
import Component from './Component'; // Automatically picks correct file
```

### Custom Hooks for Mobile

```typescript
// hooks/useKeyboard.ts
import { useEffect, useState } from 'react';
import { Keyboard, KeyboardEvent } from 'react-native';

export const useKeyboard = () => {
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);

  useEffect(() => {
    const showSubscription = Keyboard.addListener(
      'keyboardDidShow',
      (e: KeyboardEvent) => {
        setKeyboardHeight(e.endCoordinates.height);
        setIsKeyboardVisible(true);
      }
    );

    const hideSubscription = Keyboard.addListener(
      'keyboardDidHide',
      () => {
        setKeyboardHeight(0);
        setIsKeyboardVisible(false);
      }
    );

    return () => {
      showSubscription.remove();
      hideSubscription.remove();
    };
  }, []);

  return { keyboardHeight, isKeyboardVisible };
};

// hooks/useAppState.ts
import { useEffect, useState, useRef } from 'react';
import { AppState, AppStateStatus } from 'react-native';

export const useAppState = (onChange?: (status: AppStateStatus) => void) => {
  const appState = useRef(AppState.currentState);
  const [appStateVisible, setAppStateVisible] = useState(appState.current);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', nextAppState => {
      appState.current = nextAppState;
      setAppStateVisible(nextAppState);
      onChange?.(nextAppState);
    });

    return () => subscription.remove();
  }, [onChange]);

  return appStateVisible;
};
```

### Async Storage

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

export const storage = {
  async getItem<T>(key: string): Promise<T | null> {
    try {
      const item = await AsyncStorage.getItem(key);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      console.error('Error getting item:', error);
      return null;
    }
  },

  async setItem<T>(key: string, value: T): Promise<void> {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error setting item:', error);
    }
  },

  async removeItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing item:', error);
    }
  },

  async clear(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  },
};
```

### Performance Optimization

```typescript
import { memo, useMemo, useCallback } from 'react';
import { FlatList } from 'react-native';

// Memoized list item
const ListItem = memo(({ item, onPress }: { item: any; onPress: (id: string) => void }) => {
  const handlePress = useCallback(() => {
    onPress(item.id);
  }, [item.id, onPress]);

  return (
    <Pressable onPress={handlePress}>
      <Text>{item.name}</Text>
    </Pressable>
  );
});

// Optimized FlatList
export const OptimizedList = ({ data }: { data: any[] }) => {
  const keyExtractor = useCallback((item: any) => item.id.toString(), []);

  const renderItem = useCallback(({ item }: { item: any }) => (
    <ListItem item={item} onPress={handleItemPress} />
  ), []);

  const handleItemPress = useCallback((id: string) => {
    console.log('Item pressed:', id);
  }, []);

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={keyExtractor}
      removeClippedSubviews={true}
      maxToRenderPerBatch={10}
      updateCellsBatchingPeriod={50}
      initialNumToRender={10}
      windowSize={5}
    />
  );
};
```

## Critical Rules

### Always Do
- Use FlatList/SectionList for long lists (not ScrollView)
- Implement proper key extractors
- Use memo/useCallback for list items
- Handle keyboard properly (KeyboardAvoidingView)
- Test on both iOS and Android
- Use SafeAreaView for notch support
- Implement proper loading and error states
- Handle offline scenarios
- Optimize images (use appropriate sizes)
- Use Platform-specific code when needed

### Never Do
- Never use ScrollView for long lists
- Never forget to handle Android back button
- Never ignore platform differences
- Never skip performance profiling
- Never hardcode dimensions (use Dimensions API)
- Never forget to test on real devices
- Never ignore memory leaks
- Never use inline styles extensively (hurts performance)

## Knowledge Base

- **React Native Core**: Components, APIs, Platform-specific code
- **Navigation**: React Navigation, Expo Router
- **State Management**: Redux, Zustand, Context API
- **Storage**: AsyncStorage, MMKV, SecureStore
- **Networking**: fetch, axios, React Query
- **Native Modules**: Creating custom native modules
- **Performance**: FlatList optimization, Reanimated
- **Expo**: Managed workflow, EAS Build, OTA updates

## Integration with Other Skills

- **Works with**: React Expert, Fullstack Guardian, Test Master
- **Complements**: Flutter Expert (alternative mobile framework)

## Best Practices Summary

1. **Performance**: FlatList, memo, useCallback for lists
2. **Platform**: Handle iOS/Android differences
3. **Navigation**: Type-safe navigation
4. **Storage**: AsyncStorage for persistence
5. **Images**: Optimize and cache properly
6. **Keyboard**: Handle keyboard events
7. **Testing**: Test on real devices
8. **Offline**: Handle network failures
9. **Accessibility**: Support screen readers
10. **Updates**: Use OTA updates (Expo)
