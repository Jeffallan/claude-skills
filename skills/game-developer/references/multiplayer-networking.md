# Multiplayer Networking

## Client-Server Architecture

```csharp
// Server-authoritative model
public class NetworkPlayer
{
    public int PlayerId { get; set; }
    public Vector3 Position { get; set; }
    public Quaternion Rotation { get; set; }
    public float Health { get; set; }

    // Server validates all actions
    public bool TryMove(Vector3 newPosition, float deltaTime)
    {
        float maxDistance = MoveSpeed * deltaTime * 1.1f; // 10% tolerance

        if (Vector3.Distance(Position, newPosition) > maxDistance)
        {
            // Client sent invalid movement - possible cheat
            return false;
        }

        Position = newPosition;
        return true;
    }
}

// Server
public class GameServer
{
    private Dictionary<int, NetworkPlayer> players = new();

    public void ProcessPlayerInput(int playerId, PlayerInput input)
    {
        if (!players.TryGetValue(playerId, out NetworkPlayer player))
            return;

        // Server processes input
        Vector3 newPosition = player.Position + input.Movement;

        if (player.TryMove(newPosition, Time.deltaTime))
        {
            // Broadcast to other clients
            BroadcastPlayerState(player);
        }
        else
        {
            // Send authoritative correction
            SendPositionCorrection(playerId, player.Position);
        }
    }
}
```

## State Synchronization

```csharp
// Network state with interpolation
public class NetworkTransform
{
    // Circular buffer for state history
    private struct State
    {
        public float Timestamp;
        public Vector3 Position;
        public Quaternion Rotation;
    }

    private State[] stateBuffer = new State[32];
    private int bufferIndex = 0;

    public void ReceiveState(float timestamp, Vector3 position, Quaternion rotation)
    {
        stateBuffer[bufferIndex] = new State
        {
            Timestamp = timestamp,
            Position = position,
            Rotation = rotation
        };

        bufferIndex = (bufferIndex + 1) % stateBuffer.Length;
    }

    public void Interpolate(float renderTime)
    {
        // Find two states to interpolate between
        State from = default;
        State to = default;

        for (int i = 0; i < stateBuffer.Length; i++)
        {
            if (stateBuffer[i].Timestamp <= renderTime)
                from = stateBuffer[i];
            else
            {
                to = stateBuffer[i];
                break;
            }
        }

        if (from.Timestamp == 0 || to.Timestamp == 0)
            return;

        // Interpolate between states
        float t = (renderTime - from.Timestamp) / (to.Timestamp - from.Timestamp);
        t = Mathf.Clamp01(t);

        transform.position = Vector3.Lerp(from.Position, to.Position, t);
        transform.rotation = Quaternion.Slerp(from.Rotation, to.Rotation, t);
    }
}
```

## Client-Side Prediction

```csharp
public class PredictivePlayer : MonoBehaviour
{
    private struct InputState
    {
        public int SequenceNumber;
        public float Timestamp;
        public Vector3 Movement;
    }

    private Queue<InputState> pendingInputs = new Queue<InputState>();
    private int sequenceNumber = 0;
    private Vector3 predictedPosition;

    void Update()
    {
        // Gather input
        Vector3 movement = new Vector3(
            Input.GetAxis("Horizontal"),
            0,
            Input.GetAxis("Vertical")
        ) * moveSpeed * Time.deltaTime;

        // Create input state
        InputState input = new InputState
        {
            SequenceNumber = sequenceNumber++,
            Timestamp = Time.time,
            Movement = movement
        };

        // Send to server
        SendInputToServer(input);

        // Apply locally (prediction)
        predictedPosition += movement;
        transform.position = predictedPosition;

        // Store for reconciliation
        pendingInputs.Enqueue(input);
    }

    public void ReceiveServerState(int lastProcessedInput, Vector3 serverPosition)
    {
        // Remove acknowledged inputs
        while (pendingInputs.Count > 0 && pendingInputs.Peek().SequenceNumber <= lastProcessedInput)
        {
            pendingInputs.Dequeue();
        }

        // Start from server position
        predictedPosition = serverPosition;

        // Replay pending inputs (reconciliation)
        foreach (var input in pendingInputs)
        {
            predictedPosition += input.Movement;
        }

        // Smooth correction if needed
        if (Vector3.Distance(transform.position, predictedPosition) > 0.1f)
        {
            // Snap or smooth based on distance
            transform.position = predictedPosition;
        }
    }
}
```

## Lag Compensation (Server-Side Rewind)

```csharp
public class LagCompensation
{
    private struct HistoricalState
    {
        public float Timestamp;
        public Vector3 Position;
        public Quaternion Rotation;
        public Bounds Hitbox;
    }

    private Dictionary<int, Queue<HistoricalState>> playerHistory = new();
    private const float MaxHistoryTime = 1.0f; // 1 second of history

    public void RecordState(int playerId, Vector3 position, Quaternion rotation, Bounds hitbox)
    {
        if (!playerHistory.ContainsKey(playerId))
            playerHistory[playerId] = new Queue<HistoricalState>();

        var queue = playerHistory[playerId];

        // Add current state
        queue.Enqueue(new HistoricalState
        {
            Timestamp = Time.time,
            Position = position,
            Rotation = rotation,
            Hitbox = hitbox
        });

        // Remove old states
        while (queue.Count > 0 && Time.time - queue.Peek().Timestamp > MaxHistoryTime)
        {
            queue.Dequeue();
        }
    }

    public bool ProcessHitscan(int shooterPlayerId, float clientTimestamp, Ray ray, out int hitPlayerId)
    {
        // Rewind to client's timestamp
        float targetTime = clientTimestamp; // Shooter's perceived time

        foreach (var kvp in playerHistory)
        {
            int playerId = kvp.Key;
            if (playerId == shooterPlayerId) continue; // Don't shoot self

            // Find state at target time
            HistoricalState state = GetStateAtTime(kvp.Value, targetTime);

            // Check raycast against historical hitbox
            if (state.Hitbox.IntersectRay(ray))
            {
                hitPlayerId = playerId;
                return true;
            }
        }

        hitPlayerId = -1;
        return false;
    }

    private HistoricalState GetStateAtTime(Queue<HistoricalState> history, float targetTime)
    {
        HistoricalState closest = default;
        float minDelta = float.MaxValue;

        foreach (var state in history)
        {
            float delta = Mathf.Abs(state.Timestamp - targetTime);
            if (delta < minDelta)
            {
                minDelta = delta;
                closest = state;
            }
        }

        return closest;
    }
}
```

## Network Message Serialization

```csharp
using System;
using System.IO;

// Efficient binary serialization
public class NetworkWriter
{
    private MemoryStream stream = new MemoryStream();
    private BinaryWriter writer;

    public NetworkWriter()
    {
        writer = new BinaryWriter(stream);
    }

    public void WriteInt(int value) => writer.Write(value);
    public void WriteFloat(float value) => writer.Write(value);
    public void WriteBool(bool value) => writer.Write(value);
    public void WriteString(string value) => writer.Write(value);

    public void WriteVector3(Vector3 value)
    {
        writer.Write(value.x);
        writer.Write(value.y);
        writer.Write(value.z);
    }

    // Compressed vector (16-bit per component)
    public void WriteVector3Compressed(Vector3 value, float min, float max)
    {
        writer.Write(CompressFloat(value.x, min, max));
        writer.Write(CompressFloat(value.y, min, max));
        writer.Write(CompressFloat(value.z, min, max));
    }

    private ushort CompressFloat(float value, float min, float max)
    {
        float normalized = Mathf.Clamp01((value - min) / (max - min));
        return (ushort)(normalized * ushort.MaxValue);
    }

    public byte[] ToArray() => stream.ToArray();
}

public class NetworkReader
{
    private BinaryReader reader;

    public NetworkReader(byte[] data)
    {
        reader = new BinaryReader(new MemoryStream(data));
    }

    public int ReadInt() => reader.ReadInt32();
    public float ReadFloat() => reader.ReadSingle();
    public bool ReadBool() => reader.ReadBoolean();
    public string ReadString() => reader.ReadString();

    public Vector3 ReadVector3()
    {
        return new Vector3(
            reader.ReadSingle(),
            reader.ReadSingle(),
            reader.ReadSingle()
        );
    }

    public Vector3 ReadVector3Compressed(float min, float max)
    {
        return new Vector3(
            DecompressFloat(reader.ReadUInt16(), min, max),
            DecompressFloat(reader.ReadUInt16(), min, max),
            DecompressFloat(reader.ReadUInt16(), min, max)
        );
    }

    private float DecompressFloat(ushort value, float min, float max)
    {
        float normalized = value / (float)ushort.MaxValue;
        return min + normalized * (max - min);
    }
}
```

## Interest Management (Relevancy)

```csharp
public class InterestManager
{
    private Dictionary<int, Vector3> playerPositions = new();
    private float relevancyRadius = 100f;

    public HashSet<int> GetRelevantPlayers(int playerId)
    {
        if (!playerPositions.TryGetValue(playerId, out Vector3 playerPos))
            return new HashSet<int>();

        HashSet<int> relevant = new HashSet<int>();

        foreach (var kvp in playerPositions)
        {
            if (kvp.Key == playerId) continue;

            float distance = Vector3.Distance(playerPos, kvp.Value);
            if (distance <= relevancyRadius)
            {
                relevant.Add(kvp.Key);
            }
        }

        return relevant;
    }

    public void BroadcastToRelevant(int senderId, byte[] message)
    {
        var recipients = GetRelevantPlayers(senderId);

        foreach (int recipientId in recipients)
        {
            SendMessage(recipientId, message);
        }
    }
}
```

## Delta Compression

```csharp
public class DeltaCompressor
{
    private Dictionary<int, NetworkPlayer> lastSentState = new();

    public byte[] CompressState(NetworkPlayer current)
    {
        if (!lastSentState.TryGetValue(current.PlayerId, out NetworkPlayer previous))
        {
            // First time - send full state
            return SerializeFullState(current);
        }

        NetworkWriter writer = new NetworkWriter();
        byte flags = 0;

        // Only send changed fields
        if (Vector3.Distance(current.Position, previous.Position) > 0.01f)
        {
            flags |= 1 << 0; // Position changed
            writer.WriteVector3Compressed(current.Position, -1000f, 1000f);
        }

        if (Quaternion.Angle(current.Rotation, previous.Rotation) > 1f)
        {
            flags |= 1 << 1; // Rotation changed
            writer.WriteQuaternionCompressed(current.Rotation);
        }

        if (Mathf.Abs(current.Health - previous.Health) > 0.1f)
        {
            flags |= 1 << 2; // Health changed
            writer.WriteFloat(current.Health);
        }

        // Prepend flags
        byte[] data = writer.ToArray();
        byte[] result = new byte[data.Length + 1];
        result[0] = flags;
        Array.Copy(data, 0, result, 1, data.Length);

        // Update last sent state
        lastSentState[current.PlayerId] = current;

        return result;
    }
}
```

## Network Performance Best Practices

**Bandwidth optimization:**
- Compress position/rotation data
- Use delta compression
- Implement relevancy system
- Limit update rate based on distance
- Batch multiple updates into single packet

**Latency optimization:**
- Client-side prediction for local player
- Server reconciliation for corrections
- Entity interpolation for other players
- Lag compensation for hitscan weapons

**Target metrics:**
- Latency: < 100ms
- Tick rate: 20-60 Hz (depends on game type)
- Packet size: < 1200 bytes (avoid fragmentation)
- Update rate: 10-20 Hz for distant objects, 60 Hz for nearby

**Security considerations:**
- Server-authoritative for all game logic
- Validate all client inputs
- Rate limiting to prevent flooding
- Encrypt sensitive data
- Anti-cheat measures (sanity checks, statistical analysis)
