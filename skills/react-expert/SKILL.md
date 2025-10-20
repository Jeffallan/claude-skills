---
name: React Expert
description: Expert in React for building modern web applications. Use when working with React, React hooks, state management (Redux, Zustand, Context), component architecture, performance optimization, or when the user mentions React, JSX, functional components, hooks, or frontend development.
---

# React Expert

A specialized skill for building production-ready React applications with modern patterns, hooks, performance optimization, and best practices.

## Instructions

### Core Workflow

1. **Understand requirements**
   - Identify component needs and hierarchy
   - Determine state management requirements (local, Context, Redux, Zustand)
   - Understand performance requirements
   - Identify routing needs (React Router)

2. **Project structure**
   - Organize components logically
   - Separate concerns (components, hooks, utils, types)
   - Configure TypeScript for type safety
   - Set up testing infrastructure

3. **Implement features**
   - Create reusable components
   - Implement custom hooks
   - Manage state appropriately
   - Optimize performance (memo, useMemo, useCallback)
   - Handle side effects properly

4. **Testing and optimization**
   - Write tests with React Testing Library
   - Optimize bundle size
   - Implement code splitting
   - Profile and optimize performance

### React Project Structure

```
src/
├── components/
│   ├── common/              # Reusable components
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── Button.module.css
│   │   └── Input/
│   ├── features/            # Feature-specific components
│   │   ├── auth/
│   │   └── dashboard/
│   └── layout/              # Layout components
│       ├── Header.tsx
│       └── Footer.tsx
├── hooks/                   # Custom hooks
│   ├── useAuth.ts
│   ├── useApi.ts
│   └── useLocalStorage.ts
├── contexts/                # Context providers
│   └── AuthContext.tsx
├── store/                   # State management (Redux/Zustand)
│   ├── slices/
│   └── store.ts
├── services/                # API services
│   └── api.ts
├── utils/                   # Utility functions
│   └── format.ts
├── types/                   # TypeScript types
│   └── index.ts
├── pages/                   # Page components (if using routing)
│   ├── Home.tsx
│   └── Dashboard.tsx
└── App.tsx
```

### Modern Component Patterns

```typescript
// Functional component with TypeScript
import { FC, useState, useEffect, useMemo, useCallback } from 'react';

interface User {
  id: number;
  name: string;
  email: string;
}

interface UserListProps {
  initialUsers?: User[];
  onUserSelect?: (user: User) => void;
}

export const UserList: FC<UserListProps> = ({ 
  initialUsers = [],
  onUserSelect 
}) => {
  const [users, setUsers] = useState<User[]>(initialUsers);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  // Fetch users on mount
  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/users');
        const data = await response.json();
        setUsers(data);
      } catch (error) {
        console.error('Failed to fetch users:', error);
      } finally {
        setLoading(false);
      }
    };

    if (initialUsers.length === 0) {
      fetchUsers();
    }
  }, [initialUsers.length]);

  // Memoized filtered users
  const filteredUsers = useMemo(() => {
    return users.filter(user =>
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [users, searchTerm]);

  // Memoized callback
  const handleUserClick = useCallback((user: User) => {
    onUserSelect?.(user);
  }, [onUserSelect]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <input
        type="text"
        placeholder="Search users..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <ul>
        {filteredUsers.map(user => (
          <li key={user.id} onClick={() => handleUserClick(user)}>
            {user.name} - {user.email}
          </li>
        ))}
      </ul>
    </div>
  );
};
```

### Custom Hooks

```typescript
// useApi.ts - Generic API hook
import { useState, useEffect } from 'react';

interface UseApiOptions<T> {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: any;
  dependencies?: any[];
}

interface UseApiReturn<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useApi<T = any>({
  url,
  method = 'GET',
  body,
  dependencies = []
}: UseApiOptions<T>): UseApiReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, dependencies);

  return { data, loading, error, refetch: fetchData };
}

// useLocalStorage.ts
import { useState, useEffect } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue] as const;
}

// useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

### Context API for State Management

```typescript
// AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  id: number;
  name: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const userData = await response.json();
    setUser(userData);
  };

  const logout = () => {
    fetch('/api/auth/logout', { method: 'POST' });
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      logout,
      isAuthenticated: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### Performance Optimization

```typescript
import { memo, useMemo, useCallback } from 'react';

// Memoized component (only re-renders if props change)
export const ExpensiveComponent = memo(({ data }: { data: any[] }) => {
  return (
    <div>
      {data.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
});

// Parent component
export const ParentComponent = () => {
  const [count, setCount] = useState(0);
  const [users, setUsers] = useState([]);

  // Memoize expensive calculations
  const sortedUsers = useMemo(() => {
    return [...users].sort((a, b) => a.name.localeCompare(b.name));
  }, [users]);

  // Memoize callbacks to prevent child re-renders
  const handleUserAdd = useCallback((user) => {
    setUsers(prev => [...prev, user]);
  }, []);

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Count: {count}</button>
      {/* ExpensiveComponent won't re-render when count changes */}
      <ExpensiveComponent data={sortedUsers} />
    </div>
  );
};
```

### Form Handling with React Hook Form

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type FormData = z.infer<typeof schema>;

export const RegisterForm = () => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
    } catch (error) {
      console.error('Registration failed:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <input {...register('email')} placeholder="Email" />
        {errors.email && <span>{errors.email.message}</span>}
      </div>

      <div>
        <input {...register('password')} type="password" placeholder="Password" />
        {errors.password && <span>{errors.password.message}</span>}
      </div>

      <div>
        <input {...register('confirmPassword')} type="password" placeholder="Confirm Password" />
        {errors.confirmPassword && <span>{errors.confirmPassword.message}</span>}
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Register'}
      </button>
    </form>
  );
};
```

### Testing with React Testing Library

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserList } from './UserList';

describe('UserList', () => {
  const mockUsers = [
    { id: 1, name: 'John Doe', email: 'john@example.com' },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
  ];

  it('renders users', () => {
    render(<UserList initialUsers={mockUsers} />);

    expect(screen.getByText('John Doe - john@example.com')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith - jane@example.com')).toBeInTheDocument();
  });

  it('filters users by search term', async () => {
    render(<UserList initialUsers={mockUsers} />);

    const searchInput = screen.getByPlaceholderText('Search users...');
    await userEvent.type(searchInput, 'John');

    expect(screen.getByText('John Doe - john@example.com')).toBeInTheDocument();
    expect(screen.queryByText('Jane Smith - jane@example.com')).not.toBeInTheDocument();
  });

  it('calls onUserSelect when user is clicked', async () => {
    const onUserSelect = jest.fn();
    render(<UserList initialUsers={mockUsers} onUserSelect={onUserSelect} />);

    const firstUser = screen.getByText('John Doe - john@example.com');
    fireEvent.click(firstUser);

    expect(onUserSelect).toHaveBeenCalledWith(mockUsers[0]);
  });

  it('shows loading state', () => {
    render(<UserList />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
});
```

## Critical Rules

### Always Do
- Use TypeScript for type safety
- Implement proper error boundaries
- Memoize expensive calculations with useMemo
- Memoize callbacks with useCallback when passing to child components
- Use React.memo for components that render often with same props
- Keep components small and focused
- Extract reusable logic into custom hooks
- Write tests for components
- Use proper key props in lists
- Handle loading and error states

### Never Do
- Never mutate state directly
- Never use index as key in dynamic lists
- Never forget cleanup in useEffect
- Never create functions inside JSX (causes re-renders)
- Never ignore ESLint warnings
- Never use inline styles for everything (use CSS modules or styled-components)
- Never skip error boundaries
- Never ignore accessibility (use semantic HTML, ARIA labels)

## Knowledge Base

- **React Core**: Hooks, Context, Suspense, Error Boundaries
- **State Management**: Redux, Zustand, Jotai, Context API
- **Routing**: React Router, TanStack Router
- **Forms**: React Hook Form, Formik
- **Testing**: React Testing Library, Jest
- **Styling**: CSS Modules, Styled Components, Tailwind CSS
- **Performance**: Code splitting, lazy loading, memoization
- **TypeScript**: Type safety, generics, utility types

## Integration with Other Skills

- **Works with**: Fullstack Guardian, Playwright Expert, Test Master
- **Complements**: React Native Expert (mobile), Code Reviewer

## Best Practices Summary

1. **TypeScript**: Use for all components and hooks
2. **Hooks**: Prefer functional components with hooks
3. **Custom Hooks**: Extract reusable logic
4. **Performance**: Memo, useMemo, useCallback where needed
5. **Testing**: Comprehensive tests with React Testing Library
6. **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation
7. **Code Splitting**: Lazy load routes and heavy components
8. **Error Handling**: Error boundaries for graceful degradation
9. **State Management**: Choose appropriate solution for complexity
10. **Clean Code**: Small, focused, well-named components
