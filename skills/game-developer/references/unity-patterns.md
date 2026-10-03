# Unity Development Patterns

## MonoBehaviour Best Practices

```csharp
using UnityEngine;
using System.Collections.Generic;

public class EnemyController : MonoBehaviour
{
    // Serialize private fields for Inspector
    [SerializeField] private float moveSpeed = 5f;
    [SerializeField] private Transform target;

    // Cache component references
    private Rigidbody rb;
    private Animator animator;

    private void Awake()
    {
        // Cache components in Awake
        rb = GetComponent<Rigidbody>();
        animator = GetComponent<Animator>();
    }

    private void Start()
    {
        // Initialize after all Awake calls complete
        if (target == null)
            target = GameObject.FindGameObjectWithTag("Player").transform;
    }

    private void FixedUpdate()
    {
        // Physics calculations in FixedUpdate
        Vector3 direction = (target.position - transform.position).normalized;
        rb.MovePosition(transform.position + direction * moveSpeed * Time.fixedDeltaTime);
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
    [SerializeField] private WeaponData weaponData;
    private float nextFireTime;

    public void Fire()
    {
        if (Time.time < nextFireTime) return;

        // Use data from ScriptableObject
        Instantiate(weaponData.projectilePrefab, transform.position, transform.rotation);
        nextFireTime = Time.time + 1f / weaponData.fireRate;
    }
}
```

## Object Pooling Pattern

```csharp
public class ObjectPool : MonoBehaviour
{
    [SerializeField] private GameObject prefab;
    [SerializeField] private int poolSize = 20;

    private Queue<GameObject> pool = new Queue<GameObject>();

    private void Start()
    {
        // Pre-instantiate objects
        for (int i = 0; i < poolSize; i++)
        {
            GameObject obj = Instantiate(prefab);
            obj.SetActive(false);
            pool.Enqueue(obj);
        }
    }

    public GameObject Get()
    {
        if (pool.Count > 0)
        {
            GameObject obj = pool.Dequeue();
            obj.SetActive(true);
            return obj;
        }

        // Expand pool if needed
        return Instantiate(prefab);
    }

    public void Return(GameObject obj)
    {
        obj.SetActive(false);
        pool.Enqueue(obj);
    }
}

// Pooled object example
public class Bullet : MonoBehaviour
{
    private ObjectPool pool;

    public void Initialize(ObjectPool pool)
    {
        this.pool = pool;
    }

    private void OnCollisionEnter(Collision collision)
    {
        // Return to pool instead of destroying
        pool.Return(gameObject);
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
    [SerializeField] private int maxHealth = 100;
    private int currentHealth;

    // UnityEvent visible in Inspector
    public HealthChangedEvent onHealthChanged;
    public UnityEvent onDeath;

    private void Start()
    {
        currentHealth = maxHealth;
        onHealthChanged?.Invoke(currentHealth, maxHealth);
    }

    public void TakeDamage(int damage)
    {
        currentHealth = Mathf.Max(0, currentHealth - damage);
        onHealthChanged?.Invoke(currentHealth, maxHealth);

        if (currentHealth <= 0)
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
    private WaitForSeconds cooldownWait = new WaitForSeconds(5f);
    private Coroutine currentAbility;

    public void ActivateAbility()
    {
        // Stop previous coroutine if running
        if (currentAbility != null)
            StopCoroutine(currentAbility);

        currentAbility = StartCoroutine(AbilityCoroutine());
    }

    private IEnumerator AbilityCoroutine()
    {
        // Activate ability
        Debug.Log("Ability activated");

        // Wait for duration
        yield return cooldownWait;

        // Cooldown complete
        Debug.Log("Ability ready");
        currentAbility = null;
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
    private static GameManager instance;
    public static GameManager Instance => instance;

    private void Awake()
    {
        if (instance != null && instance != this)
        {
            Destroy(gameObject);
            return;
        }

        instance = this;
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
