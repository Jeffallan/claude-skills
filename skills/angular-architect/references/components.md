# Standalone Components & Signals

## Standalone Component Pattern

```typescript
import { Component, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './user-profile.component.html',
  styleUrl: './user-profile.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserProfileComponent {
  // Signal-based state
  count = signal(0);
  doubleCount = computed(() => this.count() * 2);

  constructor() {
    // Side effects
    effect(() => {
      console.log(`Count is: ${this.count()}`);
    });
  }

  increment() {
    this.count.update(value => value + 1);
  }
}
```

## Input/Output with Signals

```typescript
import { Component, input, output, model } from '@angular/core';

@Component({
  selector: 'app-search-box',
  standalone: true,
  template: `
    <input
      [value]="query()"
      (input)="onQueryChange($event)"
      [placeholder]="placeholder()" />
  `
})
export class SearchBoxComponent {
  // Signal inputs (Angular 17.1+)
  placeholder = input<string>('Search...');
  initialQuery = input<string>('');

  // Signal outputs
  queryChange = output<string>();

  // Two-way binding with model signal
  query = model<string>('');

  onQueryChange(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.query.set(value);
    this.queryChange.emit(value);
  }
}

// Parent usage
@Component({
  template: `
    <app-search-box
      [(query)]="searchQuery"
      [placeholder]="'Find users...'"
      (queryChange)="onSearch($event)" />
  `
})
export class ParentComponent {
  searchQuery = signal('');

  onSearch(query: string) {
    console.log('Searching:', query);
  }
}
```

## Smart vs Dumb Components

```typescript
// Smart Component (Container)
@Component({
  selector: 'app-users-container',
  standalone: true,
  imports: [UserListComponent],
  template: `
    <app-user-list
      [users]="users()"
      [loading]="loading()"
      (userSelected)="onUserSelected($event)" />
  `
})
export class UsersContainerComponent {
  private usersService = inject(UsersService);

  users = signal<User[]>([]);
  loading = signal(true);

  constructor() {
    effect(() => {
      this.usersService.getUsers().subscribe({
        next: users => {
          this.users.set(users);
          this.loading.set(false);
        },
        error: err => console.error(err)
      });
    });
  }

  onUserSelected(user: User) {
    // Handle business logic
  }
}

// Dumb Component (Presentational)
@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (loading()) {
      <div>Loading...</div>
    } @else {
      @for (user of users(); track user.id) {
        <div (click)="userSelected.emit(user)">
          {{ user.name }}
        </div>
      }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class UserListComponent {
  users = input.required<User[]>();
  loading = input<boolean>(false);
  userSelected = output<User>();
}
```

## Content Projection

```typescript
// Card component with multiple slots
@Component({
  selector: 'app-card',
  standalone: true,
  template: `
    <div class="card">
      <div class="card-header">
        <ng-content select="[header]"></ng-content>
      </div>
      <div class="card-body">
        <ng-content></ng-content>
      </div>
      <div class="card-footer">
        <ng-content select="[footer]"></ng-content>
      </div>
    </div>
  `
})
export class CardComponent {}

// Usage
@Component({
  template: `
    <app-card>
      <h2 header>Card Title</h2>
      <p>Card content goes here</p>
      <button footer>Action</button>
    </app-card>
  `
})
export class ParentComponent {}
```

## Dependency Injection

```typescript
import { Component, inject } from '@angular/core';
import { UserService } from './user.service';

@Component({
  selector: 'app-user-dashboard',
  standalone: true
})
export class UserDashboardComponent {
  // Modern inject() API
  private userService = inject(UserService);
  private router = inject(Router);

  // Optional dependency
  private logger = inject(LoggerService, { optional: true });

  users = signal<User[]>([]);

  ngOnInit() {
    this.loadUsers();
  }

  loadUsers() {
    this.userService.getUsers().subscribe({
      next: users => this.users.set(users),
      error: err => this.logger?.error('Failed to load users', err)
    });
  }
}
```

## New Control Flow (@if, @for)

```typescript
@Component({
  template: `
    <!-- @if instead of *ngIf -->
    @if (user(); as currentUser) {
      <div>Hello, {{ currentUser.name }}</div>
    } @else if (loading()) {
      <div>Loading...</div>
    } @else {
      <div>Please log in</div>
    }

    <!-- @for instead of *ngFor -->
    @for (item of items(); track item.id) {
      <div>{{ item.name }}</div>
    } @empty {
      <div>No items found</div>
    }

    <!-- @switch instead of *ngSwitch -->
    @switch (status()) {
      @case ('pending') {
        <span>Pending...</span>
      }
      @case ('success') {
        <span>Success!</span>
      }
      @default {
        <span>Unknown</span>
      }
    }
  `
})
export class ModernControlFlowComponent {
  user = signal<User | null>(null);
  loading = signal(false);
  items = signal<Item[]>([]);
  status = signal<'pending' | 'success' | 'error'>('pending');
}
```

## Performance: OnPush & TrackBy

```typescript
@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    @for (product of products(); track trackByProductId($index, product)) {
      <app-product-card [product]="product" />
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ProductListComponent {
  products = input.required<Product[]>();

  // TrackBy for optimal rendering
  trackByProductId(index: number, product: Product): number {
    return product.id;
  }
}
```

## Quick Reference

| Pattern | Angular 17+ Approach |
|---------|---------------------|
| Component | Standalone by default |
| State | Signals (`signal()`, `computed()`) |
| Input | `input()`, `input.required()` |
| Output | `output<T>()` |
| Two-way | `model<T>()` |
| DI | `inject()` function |
| Control Flow | `@if`, `@for`, `@switch` |
| Change Detection | `ChangeDetectionStrategy.OnPush` |
