# Unity Development Patterns

## MonoBehaviour Best Practices

```csharp
using UnityEngine;
using System.Collections.Generic;

public class EnemyController : MonoBehaviour
{
    // Serialize private fields for Inspector
    [SerializeField] private float _moveSpeed = 5f;
    [SerializeField] private Transform _target;

    // Cache component references
    private Rigidbody _rb;
    private Animator _animator;

    private void Awake()
    {
        // Cache components in Awake
        _rb = GetComponent<Rigidbody>();
        _animator = GetComponent<Animator>();
    }

    private void Start()
    {
        // Initialize after all Awake calls complete
        if (_target == null)
            _target = GameObject.FindGameObjectWithTag("Player").transform;
    }

    private void FixedUpdate()
    {
        // Physics calculations in FixedUpdate
        Vector3 direction = (_target.position - transform.position).normalized;
        _rb.MovePosition(transform.position + direction * _moveSpeed * Time.fixedDeltaTime);
    }

    private void OnDisable()
    {
        // Clean up when disabled
        StopAllCoroutines();
    }
}
```

## ScriptableObjects for Data

```csharp
[CreateAssetMenu(fileName = "WeaponData", menuName = "Game/Weapon")]
public class WeaponData : ScriptableObject
{
    public string weaponName;
    public int damage;
    public float fireRate;
    public GameObject projectilePrefab;
    public AudioClip fireSound;

    // Methods can contain logic
    public float GetDamageMultiplier(float distance)
    {
        return Mathf.Max(0.5f, 1f - (distance / 100f));
    }
}

// Usage in MonoBehaviour
public class Weapon : MonoBehaviour
{
    [SerializeField] private WeaponData _weaponData;
    private float _nextFireTime;

    public void Fire()
    {
        if (Time.time < _nextFireTime) return;

        // Use data from ScriptableObject
        Instantiate(_weaponData.projectilePrefab, transform.position, transform.rotation);
        _nextFireTime = Time.time + 1f / _weaponData.fireRate;
    }
}
```

## Object Pooling Pattern

Prefer Unity's built-in `UnityEngine.Pool.ObjectPool<T>` (Unity 2021.1+), which adds a double-release check, a size cap and a destroy callback; the hand-rolled pool below shows the mechanics.

```csharp
public class ObjectPool : MonoBehaviour
{
    [SerializeField] private GameObject _prefab;
    [SerializeField] private int _poolSize = 20;

    private Queue<GameObject> _pool = new Queue<GameObject>();

    private void Start()
    {
        // Pre-instantiate objects
        for (int i = 0; i < _poolSize; i++)
        {
            GameObject obj = Instantiate(_prefab);
            obj.SetActive(false);
            _pool.Enqueue(obj);
        }
    }

    public GameObject Get()
    {
        if (_pool.Count > 0)
        {
            GameObject obj = _pool.Dequeue();
            obj.SetActive(true);
            return obj;
        }

        // Expand pool if needed
        return Instantiate(_prefab);
    }

    public void Return(GameObject obj)
    {
        obj.SetActive(false);
        _pool.Enqueue(obj);
    }
}

// Pooled object example
public class Bullet : MonoBehaviour
{
    private ObjectPool _pool;

    public void Initialize(ObjectPool pool)
    {
        _pool = pool;
    }

    private void OnCollisionEnter(Collision collision)
    {
        // Return to pool instead of destroying
        _pool.Return(gameObject);
    }
}
```

## Event System Pattern

```csharp
using System;
using UnityEngine.Events;

// Event definition
[Serializable]
public class HealthChangedEvent : UnityEvent<int, int> { } // current, max

public class Health : MonoBehaviour
{
    [SerializeField] private int _maxHealth = 100;
    private int _currentHealth;

    // UnityEvent visible in Inspector
    public HealthChangedEvent onHealthChanged;
    public UnityEvent onDeath;

    private void Start()
    {
        _currentHealth = _maxHealth;
        onHealthChanged?.Invoke(_currentHealth, _maxHealth);
    }

    public void TakeDamage(int damage)
    {
        _currentHealth = Mathf.Max(0, _currentHealth - damage);
        onHealthChanged?.Invoke(_currentHealth, _maxHealth);

        if (_currentHealth <= 0)
            onDeath?.Invoke();
    }
}

// C# event alternative for performance
public static class GameEvents
{
    public static event Action<int> OnScoreChanged;
    public static event Action<string> OnGameOver;

    public static void TriggerScoreChanged(int score) => OnScoreChanged?.Invoke(score);
    public static void TriggerGameOver(string reason) => OnGameOver?.Invoke(reason);
}
```

## Coroutines Best Practices

```csharp
using System.Collections;

public class TimedAbility : MonoBehaviour
{
    // Cache WaitForSeconds to avoid GC
    private WaitForSeconds _cooldownWait = new WaitForSeconds(5f);
    private Coroutine _currentAbility;

    public void ActivateAbility()
    {
        // Stop previous coroutine if running
        if (_currentAbility != null)
            StopCoroutine(_currentAbility);

        _currentAbility = StartCoroutine(AbilityCoroutine());
    }

    private IEnumerator AbilityCoroutine()
    {
        // Activate ability
        Debug.Log("Ability activated");

        // Wait for duration
        yield return _cooldownWait;

        // Cooldown complete
        Debug.Log("Ability ready");
        _currentAbility = null;
    }

    // Animation-based coroutine
    private IEnumerator LerpPosition(Vector3 target, float duration)
    {
        Vector3 start = transform.position;
        float elapsed = 0f;

        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            float t = elapsed / duration;
            transform.position = Vector3.Lerp(start, target, t);
            yield return null; // Wait one frame
        }

        transform.position = target; // Ensure exact final position
    }
}
```

## Singleton Pattern (Use Sparingly)

```csharp
public class GameManager : MonoBehaviour
{
    private static GameManager _instance;
    public static GameManager Instance => _instance;

    private void Awake()
    {
        if (_instance != null && _instance != this)
        {
            Destroy(gameObject);
            return;
        }

        _instance = this;
        DontDestroyOnLoad(gameObject);
    }
}
```

## Performance Tips

- Cache `GetComponent<T>()` calls in Awake/Start
- Use `CompareTag()` instead of `tag == "TagName"`
- Use object pooling for frequently instantiated objects
- Avoid `Camera.main` in Update (cache the reference)
- Use `FixedUpdate` for physics, `Update` for input/logic
- Disable components instead of GameObjects when possible
- Use `StringBuilder` for string concatenation in loops
