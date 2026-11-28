# ECS Architecture and Game Patterns

## Entity Component System (ECS)

```csharp
// Component = pure data (no logic)
public struct PositionComponent
{
    public float X;
    public float Y;
    public float Z;
}

public struct VelocityComponent
{
    public float X;
    public float Y;
    public float Z;
}

public struct HealthComponent
{
    public int Current;
    public int Max;
}

public struct PlayerTag { } // Marker component

// Entity = just an ID
public struct Entity
{
    public int Id;
}

// System = logic operating on components
public class MovementSystem
{
    public void Update(float deltaTime,
        Span<PositionComponent> positions,
        Span<VelocityComponent> velocities)
    {
        for (int i = 0; i < positions.Length; i++)
        {
            positions[i].X += velocities[i].X * deltaTime;
            positions[i].Y += velocities[i].Y * deltaTime;
            positions[i].Z += velocities[i].Z * deltaTime;
        }
    }
}

// Simple ECS World
public class World
{
    private int _nextEntityId = 0;
    private Dictionary<int, PositionComponent> _positions = new();
    private Dictionary<int, VelocityComponent> _velocities = new();
    private Dictionary<int, HealthComponent> _healths = new();

    public Entity CreateEntity()
    {
        return new Entity { Id = _nextEntityId++ };
    }

    public void AddComponent<T>(Entity entity, T component)
    {
        // Store component by entity ID
    }

    public T GetComponent<T>(Entity entity)
    {
        // Retrieve component for entity
        return default;
    }
}
```

## Object Pool Pattern

```csharp
public class ObjectPool<T> where T : class, new()
{
    private readonly Stack<T> _pool = new();
    private readonly Func<T> _createFunc;
    private readonly Action<T> _resetAction;
    private readonly int _maxSize;

    public ObjectPool(Func<T> createFunc, Action<T> resetAction, int initialSize = 10, int maxSize = 100)
    {
        _createFunc = createFunc;
        _resetAction = resetAction;
        _maxSize = maxSize;

        // Pre-populate pool
        for (int i = 0; i < initialSize; i++)
        {
            _pool.Push(createFunc());
        }
    }

    public T Get()
    {
        if (_pool.Count > 0)
            return _pool.Pop();

        return _createFunc();
    }

    public void Return(T obj)
    {
        if (_pool.Count < _maxSize)
        {
            _resetAction?.Invoke(obj);
            _pool.Push(obj);
        }
    }
}

// Usage example
public class BulletManager
{
    private ObjectPool<Bullet> _bulletPool;

    public void Initialize()
    {
        _bulletPool = new ObjectPool<Bullet>(
            createFunc: () => new Bullet(),
            resetAction: (bullet) => bullet.Reset(),
            initialSize: 50,
            maxSize: 200
        );
    }

    public Bullet SpawnBullet()
    {
        Bullet bullet = _bulletPool.Get();
        bullet.Activate();
        return bullet;
    }

    public void ReturnBullet(Bullet bullet)
    {
        bullet.Deactivate();
        _bulletPool.Return(bullet);
    }
}
```

## State Machine Pattern

```csharp
public interface IState
{
    void Enter();
    void Update(float deltaTime);
    void Exit();
}

public class StateMachine
{
    private IState _currentState;

    public void ChangeState(IState newState)
    {
        _currentState?.Exit();
        _currentState = newState;
        _currentState?.Enter();
    }

    public void Update(float deltaTime)
    {
        _currentState?.Update(deltaTime);
    }
}

// Example: Enemy AI States
public class IdleState : IState
{
    private readonly EnemyController _enemy;

    public IdleState(EnemyController enemy) => _enemy = enemy;

    public void Enter()
    {
        _enemy.PlayAnimation("Idle");
    }

    public void Update(float deltaTime)
    {
        if (_enemy.PlayerInRange())
            _enemy.StateMachine.ChangeState(new ChaseState(_enemy));
    }

    public void Exit() { }
}

public class ChaseState : IState
{
    private readonly EnemyController _enemy;

    public ChaseState(EnemyController enemy) => _enemy = enemy;

    public void Enter()
    {
        _enemy.PlayAnimation("Run");
    }

    public void Update(float deltaTime)
    {
        if (!_enemy.PlayerInRange())
            _enemy.StateMachine.ChangeState(new IdleState(_enemy));
        else if (_enemy.InAttackRange())
            _enemy.StateMachine.ChangeState(new AttackState(_enemy));
        else
            _enemy.MoveTowardsPlayer(deltaTime);
    }

    public void Exit() { }
}
```

## Command Pattern (Input Handling)

```csharp
public interface ICommand
{
    void Execute();
    void Undo();
}

public class MoveCommand : ICommand
{
    private readonly Transform _transform;
    private readonly Vector3 _movement;
    private Vector3 _previousPosition;

    public MoveCommand(Transform transform, Vector3 movement)
    {
        _transform = transform;
        _movement = movement;
    }

    public void Execute()
    {
        _previousPosition = _transform.position;
        _transform.position += _movement;
    }

    public void Undo()
    {
        _transform.position = _previousPosition;
    }
}

public class InputHandler
{
    private Stack<ICommand> _commandHistory = new();

    public void ExecuteCommand(ICommand command)
    {
        command.Execute();
        _commandHistory.Push(command);
    }

    public void UndoLastCommand()
    {
        if (_commandHistory.Count > 0)
        {
            ICommand command = _commandHistory.Pop();
            command.Undo();
        }
    }
}
```

## Observer Pattern (Event System)

```csharp
public class GameEvent<T>
{
    private event Action<T> _listeners;

    public void Subscribe(Action<T> listener)
    {
        _listeners += listener;
    }

    public void Unsubscribe(Action<T> listener)
    {
        _listeners -= listener;
    }

    public void Trigger(T data)
    {
        _listeners?.Invoke(data);
    }
}

// Event hub
public static class GameEvents
{
    public static readonly GameEvent<int> OnScoreChanged = new();
    public static readonly GameEvent<float> OnHealthChanged = new();
    public static readonly GameEvent<string> OnGameOver = new();
}

// Subscriber
public class UIController
{
    private void OnEnable()
    {
        GameEvents.OnScoreChanged.Subscribe(UpdateScoreDisplay);
        GameEvents.OnHealthChanged.Subscribe(UpdateHealthBar);
    }

    private void OnDisable()
    {
        GameEvents.OnScoreChanged.Unsubscribe(UpdateScoreDisplay);
        GameEvents.OnHealthChanged.Unsubscribe(UpdateHealthBar);
    }

    private void UpdateScoreDisplay(int score)
    {
        // Update UI
    }

    private void UpdateHealthBar(float health)
    {
        // Update UI
    }
}

// Publisher
public class Player
{
    private float _health = 100f;

    public void TakeDamage(float damage)
    {
        _health -= damage;
        GameEvents.OnHealthChanged.Trigger(_health);
    }
}
```

## Service Locator Pattern

```csharp
public static class ServiceLocator
{
    private static Dictionary<Type, object> _services = new();

    public static void Register<T>(T service)
    {
        _services[typeof(T)] = service;
    }

    public static T Get<T>()
    {
        if (_services.TryGetValue(typeof(T), out object service))
            return (T)service;

        throw new Exception($"Service {typeof(T)} not found");
    }

    public static bool TryGet<T>(out T service)
    {
        if (_services.TryGetValue(typeof(T), out object obj))
        {
            service = (T)obj;
            return true;
        }

        service = default;
        return false;
    }

    public static void Clear()
    {
        _services.Clear();
    }
}

// Usage
public class GameInitializer
{
    public void Initialize()
    {
        ServiceLocator.Register<IAudioManager>(new AudioManager());
        ServiceLocator.Register<ISaveSystem>(new SaveSystem());
        ServiceLocator.Register<IInputManager>(new InputManager());
    }
}

public class Player
{
    private IAudioManager _audioManager;

    public void Start()
    {
        _audioManager = ServiceLocator.Get<IAudioManager>();
    }

    public void PlaySound(string soundName)
    {
        _audioManager.PlaySound(soundName);
    }
}
```

## Spatial Partitioning (Grid)

```csharp
public class SpatialGrid<T>
{
    private readonly Dictionary<(int, int), List<T>> _grid = new();
    private readonly float _cellSize;

    public SpatialGrid(float cellSize)
    {
        _cellSize = cellSize;
    }

    private (int, int) GetCell(Vector2 position)
    {
        int x = Mathf.FloorToInt(position.x / _cellSize);
        int y = Mathf.FloorToInt(position.y / _cellSize);
        return (x, y);
    }

    public void Insert(Vector2 position, T item)
    {
        var cell = GetCell(position);
        if (!_grid.ContainsKey(cell))
            _grid[cell] = new List<T>();

        _grid[cell].Add(item);
    }

    public List<T> Query(Vector2 position, float radius)
    {
        List<T> results = new();
        int cellRadius = Mathf.CeilToInt(radius / _cellSize);

        var centerCell = GetCell(position);

        for (int x = -cellRadius; x <= cellRadius; x++)
        {
            for (int y = -cellRadius; y <= cellRadius; y++)
            {
                var cell = (centerCell.Item1 + x, centerCell.Item2 + y);
                if (_grid.TryGetValue(cell, out List<T> items))
                    results.AddRange(items);
            }
        }

        return results;
    }

    public void Clear()
    {
        _grid.Clear();
    }
}
```

## Double Buffer Pattern (for Rendering/Physics)

```csharp
public class DoubleBuffer<T>
{
    private T[] _buffers = new T[2];
    private int _currentIndex = 0;

    public DoubleBuffer(T buffer1, T buffer2)
    {
        _buffers[0] = buffer1;
        _buffers[1] = buffer2;
    }

    public T Current => _buffers[_currentIndex];
    public T Next => _buffers[1 - _currentIndex];

    public void Swap()
    {
        _currentIndex = 1 - _currentIndex;
    }
}

// Usage for physics
public class PhysicsSimulation
{
    private DoubleBuffer<PhysicsState> _stateBuffer = new DoubleBuffer<PhysicsState>(new PhysicsState(), new PhysicsState());

    public void Update(float deltaTime)
    {
        // Read from current, write to next
        ComputeNextState(_stateBuffer.Current, _stateBuffer.Next, deltaTime);

        // Swap buffers
        _stateBuffer.Swap();
    }
}
```