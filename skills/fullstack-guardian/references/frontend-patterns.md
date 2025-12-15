# Frontend Patterns

> Reference for: Fullstack Guardian
> Load when: Building UI components, optimizing frontend, real-time features, or accessibility

## TypeScript Configuration

### Strict Setup
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/components/*": ["src/components/*"],
      "@/hooks/*": ["src/hooks/*"],
      "@/utils/*": ["src/utils/*"],
      "@/types/*": ["src/types/*"]
    }
  }
}
```

## Real-time Features

### WebSocket Hook
```typescript
function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onmessage = (event) => setLastMessage(JSON.parse(event.data));

    return () => ws.close();
  }, [url]);

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, lastMessage, sendMessage };
}

// Usage
function Chat() {
  const { isConnected, lastMessage, sendMessage } = useWebSocket('ws://localhost:3000');

  return (
    <div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      <button onClick={() => sendMessage({ text: 'Hello' })}>Send</button>
    </div>
  );
}
```

### Optimistic Updates
```typescript
// React Query with optimistic update
function useUpdateTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (todo: Todo) => api.updateTodo(todo),

    // Optimistically update cache before mutation
    onMutate: async (newTodo) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['todos'] });

      // Snapshot previous value
      const previous = queryClient.getQueryData(['todos']);

      // Optimistically update
      queryClient.setQueryData(['todos'], (old: Todo[]) =>
        old.map(todo => todo.id === newTodo.id ? newTodo : todo)
      );

      return { previous };
    },

    // Rollback on error
    onError: (err, newTodo, context) => {
      queryClient.setQueryData(['todos'], context?.previous);
      toast.error('Failed to update todo');
    },

    // Refetch on success
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });
}
```

### Presence Hook
```typescript
function usePresence(roomId: string) {
  const [users, setUsers] = useState<User[]>([]);
  const { sendMessage, lastMessage } = useWebSocket(`ws://localhost:3000/presence`);

  useEffect(() => {
    sendMessage({ type: 'join', roomId });
    const interval = setInterval(() => sendMessage({ type: 'heartbeat', roomId }), 30000);
    return () => {
      sendMessage({ type: 'leave', roomId });
      clearInterval(interval);
    };
  }, [roomId, sendMessage]);

  useEffect(() => {
    if (lastMessage?.type === 'presence_update') setUsers(lastMessage.users);
  }, [lastMessage]);

  return users;
}
```

## Performance Optimization

### Code Splitting & Lazy Loading
```typescript
import { lazy, Suspense } from 'react';

// Lazy load route components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Suspense>
  );
}

// Component-level code splitting
const HeavyChart = lazy(() => import('./components/HeavyChart'));

function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<div>Loading chart...</div>}>
        <HeavyChart data={data} />
      </Suspense>
    </div>
  );
}
```

### Bundle Analysis
```javascript
// webpack.config.js
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin({ analyzerMode: 'static' })
  ]
};
```

### Lazy Load Images
```typescript
function LazyImage({ src, alt }: Props) {
  const [imgSrc, setImgSrc] = useState('/placeholder.jpg');
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setImgSrc(src);
          observer.disconnect();
        }
      },
      { rootMargin: '100px' }
    );

    if (imgRef.current) observer.observe(imgRef.current);
    return () => observer.disconnect();
  }, [src]);

  return <img ref={imgRef} src={imgSrc} alt={alt} />;
}
```

## Accessibility

### Accessible Modal
```typescript
function Modal({ isOpen, onClose, title, children }: Props) {
  const titleId = useId();

  useEffect(() => {
    if (isOpen) document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div role="dialog" aria-modal="true" aria-labelledby={titleId} onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()}>
        <h2 id={titleId}>{title}</h2>
        {children}
        <button onClick={onClose} aria-label="Close modal">×</button>
      </div>
    </div>
  );
}
```

### Keyboard Navigation
```typescript
function Dropdown({ items }: Props) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(i => (i + 1) % items.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(i => (i - 1 + items.length) % items.length);
        break;
      case 'Enter':
        selectItem(items[selectedIndex]);
        break;
    }
  };

  return <div role="combobox" onKeyDown={handleKeyDown}>{/* ... */}</div>;
}
```

### Focus Trap
```typescript
function useFocusTrap(ref: RefObject<HTMLElement>) {
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const focusable = element.querySelectorAll(
      'a[href], button:not([disabled]), textarea, input, select'
    );
    const first = focusable[0] as HTMLElement;
    const last = focusable[focusable.length - 1] as HTMLElement;

    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    element.addEventListener('keydown', handleTab);
    first?.focus();
    return () => element.removeEventListener('keydown', handleTab);
  }, [ref]);
}
```

## Testing

### Component Testing with Testing Library
```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('UserForm', () => {
  it('validates email format', async () => {
    const user = userEvent.setup();
    render(<UserForm onSubmit={jest.fn()} />);

    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 'invalid-email');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument();
  });

  it('submits valid form', async () => {
    const onSubmit = jest.fn();
    const user = userEvent.setup();
    render(<UserForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'John Doe',
        email: 'john@example.com',
      });
    });
  });
});
```

## Quick Reference

| Pattern | Use Case | Key Benefit |
|---------|----------|-------------|
| WebSocket | Real-time updates | Bidirectional communication |
| Optimistic Updates | Better UX | Instant feedback |
| Code Splitting | Large apps | Faster initial load |
| Lazy Loading | Images, routes | Reduce bundle size |
| ARIA attributes | Screen readers | Accessibility compliance |
| Focus trap | Modals | Keyboard navigation |
