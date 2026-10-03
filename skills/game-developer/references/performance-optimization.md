# Performance Optimization

## Profiling First

```csharp
using UnityEngine.Profiling;

public class PerformanceMonitor : MonoBehaviour
{
    private void Update()
    {
        // CPU profiling
        Profiler.BeginSample("Enemy AI Update");
        UpdateEnemyAI();
        Profiler.EndSample();

        // Memory profiling
        long allocatedMemory = Profiler.GetTotalAllocatedMemoryLong();
        long reservedMemory = Profiler.GetTotalReservedMemoryLong();

        // FPS calculation
        float fps = 1.0f / Time.unscaledDeltaTime;
    }
}
```

## Memory Optimization

```csharp
// BAD: Allocates garbage every frame
void Update()
{
    string status = "Health: " + health + " / " + maxHealth; // Boxing + allocation
    Vector3 direction = transform.position - target.position; // Allocation
    var enemies = GameObject.FindGameObjectsWithTag("Enemy"); // Allocation
}

// GOOD: Zero allocations
private StringBuilder statusBuilder = new StringBuilder(50);
private Vector3 directionCache;
private List<Enemy> enemyCache = new List<Enemy>(100);

void Update()
{
    // Reuse StringBuilder
    statusBuilder.Clear();
    statusBuilder.Append("Health: ").Append(health).Append(" / ").Append(maxHealth);

    // Reuse Vector3
    directionCache = transform.position - target.position;

    // Cache references (done in Start)
    foreach (var enemy in enemyCache)
    {
        enemy.UpdateLogic();
    }
}
```

## Draw Call Batching

```csharp
// Static batching (for non-moving objects)
public class StaticBatchHelper : MonoBehaviour
{
    void Start()
    {
        // Mark objects as static in Inspector OR
        GameObject[] staticObjects = GameObject.FindGameObjectsWithTag("StaticProp");
        StaticBatchingUtility.Combine(staticObjects, gameObject);
    }
}

// Dynamic batching requirements:
// - Same material
// - Vertex count < 300
// - Same scale (non-uniform scale breaks batching)
// - No lightmaps

// GPU Instancing (for many identical objects)
// Add to shader: #pragma multi_compile_instancing
// Add to material: Enable GPU Instancing checkbox
// Use Graphics.DrawMeshInstanced or Graphics.RenderMeshInstanced
```

## LOD (Level of Detail) System

```csharp
using UnityEngine;

public class LODSetup : MonoBehaviour
{
    void SetupLOD()
    {
        LODGroup lodGroup = gameObject.AddComponent<LODGroup>();

        // LOD 0: 0% - 60% screen height (high detail)
        LOD[] lods = new LOD[3];
        lods[0] = new LOD(0.6f, GetRenderers("LOD0"));

        // LOD 1: 60% - 30% screen height (medium detail)
        lods[1] = new LOD(0.3f, GetRenderers("LOD1"));

        // LOD 2: 30% - 10% screen height (low detail)
        lods[2] = new LOD(0.1f, GetRenderers("LOD2"));

        lodGroup.SetLODs(lods);
        lodGroup.RecalculateBounds();
    }

    private Renderer[] GetRenderers(string lodName)
    {
        // Return renderers for specific LOD level
        return transform.Find(lodName).GetComponentsInChildren<Renderer>();
    }
}
```

## Occlusion Culling

```csharp
// Setup in Unity:
// 1. Mark static objects as "Occluder Static" and "Occludee Static"
// 2. Window > Rendering > Occlusion Culling
// 3. Bake occlusion data

// Runtime check
public class OcclusionCheck : MonoBehaviour
{
    private Camera mainCamera;

    void Start()
    {
        mainCamera = Camera.main;
    }

    void Update()
    {
        // Check if object is visible to camera
        Plane[] planes = GeometryUtility.CalculateFrustumPlanes(mainCamera);
        Bounds bounds = GetComponent<Renderer>().bounds;

        if (GeometryUtility.TestPlanesAABB(planes, bounds))
        {
            // Object is in camera frustum
            UpdateVisibleObject();
        }
    }
}
```

## Object Pooling (Performance-Focused)

```csharp
public class OptimizedPool<T> where T : Component
{
    private readonly Stack<T> available = new Stack<T>();
    private readonly HashSet<T> inUse = new HashSet<T>();
    private readonly T prefab;
    private readonly Transform parent;

    public OptimizedPool(T prefab, int initialSize, Transform parent = null)
    {
        this.prefab = prefab;
        this.parent = parent;

        // Pre-warm pool
        for (int i = 0; i < initialSize; i++)
        {
            T instance = Object.Instantiate(prefab, parent);
            instance.gameObject.SetActive(false);
            available.Push(instance);
        }
    }

    public T Get()
    {
        T instance;

        if (available.Count > 0)
        {
            instance = available.Pop();
        }
        else
        {
            // Pool exhausted, create new
            instance = Object.Instantiate(prefab, parent);
        }

        instance.gameObject.SetActive(true);
        inUse.Add(instance);
        return instance;
    }

    public void Return(T instance)
    {
        if (inUse.Remove(instance))
        {
            instance.gameObject.SetActive(false);
            available.Push(instance);
        }
    }

    public void Clear()
    {
        foreach (var instance in inUse)
            Object.Destroy(instance.gameObject);

        foreach (var instance in available)
            Object.Destroy(instance.gameObject);

        inUse.Clear();
        available.Clear();
    }
}
```

## Physics Optimization

```csharp
public class PhysicsOptimization : MonoBehaviour
{
    void Start()
    {
        // Use layers for collision filtering
        // Edit > Project Settings > Physics > Layer Collision Matrix

        // Use trigger colliders when possible (cheaper than collision)
        // Use simple collider shapes (sphere, box > capsule > mesh)

        // Disable unnecessary physics
        Rigidbody rb = GetComponent<Rigidbody>();
        rb.sleepThreshold = 0.1f; // Allow sleeping
        rb.interpolation = RigidbodyInterpolation.None; // Only if needed

        // Use fixed timestep wisely
        // Edit > Project Settings > Time > Fixed Timestep (default 0.02 = 50 fps)
    }

    // Raycasts: cache and limit
    private RaycastHit hitInfo;
    private float raycastInterval = 0.1f;
    private float nextRaycast;

    void Update()
    {
        if (Time.time >= nextRaycast)
        {
            // Use layers to filter raycasts
            int layerMask = 1 << LayerMask.NameToLayer("Ground");

            if (Physics.Raycast(transform.position, Vector3.down, out hitInfo, 10f, layerMask))
            {
                // Process hit
            }

            nextRaycast = Time.time + raycastInterval;
        }
    }
}
```

## Texture and Material Optimization

```csharp
// Texture atlasing
public class TextureAtlas : MonoBehaviour
{
    // Combine multiple textures into one atlas
    // Reduces draw calls significantly
    // Use Sprite Atlas or Texture Packer

    void PackTextures()
    {
        Texture2D[] textures = new Texture2D[10]; // Your textures
        Texture2D atlas = new Texture2D(2048, 2048);

        // Pack textures into atlas
        Rect[] uvs = atlas.PackTextures(textures, 2, 2048);

        // Update UV coordinates on meshes
    }
}

// Material sharing
public class MaterialSharing : MonoBehaviour
{
    void Start()
    {
        // BAD: Creates material instance
        Renderer renderer = GetComponent<Renderer>();
        renderer.material.color = Color.red; // Breaks batching!

        // GOOD: Share material
        Material sharedMat = renderer.sharedMaterial;
        // Modify material asset directly (affects all instances)
    }
}
```

## Update Optimization

```csharp
// Stagger updates to reduce per-frame cost
public class StaggeredUpdate : MonoBehaviour
{
    private static int updateOffset = 0;
    private int myOffset;

    void Start()
    {
        myOffset = updateOffset++;
    }

    void Update()
    {
        // Only update every 5th frame, staggered
        if ((Time.frameCount + myOffset) % 5 == 0)
        {
            ExpensiveUpdate();
        }
    }

    void ExpensiveUpdate()
    {
        // AI logic, pathfinding, etc.
    }
}

// Distance-based update rates
public class DistanceBasedUpdate : MonoBehaviour
{
    private Transform player;
    private float updateInterval;
    private float nextUpdate;

    void Update()
    {
        if (Time.time < nextUpdate) return;

        float distance = Vector3.Distance(transform.position, player.position);

        // Update more frequently when close
        if (distance < 10f)
            updateInterval = 0.05f; // 20 fps
        else if (distance < 50f)
            updateInterval = 0.1f; // 10 fps
        else
            updateInterval = 0.5f; // 2 fps

        PerformUpdate();
        nextUpdate = Time.time + updateInterval;
    }
}
```

## Async Loading

```csharp
using UnityEngine.SceneManagement;
using System.Collections;

public class AsyncLoader : MonoBehaviour
{
    public IEnumerator LoadSceneAsync(string sceneName)
    {
        AsyncOperation asyncLoad = SceneManager.LoadSceneAsync(sceneName);
        asyncLoad.allowSceneActivation = false;

        while (!asyncLoad.isDone)
        {
            // Loading progress
            float progress = Mathf.Clamp01(asyncLoad.progress / 0.9f);

            // When ready, activate
            if (asyncLoad.progress >= 0.9f)
            {
                // Wait for player input or fade completion
                yield return new WaitForSeconds(1f);
                asyncLoad.allowSceneActivation = true;
            }

            yield return null;
        }
    }

    public IEnumerator LoadAssetAsync<T>(string path) where T : Object
    {
        ResourceRequest request = Resources.LoadAsync<T>(path);

        while (!request.isDone)
        {
            yield return null;
        }

        T asset = request.asset as T;
        // Use asset
    }
}
```

## Performance Checklist

**Target: 60 FPS (16.67ms per frame)**

CPU Budget:
- Game logic: 5-7ms
- Rendering: 3-5ms
- Physics: 2-3ms
- Scripts: 2-3ms

Optimization priorities:
1. Profile first (Profiler, Frame Debugger)
2. Reduce draw calls (batching, instancing)
3. Optimize expensive Update loops
4. Use object pooling
5. Implement LOD systems
6. Enable occlusion culling
7. Optimize texture sizes and compression
8. Minimize garbage collection (allocations)
9. Use async loading
10. Implement distance-based update rates
