# Blazor Patterns

> Reference for: C# Developer
> Load when: Building Blazor apps, components, state management, interop

## Component Basics

```razor
@* ProductList.razor *@
@page "/products"
@inject IProductService ProductService
@inject NavigationManager Navigation

<PageTitle>Products</PageTitle>

<h1>Products</h1>

@if (products is null)
{
    <p><em>Loading...</em></p>
}
else if (!products.Any())
{
    <p>No products found.</p>
}
else
{
    <div class="product-grid">
        @foreach (var product in products)
        {
            <ProductCard Product="@product" OnClick="@(() => ViewDetails(product.Id))" />
        }
    </div>
}

@code {
    private List<ProductDto>? products;

    protected override async Task OnInitializedAsync()
    {
        products = await ProductService.GetAllAsync();
    }

    private void ViewDetails(int id)
    {
        Navigation.NavigateTo($"/products/{id}");
    }
}
```

## Component Parameters

```razor
@* ProductCard.razor *@
<div class="card" @onclick="HandleClick">
    <img src="@Product.ImageUrl" alt="@Product.Name" />
    <h3>@Product.Name</h3>
    <p class="price">@Product.Price.ToString("C")</p>

    @if (ShowDescription)
    {
        <p>@Product.Description</p>
    }

    <CascadingValue Value="@Product">
        @ChildContent
    </CascadingValue>
</div>

@code {
    [Parameter, EditorRequired]
    public ProductDto Product { get; set; } = null!;

    [Parameter]
    public bool ShowDescription { get; set; }

    [Parameter]
    public EventCallback<int> OnClick { get; set; }

    [Parameter]
    public RenderFragment? ChildContent { get; set; }

    private async Task HandleClick()
    {
        await OnClick.InvokeAsync(Product.Id);
    }
}
```

## Form Handling and Validation

```razor
@* ProductForm.razor *@
@using System.ComponentModel.DataAnnotations

<EditForm Model="@model" OnValidSubmit="@HandleValidSubmit">
    <DataAnnotationsValidator />
    <ValidationSummary />

    <div class="form-group">
        <label>Name:</label>
        <InputText @bind-Value="model.Name" class="form-control" />
        <ValidationMessage For="@(() => model.Name)" />
    </div>

    <div class="form-group">
        <label>Price:</label>
        <InputNumber @bind-Value="model.Price" class="form-control" />
        <ValidationMessage For="@(() => model.Price)" />
    </div>

    <div class="form-group">
        <label>Category:</label>
        <InputSelect @bind-Value="model.CategoryId" class="form-control">
            <option value="">Select category...</option>
            @foreach (var category in categories)
            {
                <option value="@category.Id">@category.Name</option>
            }
        </InputSelect>
        <ValidationMessage For="@(() => model.CategoryId)" />
    </div>

    <button type="submit" class="btn btn-primary" disabled="@isSaving">
        @(isSaving ? "Saving..." : "Save")
    </button>
</EditForm>

@code {
    [Parameter]
    public int? ProductId { get; set; }

    [Parameter]
    public EventCallback<ProductDto> OnSaved { get; set; }

    private ProductFormModel model = new();
    private List<CategoryDto> categories = [];
    private bool isSaving;

    protected override async Task OnInitializedAsync()
    {
        categories = await CategoryService.GetAllAsync();

        if (ProductId.HasValue)
        {
            var product = await ProductService.GetByIdAsync(ProductId.Value);
            if (product is not null)
            {
                model = new ProductFormModel
                {
                    Name = product.Name,
                    Price = product.Price,
                    CategoryId = product.CategoryId
                };
            }
        }
    }

    private async Task HandleValidSubmit()
    {
        isSaving = true;
        try
        {
            var product = ProductId.HasValue
                ? await ProductService.UpdateAsync(ProductId.Value, model)
                : await ProductService.CreateAsync(model);

            await OnSaved.InvokeAsync(product);
        }
        finally
        {
            isSaving = false;
        }
    }

    private class ProductFormModel
    {
        [Required, StringLength(200)]
        public string Name { get; set; } = string.Empty;

        [Required, Range(0.01, 999999.99)]
        public decimal Price { get; set; }

        [Required]
        public int CategoryId { get; set; }
    }
}
```

## State Management with Cascading Values

```razor
@* App.razor *@
<CascadingAuthenticationState>
    <CascadingValue Value="@appState">
        <Router AppAssembly="@typeof(App).Assembly">
            <Found Context="routeData">
                <RouteView RouteData="@routeData" DefaultLayout="@typeof(MainLayout)" />
            </Found>
        </Router>
    </CascadingValue>
</CascadingAuthenticationState>

@code {
    private AppState appState = new();
}

// AppState.cs
public class AppState
{
    public event Action? OnChange;

    private int _cartItemCount;
    public int CartItemCount
    {
        get => _cartItemCount;
        set
        {
            if (_cartItemCount != value)
            {
                _cartItemCount = value;
                NotifyStateChanged();
            }
        }
    }

    private void NotifyStateChanged() => OnChange?.Invoke();
}

// Using cascading value
@code {
    [CascadingParameter]
    public AppState AppState { get; set; } = null!;

    protected override void OnInitialized()
    {
        AppState.OnChange += StateHasChanged;
    }

    public void Dispose()
    {
        AppState.OnChange -= StateHasChanged;
    }
}
```

## JavaScript Interop

```razor
@inject IJSRuntime JS
@implements IAsyncDisposable

<div @ref="mapElement" style="height: 400px;"></div>

@code {
    private ElementReference mapElement;
    private IJSObjectReference? module;
    private IJSObjectReference? mapInstance;

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        if (firstRender)
        {
            // Import JS module
            module = await JS.InvokeAsync<IJSObjectReference>(
                "import", "./js/mapComponent.js");

            // Initialize map
            mapInstance = await module.InvokeAsync<IJSObjectReference>(
                "initializeMap", mapElement);
        }
    }

    public async Task SetLocationAsync(double lat, double lng)
    {
        if (mapInstance is not null)
        {
            await mapInstance.InvokeVoidAsync("setLocation", lat, lng);
        }
    }

    async ValueTask IAsyncDisposable.DisposeAsync()
    {
        if (mapInstance is not null)
            await mapInstance.DisposeAsync();

        if (module is not null)
            await module.DisposeAsync();
    }
}
```

```javascript
// wwwroot/js/mapComponent.js
export function initializeMap(element) {
    const map = new Map(element);
    return {
        setLocation: (lat, lng) => {
            map.setView([lat, lng], 13);
        }
    };
}
```

## Component Lifecycle

```razor
@implements IDisposable

@code {
    protected override void OnInitialized()
    {
        // Called when component is initialized
        // Use for non-async initialization
    }

    protected override async Task OnInitializedAsync()
    {
        // Called when component is initialized
        // Use for async initialization (API calls, etc.)
        await LoadDataAsync();
    }

    protected override void OnParametersSet()
    {
        // Called when parameters are set
        // Use to react to parameter changes
    }

    protected override async Task OnParametersSetAsync()
    {
        // Async version of OnParametersSet
        await ValidateParametersAsync();
    }

    protected override bool ShouldRender()
    {
        // Return false to prevent re-rendering
        return true;
    }

    protected override void OnAfterRender(bool firstRender)
    {
        // Called after component renders
        // firstRender is true only on first render
        if (firstRender)
        {
            // One-time setup
        }
    }

    protected override async Task OnAfterRenderAsync(bool firstRender)
    {
        // Async version - use for JS interop
        if (firstRender)
        {
            await InitializeJavaScriptAsync();
        }
    }

    public void Dispose()
    {
        // Cleanup resources
        timer?.Dispose();
    }
}
```

## Authentication

```razor
@* LoginDisplay.razor *@
<AuthorizeView>
    <Authorized>
        <span>Hello, @context.User.Identity?.Name!</span>
        <button @onclick="LogOut">Log out</button>
    </Authorized>
    <NotAuthorized>
        <a href="authentication/login">Log in</a>
    </NotAuthorized>
</AuthorizeView>

@code {
    [Inject]
    private NavigationManager Navigation { get; set; } = null!;

    private void LogOut()
    {
        Navigation.NavigateTo("authentication/logout");
    }
}

@* Protecting a page *@
@page "/admin"
@attribute [Authorize(Roles = "Admin")]

<h1>Admin Panel</h1>

@* Conditional rendering based on auth *@
<AuthorizeView Roles="Admin">
    <Authorized>
        <button>Delete All</button>
    </Authorized>
</AuthorizeView>
```

## Error Boundaries

```razor
<ErrorBoundary>
    <ChildContent>
        <ProductList />
    </ChildContent>
    <ErrorContent Context="exception">
        <div class="alert alert-danger">
            <h4>An error occurred</h4>
            <p>@exception.Message</p>
            <button @onclick="RecoverAsync">Retry</button>
        </div>
    </ErrorContent>
</ErrorBoundary>

@code {
    private ErrorBoundary? errorBoundary;

    protected override void OnParametersSet()
    {
        errorBoundary?.Recover();
    }

    private async Task RecoverAsync()
    {
        errorBoundary?.Recover();
        await LoadDataAsync();
    }
}
```

## Virtualization for Large Lists

```razor
@using Microsoft.AspNetCore.Components.Web.Virtualization

<Virtualize Items="@products" Context="product">
    <div class="product-item">
        <h3>@product.Name</h3>
        <p>@product.Price.ToString("C")</p>
    </div>
</Virtualize>

@* Or with ItemsProvider for lazy loading *@
<Virtualize ItemsProvider="@LoadProducts" Context="product">
    <ItemContent>
        <ProductCard Product="@product" />
    </ItemContent>
    <Placeholder>
        <div class="loading-skeleton"></div>
    </Placeholder>
</Virtualize>

@code {
    private async ValueTask<ItemsProviderResult<ProductDto>> LoadProducts(
        ItemsProviderRequest request)
    {
        var products = await ProductService.GetPageAsync(
            request.StartIndex,
            request.Count);

        var totalCount = await ProductService.GetCountAsync();

        return new ItemsProviderResult<ProductDto>(products, totalCount);
    }
}
```

## SignalR Integration

```csharp
// Program.cs
builder.Services.AddScoped<NotificationService>();

// NotificationService.cs
public class NotificationService : IAsyncDisposable
{
    private HubConnection? _hubConnection;

    public async Task InitializeAsync(string hubUrl)
    {
        _hubConnection = new HubConnectionBuilder()
            .WithUrl(hubUrl)
            .WithAutomaticReconnect()
            .Build();

        _hubConnection.On<string>("ReceiveNotification", notification =>
        {
            OnNotificationReceived?.Invoke(notification);
        });

        await _hubConnection.StartAsync();
    }

    public event Action<string>? OnNotificationReceived;

    public async ValueTask DisposeAsync()
    {
        if (_hubConnection is not null)
            await _hubConnection.DisposeAsync();
    }
}
```

```razor
@inject NotificationService NotificationService
@implements IDisposable

@if (!string.IsNullOrEmpty(lastNotification))
{
    <div class="notification">@lastNotification</div>
}

@code {
    private string? lastNotification;

    protected override async Task OnInitializedAsync()
    {
        NotificationService.OnNotificationReceived += HandleNotification;
        await NotificationService.InitializeAsync("/notificationHub");
    }

    private void HandleNotification(string notification)
    {
        lastNotification = notification;
        StateHasChanged();
    }

    public void Dispose()
    {
        NotificationService.OnNotificationReceived -= HandleNotification;
    }
}
```

## Quick Reference

| Feature | Use Case | Notes |
|---------|----------|-------|
| `@page` | Route definition | Can have multiple routes |
| `@inject` | Dependency injection | Or use `[Inject]` property |
| `@bind` | Two-way binding | `@bind-Value` for components |
| `[Parameter]` | Component input | Use `[EditorRequired]` when needed |
| `EventCallback` | Component events | Type-safe callbacks |
| `RenderFragment` | Child content | For flexible layouts |
| `CascadingValue` | Shared state | Automatic to descendants |
| `AuthorizeView` | Conditional auth UI | Or `@attribute [Authorize]` |
| `ErrorBoundary` | Error handling | Catch render exceptions |
| `Virtualize` | Large lists | Performance optimization |
