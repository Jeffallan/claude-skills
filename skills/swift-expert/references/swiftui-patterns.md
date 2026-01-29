# SwiftUI Patterns

## State Management

```swift
import SwiftUI

// @State for local view state
struct CounterView: View {
    @State private var count = 0

    var body: some View {
        VStack {
            Text("Count: \(count)")
            Button("Increment") { count += 1 }
        }
    }
}

// @Binding for two-way data flow
struct ToggleView: View {
    @Binding var isOn: Bool

    var body: some View {
        Toggle("Enable Feature", isOn: $isOn)
    }
}

// @StateObject for observable objects (view owns it)
class ViewModel: ObservableObject {
    @Published var items: [String] = []
    @Published var isLoading = false
}

struct ContentView: View {
    @StateObject private var viewModel = ViewModel()

    var body: some View {
        List(viewModel.items, id: \.self) { item in
            Text(item)
        }
    }
}

// @ObservedObject for passed-in observable objects
struct DetailView: View {
    @ObservedObject var viewModel: ViewModel
}

// @EnvironmentObject for dependency injection
struct AppView: View {
    @EnvironmentObject var appState: AppState
}
```

## Modern View Composition

```swift
// View builder for custom containers
struct ConditionalView<Content: View>: View {
    let condition: Bool
    @ViewBuilder let content: () -> Content

    var body: some View {
        if condition {
            content()
        } else {
            EmptyView()
        }
    }
}

// Custom ViewModifier
struct CardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .background(Color.white)
            .cornerRadius(12)
            .shadow(radius: 4)
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardModifier())
    }
}

// Usage
Text("Hello")
    .cardStyle()
```

## Environment Values

```swift
// Custom environment key
private struct ThemeKey: EnvironmentKey {
    static let defaultValue: Theme = .light
}

extension EnvironmentValues {
    var theme: Theme {
        get { self[ThemeKey.self] }
        set { self[ThemeKey.self] = newValue }
    }
}

extension View {
    func theme(_ theme: Theme) -> some View {
        environment(\.theme, theme)
    }
}

// Usage
struct ThemedView: View {
    @Environment(\.theme) var theme

    var body: some View {
        Text("Themed")
            .foregroundColor(theme.textColor)
    }
}
```

## Preference Keys

```swift
// Collecting data from child views
struct SizePreferenceKey: PreferenceKey {
    static var defaultValue: CGSize = .zero

    static func reduce(value: inout CGSize, nextValue: () -> CGSize) {
        value = nextValue()
    }
}

struct MeasurableView: View {
    @State private var size: CGSize = .zero

    var body: some View {
        Text("Measure me")
            .background(
                GeometryReader { geometry in
                    Color.clear
                        .preference(key: SizePreferenceKey.self, value: geometry.size)
                }
            )
            .onPreferenceChange(SizePreferenceKey.self) { newSize in
                size = newSize
            }
    }
}
```

## Animations

```swift
// Implicit animations
struct AnimatedView: View {
    @State private var scale: CGFloat = 1.0

    var body: some View {
        Circle()
            .scaleEffect(scale)
            .animation(.spring(response: 0.5, dampingFraction: 0.6), value: scale)
            .onTapGesture {
                scale = scale == 1.0 ? 1.5 : 1.0
            }
    }
}

// Explicit animations
struct ExplicitAnimationView: View {
    @State private var offset: CGFloat = 0

    var body: some View {
        Text("Slide")
            .offset(x: offset)
            .onTapGesture {
                withAnimation(.easeInOut(duration: 0.3)) {
                    offset = offset == 0 ? 100 : 0
                }
            }
    }
}

// Custom transitions
extension AnyTransition {
    static var slideAndFade: AnyTransition {
        AnyTransition.slide.combined(with: .opacity)
    }
}
```

## Async/Await Integration

```swift
struct AsyncDataView: View {
    @State private var data: [Item] = []
    @State private var isLoading = false

    var body: some View {
        List(data) { item in
            Text(item.title)
        }
        .task {
            await loadData()
        }
        .refreshable {
            await loadData()
        }
    }

    private func loadData() async {
        isLoading = true
        defer { isLoading = false }

        do {
            data = try await API.fetchItems()
        } catch {
            print("Error: \(error)")
        }
    }
}
```

## Custom Layouts (iOS 16+)

```swift
struct WaterfallLayout: Layout {
    var columns: Int = 2
    var spacing: CGFloat = 8

    func sizeThatFits(
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) -> CGSize {
        // Calculate total size needed
        let columnWidth = (proposal.width! - spacing * CGFloat(columns - 1)) / CGFloat(columns)
        var columnHeights = Array(repeating: CGFloat(0), count: columns)

        for subview in subviews {
            let column = columnHeights.enumerated().min(by: { $0.element < $1.element })!.offset
            let size = subview.sizeThatFits(.init(width: columnWidth, height: nil))
            columnHeights[column] += size.height + spacing
        }

        return CGSize(
            width: proposal.width!,
            height: columnHeights.max()! - spacing
        )
    }

    func placeSubviews(
        in bounds: CGRect,
        proposal: ProposedViewSize,
        subviews: Subviews,
        cache: inout ()
    ) {
        let columnWidth = (bounds.width - spacing * CGFloat(columns - 1)) / CGFloat(columns)
        var columnHeights = Array(repeating: CGFloat(0), count: columns)

        for subview in subviews {
            let column = columnHeights.enumerated().min(by: { $0.element < $1.element })!.offset
            let x = bounds.minX + CGFloat(column) * (columnWidth + spacing)
            let y = bounds.minY + columnHeights[column]

            subview.place(
                at: CGPoint(x: x, y: y),
                proposal: .init(width: columnWidth, height: nil)
            )

            columnHeights[column] += subview.dimensions(in: .init(width: columnWidth, height: nil)).height + spacing
        }
    }
}
```

## Performance Tips

- Use `@State` for simple value types
- Use `@StateObject` for reference types you create
- Use `@ObservedObject` for reference types passed in
- Prefer `@Environment` over prop drilling
- Use `equatable()` modifier for expensive views
- Leverage `id()` modifier to control view identity
- Use `task(id:)` to cancel and restart async work
- Avoid computing expensive values in body - use `@State` or computed properties
