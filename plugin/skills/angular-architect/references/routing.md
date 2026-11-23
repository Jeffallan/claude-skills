# Angular Routing

## Routes Configuration

```typescript
// app.routes.ts
import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/home',
    pathMatch: 'full'
  },
  {
    path: 'home',
    component: HomeComponent,
    title: 'Home'
  },
  {
    path: 'users',
    loadComponent: () => import('./users/users.component').then(m => m.UsersComponent),
    title: 'Users'
  },
  {
    path: 'users/:id',
    loadComponent: () => import('./users/user-detail.component').then(m => m.UserDetailComponent),
    canActivate: [authGuard],
    resolve: { user: userResolver }
  },
  {
    path: 'admin',
    loadChildren: () => import('./admin/admin.routes').then(m => m.ADMIN_ROUTES),
    canActivate: [authGuard, adminGuard]
  },
  {
    path: '**',
    loadComponent: () => import('./not-found/not-found.component').then(m => m.NotFoundComponent),
    title: '404 Not Found'
  }
];

// app.config.ts
import { provideRouter, withComponentInputBinding } from '@angular/router';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(
      routes,
      withComponentInputBinding(),  // Bind route params to @Input()
      withViewTransitions(),        // Enable view transitions
      withPreloading(PreloadAllModules)
    )
  ]
};
```

## Lazy Loading

```typescript
// Feature routes
// admin/admin.routes.ts
import { Routes } from '@angular/router';

export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./admin-dashboard.component').then(m => m.AdminDashboardComponent)
  },
  {
    path: 'users',
    loadComponent: () => import('./admin-users.component').then(m => m.AdminUsersComponent)
  },
  {
    path: 'settings',
    loadComponent: () => import('./admin-settings.component').then(m => m.AdminSettingsComponent)
  }
];
```

## Functional Guards

```typescript
// guards/auth.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // Redirect to login with return URL
  return router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url }
  });
};

// Admin guard
export const adminGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.hasRole('admin')) {
    return true;
  }

  return router.createUrlTree(['/unauthorized']);
};

// Can deactivate (unsaved changes)
export const canDeactivateGuard: CanDeactivateFn<FormComponent> = (component) => {
  if (component.hasUnsavedChanges()) {
    return confirm('You have unsaved changes. Are you sure you want to leave?');
  }
  return true;
};
```

## Resolvers

```typescript
// resolvers/user.resolver.ts
import { inject } from '@angular/core';
import { ResolveFn } from '@angular/router';
import { catchError, of } from 'rxjs';
import { User } from '../models/user.model';
import { UsersService } from '../services/users.service';

export const userResolver: ResolveFn<User | null> = (route, state) => {
  const usersService = inject(UsersService);
  const id = route.paramMap.get('id')!;

  return usersService.getById(id).pipe(
    catchError(() => of(null))
  );
};

// Component receives resolved data
@Component({
  selector: 'app-user-detail',
  standalone: true,
  template: `
    @if (user) {
      <h1>{{ user.name }}</h1>
    } @else {
      <p>User not found</p>
    }
  `
})
export class UserDetailComponent {
  user = input<User | null>(null);  // Resolved data bound as input
}
```

## Route Parameters

```typescript
import { Component, inject, input } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-product-detail',
  standalone: true
})
export class ProductDetailComponent {
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  // Modern approach: route params as inputs
  id = input.required<string>();

  // Legacy approach: subscribe to params
  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      this.loadProduct(id);
    });

    // Query params
    this.route.queryParamMap.subscribe(params => {
      const filter = params.get('filter');
      const sort = params.get('sort');
    });
  }

  // Navigate programmatically
  goToEdit() {
    this.router.navigate(['/products', this.id(), 'edit']);
  }

  // Navigate with query params
  applyFilter(filter: string) {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { filter },
      queryParamsHandling: 'merge'  // Preserve other params
    });
  }
}
```

## Router Events

```typescript
import { Component, inject } from '@angular/core';
import { Router, NavigationStart, NavigationEnd, NavigationError } from '@angular/router';
import { filter } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true
})
export class AppComponent {
  private router = inject(Router);
  loading = signal(false);

  constructor() {
    // Show loading on navigation start
    this.router.events.pipe(
      filter(event => event instanceof NavigationStart)
    ).subscribe(() => {
      this.loading.set(true);
    });

    // Hide loading on navigation end
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe(() => {
      this.loading.set(false);
    });

    // Handle navigation errors
    this.router.events.pipe(
      filter(event => event instanceof NavigationError)
    ).subscribe((event: NavigationError) => {
      console.error('Navigation error:', event.error);
      this.loading.set(false);
    });
  }
}
```

## Child Routes & Outlets

```typescript
// Parent route with child routes
const routes: Routes = [
  {
    path: 'dashboard',
    component: DashboardComponent,
    children: [
      {
        path: 'stats',
        component: StatsComponent,
        outlet: 'panel'  // Named outlet
      },
      {
        path: 'charts',
        component: ChartsComponent,
        outlet: 'panel'
      }
    ]
  }
];

// Dashboard component template
@Component({
  template: `
    <div class="dashboard">
      <div class="main">
        <router-outlet></router-outlet>  <!-- Primary outlet -->
      </div>
      <div class="panel">
        <router-outlet name="panel"></router-outlet>  <!-- Named outlet -->
      </div>
    </div>
  `
})
export class DashboardComponent {}

// Navigate to named outlet
this.router.navigate(['/dashboard', { outlets: { panel: ['stats'] } }]);
```

## Preloading Strategies

```typescript
// Custom preloading strategy
import { Injectable } from '@angular/core';
import { PreloadingStrategy, Route } from '@angular/router';
import { Observable, of, timer } from 'rxjs';
import { mergeMap } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class CustomPreloadingStrategy implements PreloadingStrategy {
  preload(route: Route, load: () => Observable<any>): Observable<any> {
    // Only preload routes with data.preload = true
    if (route.data?.['preload']) {
      const delay = route.data?.['preloadDelay'] || 0;
      return timer(delay).pipe(
        mergeMap(() => load())
      );
    }
    return of(null);
  }
}

// Route config with preload data
const routes: Routes = [
  {
    path: 'important',
    loadChildren: () => import('./important/important.routes'),
    data: { preload: true, preloadDelay: 2000 }
  }
];

// Register in app config
provideRouter(routes, withPreloading(CustomPreloadingStrategy))
```

## Route Guards with Observables

```typescript
export const dataGuard: CanActivateFn = (route, state) => {
  const dataService = inject(DataService);
  const router = inject(Router);

  return dataService.checkAccess(route.params['id']).pipe(
    map(hasAccess => {
      if (hasAccess) {
        return true;
      }
      return router.createUrlTree(['/no-access']);
    }),
    catchError(() => {
      return of(router.createUrlTree(['/error']));
    })
  );
};
```

## Quick Reference

| Feature | Usage |
|---------|-------|
| Routes | `Routes` array in app.routes.ts |
| Lazy load | `loadComponent()`, `loadChildren()` |
| Guards | `CanActivateFn`, `CanDeactivateFn` |
| Resolvers | `ResolveFn<T>` |
| Params | `route.paramMap`, `input<T>()` |
| Query | `route.queryParamMap` |
| Navigate | `router.navigate()`, `routerLink` |
| Events | `router.events` |
| Outlets | `<router-outlet name="...">` |
| Preload | `withPreloading()` |
