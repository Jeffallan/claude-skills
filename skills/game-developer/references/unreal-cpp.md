# Unreal Engine C++ Development

## Actor Component Pattern

```cpp
// Header file: MyCharacter.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "MyCharacter.generated.h"

UCLASS()
class MYGAME_API AMyCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    AMyCharacter();

protected:
    virtual void BeginPlay() override;

public:
    virtual void Tick(float DeltaTime) override;
    virtual void SetupPlayerInputComponent(class UInputComponent* PlayerInputComponent) override;

private:
    // Exposed to Blueprints
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Movement", meta = (AllowPrivateAccess = "true"))
    float WalkSpeed = 600.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera", meta = (AllowPrivateAccess = "true"))
    class UCameraComponent* CameraComponent;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Camera", meta = (AllowPrivateAccess = "true"))
    class USpringArmComponent* SpringArm;

    void MoveForward(float Value);
    void MoveRight(float Value);
};
```

```cpp
// Implementation: MyCharacter.cpp
#include "MyCharacter.h"
#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/CharacterMovementComponent.h"

AMyCharacter::AMyCharacter()
{
    PrimaryActorTick.bCanEverTick = true;

    // Create components
    SpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArm"));
    SpringArm->SetupAttachment(RootComponent);
    SpringArm->TargetArmLength = 300.0f;
    SpringArm->bUsePawnControlRotation = true;

    CameraComponent = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
    CameraComponent->SetupAttachment(SpringArm, USpringArmComponent::SocketName);
}

void AMyCharacter::BeginPlay()
{
    Super::BeginPlay();

    GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
}

void AMyCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);

    PlayerInputComponent->BindAxis("MoveForward", this, &AMyCharacter::MoveForward);
    PlayerInputComponent->BindAxis("MoveRight", this, &AMyCharacter::MoveRight);
    PlayerInputComponent->BindAxis("Turn", this, &APawn::AddControllerYawInput);
    PlayerInputComponent->BindAxis("LookUp", this, &APawn::AddControllerPitchInput);
}

void AMyCharacter::MoveForward(float Value)
{
    if (Controller && Value != 0.0f)
    {
        const FRotator Rotation = Controller->GetControlRotation();
        const FRotator YawRotation(0, Rotation.Yaw, 0);
        const FVector Direction = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
        AddMovementInput(Direction, Value);
    }
}
```

## Blueprint Callable Functions

```cpp
UCLASS()
class MYGAME_API UHealthComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UHealthComponent();

protected:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Health")
    float MaxHealth = 100.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Health")
    float CurrentHealth;

    // Event dispatcher for Blueprint
    UPROPERTY(BlueprintAssignable, Category = "Health")
    FOnHealthChangedSignature OnHealthChanged;

public:
    // Callable from Blueprint
    UFUNCTION(BlueprintCallable, Category = "Health")
    void TakeDamage(float Damage);

    UFUNCTION(BlueprintCallable, Category = "Health")
    void Heal(float Amount);

    UFUNCTION(BlueprintPure, Category = "Health")
    float GetHealthPercent() const { return CurrentHealth / MaxHealth; }

    // Native event that can be overridden in Blueprint
    UFUNCTION(BlueprintNativeEvent, Category = "Health")
    void OnDeath();
    virtual void OnDeath_Implementation();
};

// Event delegate
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnHealthChangedSignature, float, Health, float, MaxHealth);
```

## Actor Component System

```cpp
// Custom Actor Component
UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class MYGAME_API UInventoryComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UInventoryComponent();

protected:
    virtual void BeginPlay() override;

private:
    UPROPERTY(EditAnywhere, Category = "Inventory")
    int32 MaxSlots = 20;

    UPROPERTY()
    TArray<class UItemData*> Items;

public:
    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool AddItem(UItemData* Item);

    UFUNCTION(BlueprintCallable, Category = "Inventory")
    bool RemoveItem(UItemData* Item);

    UFUNCTION(BlueprintPure, Category = "Inventory")
    int32 GetItemCount() const { return Items.Num(); }
};
```

## Timers and Async Operations

```cpp
class AWeapon : public AActor
{
private:
    FTimerHandle FireRateTimer;

    UPROPERTY(EditAnywhere, Category = "Weapon")
    float FireRate = 0.2f; // Seconds between shots

public:
    void StartFiring()
    {
        Fire(); // Immediate first shot
        GetWorldTimerManager().SetTimer(FireRateTimer, this, &AWeapon::Fire, FireRate, true);
    }

    void StopFiring()
    {
        GetWorldTimerManager().ClearTimer(FireRateTimer);
    }

    void Fire()
    {
        // Spawn projectile
        FVector Location = GetActorLocation();
        FRotator Rotation = GetActorRotation();
        GetWorld()->SpawnActor<AProjectile>(ProjectileClass, Location, Rotation);
    }
};
```

## Object Pooling in Unreal

```cpp
UCLASS()
class APooledActor : public AActor
{
    GENERATED_BODY()

private:
    bool bIsActive = false;

public:
    void Activate()
    {
        bIsActive = true;
        SetActorHiddenInGame(false);
        SetActorEnableCollision(true);
        SetActorTickEnabled(true);
    }

    void Deactivate()
    {
        bIsActive = false;
        SetActorHiddenInGame(true);
        SetActorEnableCollision(false);
        SetActorTickEnabled(false);
    }

    bool IsActive() const { return bIsActive; }
};

UCLASS()
class AObjectPool : public AActor
{
    GENERATED_BODY()

private:
    UPROPERTY(EditAnywhere, Category = "Pool")
    TSubclassOf<APooledActor> PooledClass;

    UPROPERTY(EditAnywhere, Category = "Pool")
    int32 PoolSize = 50;

    UPROPERTY()
    TArray<APooledActor*> Pool;

protected:
    virtual void BeginPlay() override
    {
        Super::BeginPlay();

        // Pre-spawn pool
        for (int32 i = 0; i < PoolSize; i++)
        {
            APooledActor* Actor = GetWorld()->SpawnActor<APooledActor>(PooledClass);
            Actor->Deactivate();
            Pool.Add(Actor);
        }
    }

public:
    APooledActor* GetPooledActor()
    {
        for (APooledActor* Actor : Pool)
        {
            if (!Actor->IsActive())
            {
                Actor->Activate();
                return Actor;
            }
        }

        // Expand pool if needed
        APooledActor* NewActor = GetWorld()->SpawnActor<APooledActor>(PooledClass);
        Pool.Add(NewActor);
        NewActor->Activate();
        return NewActor;
    }

    void ReturnToPool(APooledActor* Actor)
    {
        Actor->Deactivate();
    }
};
```

## Data Assets and Structures

```cpp
// Data structure
USTRUCT(BlueprintType)
struct FWeaponStats
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FName WeaponName;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Damage = 10.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float FireRate = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 MagazineSize = 30;
};

// Data asset
UCLASS()
class UWeaponDataAsset : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
    FWeaponStats Stats;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
    TSubclassOf<class AProjectile> ProjectileClass;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Weapon")
    USoundBase* FireSound;
};
```

## Smart Pointers

```cpp
// Use TSharedPtr for shared ownership
TSharedPtr<FGameData> GameData = MakeShared<FGameData>();

// Use TWeakPtr to avoid circular references
TWeakPtr<AActor> WeakActorRef = SharedActorPtr;

// Use TUniquePtr for exclusive ownership
TUniquePtr<FComplexSystem> System = MakeUnique<FComplexSystem>();
```

## Performance Best Practices

- Use `UPROPERTY()` for garbage collection (don't use raw pointers for UObjects)
- Cache component references in `BeginPlay()`
- Use `PrimaryActorTick.bCanEverTick = false` if Tick not needed
- Prefer Timers over Tick for periodic updates
- Use `BlueprintPure` for getter functions (no execution pin)
- Profile with Unreal Insights and stat commands (`stat fps`, `stat unit`, `stat game`)
- Use forward declarations in headers, includes in .cpp files
- Implement object pooling for frequently spawned actors
