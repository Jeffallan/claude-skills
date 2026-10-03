# RxJS Patterns

## Essential Operators

```typescript
import { Component, inject, signal } from '@angular/core';
import {
  map, filter, switchMap, catchError,
  debounceTime, distinctUntilChanged,
  tap, shareReplay, takeUntil
} from 'rxjs/operators';
import { Subject, of, EMPTY } from 'rxjs';

@Component({
  selector: 'app-search',
  standalone: true
})
export class SearchComponent {
  private searchService = inject(SearchService);
  private destroy$ = new Subject<void>();

  searchTerm$ = new Subject<string>();
  results = signal<SearchResult[]>([]);

  ngOnInit() {
    this.searchTerm$.pipe(
      debounceTime(300),              // Wait 300ms after typing
      distinctUntilChanged(),         // Only if value changed
      filter(term => term.length > 2), // Minimum 3 characters
      tap(() => this.loading.set(true)),
      switchMap(term =>               // Cancel previous requests
        this.searchService.search(term).pipe(
          catchError(err => {
            console.error(err);
            return of([]);            // Return empty on error
          })
        )
      ),
      tap(() => this.loading.set(false)),
      takeUntil(this.destroy$)        // Auto-unsubscribe
    ).subscribe(results => this.results.set(results));
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
```

## Subject Types

```typescript
import { Subject, BehaviorSubject, ReplaySubject, AsyncSubject } from 'rxjs';

export class SubjectExamples {
  // Subject: No initial value, only emits to future subscribers
  private clickSubject = new Subject<MouseEvent>();
  click$ = this.clickSubject.asObservable();

  onClick(event: MouseEvent) {
    this.clickSubject.next(event);
  }

  // BehaviorSubject: Has initial value, emits latest value to new subscribers
  private loadingSubject = new BehaviorSubject<boolean>(false);
  loading$ = this.loadingSubject.asObservable();

  setLoading(loading: boolean) {
    this.loadingSubject.next(loading);
  }

  // ReplaySubject: Replays N previous values to new subscribers
  private activitySubject = new ReplaySubject<Activity>(3); // Last 3 activities
  activity$ = this.activitySubject.asObservable();

  // AsyncSubject: Only emits last value when completed
  private finalResultSubject = new AsyncSubject<Result>();
  finalResult$ = this.finalResultSubject.asObservable();
}
```

## Higher-Order Operators

```typescript
import { switchMap, mergeMap, concatMap, exhaustMap } from 'rxjs/operators';

export class HigherOrderExamples {
  private http = inject(HttpClient);

  // switchMap: Cancel previous, use latest (search, typeahead)
  searchUsers(term$: Observable<string>) {
    return term$.pipe(
      switchMap(term => this.http.get<User[]>(`/api/users?q=${term}`))
    );
  }

  // mergeMap: Process all concurrently (independent requests)
  uploadFiles(files: File[]) {
    return from(files).pipe(
      mergeMap(file => this.http.post('/api/upload', file))
    );
  }

  // concatMap: Process sequentially (order matters)
  processQueue(tasks: Task[]) {
    return from(tasks).pipe(
      concatMap(task => this.http.post('/api/process', task))
    );
  }

  // exhaustMap: Ignore new until current completes (prevent double-click)
  saveForm(clicks$: Observable<void>, formData: any) {
    return clicks$.pipe(
      exhaustMap(() => this.http.post('/api/save', formData))
    );
  }
}
```

## Error Handling

```typescript
import { catchError, retry, retryWhen, delay, tap } from 'rxjs/operators';
import { throwError, of, timer } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class DataService {
  private http = inject(HttpClient);

  // Retry with exponential backoff
  getData() {
    return this.http.get<Data>('/api/data').pipe(
      retryWhen(errors =>
        errors.pipe(
          mergeMap((error, index) => {
            if (index >= 3) {
              return throwError(() => error);
            }
            const delayMs = Math.pow(2, index) * 1000;
            return timer(delayMs);
          })
        )
      ),
      catchError(err => {
        console.error('Failed after retries:', err);
        return of(null); // Fallback value
      })
    );
  }

  // Catch and rethrow with context
  saveData(data: Data) {
    return this.http.post('/api/data', data).pipe(
      catchError(err => {
        if (err.status === 401) {
          // Handle auth error
          return throwError(() => new Error('Unauthorized'));
        }
        return throwError(() => err);
      })
    );
  }
}
```

## Memory Management

```typescript
import { Component, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-auto-cleanup',
  standalone: true
})
export class AutoCleanupComponent {
  private dataService = inject(DataService);
  private destroyRef = inject(DestroyRef);

  data = signal<Data[]>([]);

  constructor() {
    // Modern approach: takeUntilDestroyed
    this.dataService.getData().pipe(
      takeUntilDestroyed()  // Auto-cleanup on destroy
    ).subscribe(data => this.data.set(data));

    // Manual cleanup with DestroyRef
    const subscription = this.dataService.getUpdates().subscribe();
    this.destroyRef.onDestroy(() => subscription.unsubscribe());
  }
}

// Legacy approach (still valid)
@Component({
  selector: 'app-manual-cleanup',
  standalone: true
})
export class ManualCleanupComponent implements OnDestroy {
  private destroy$ = new Subject<void>();

  ngOnInit() {
    this.dataService.getData().pipe(
      takeUntil(this.destroy$)
    ).subscribe();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
```

## Combining Observables

```typescript
import { combineLatest, forkJoin, merge, zip } from 'rxjs';

export class CombiningExamples {
  private http = inject(HttpClient);

  // combineLatest: Emit when any source emits (latest values)
  getDashboard() {
    return combineLatest({
      user: this.http.get<User>('/api/user'),
      stats: this.http.get<Stats>('/api/stats'),
      notifications: this.http.get<Notification[]>('/api/notifications')
    }).pipe(
      map(({ user, stats, notifications }) => ({
        user,
        stats,
        notifications
      }))
    );
  }

  // forkJoin: Emit when all sources complete (like Promise.all)
  loadAllData() {
    return forkJoin({
      users: this.http.get<User[]>('/api/users'),
      products: this.http.get<Product[]>('/api/products'),
      orders: this.http.get<Order[]>('/api/orders')
    });
  }

  // merge: Emit when any source emits (flattens all)
  getActivityFeed() {
    return merge(
      this.http.get<Activity[]>('/api/recent'),
      this.http.get<Activity[]>('/api/trending')
    );
  }
}
```

## Custom Operators

```typescript
import { Observable, OperatorFunction } from 'rxjs';
import { tap } from 'rxjs/operators';

// Custom operator for logging
export function debug<T>(tag: string): OperatorFunction<T, T> {
  return (source: Observable<T>) =>
    source.pipe(
      tap({
        next: value => console.log(`[${tag}] Next:`, value),
        error: err => console.error(`[${tag}] Error:`, err),
        complete: () => console.log(`[${tag}] Complete`)
      })
    );
}

// Usage
this.http.get('/api/data').pipe(
  debug('API Call'),
  map(data => transform(data))
).subscribe();
```

## ShareReplay for Caching

```typescript
import { shareReplay } from 'rxjs/operators';

@Injectable({ providedIn: 'root' })
export class ConfigService {
  private http = inject(HttpClient);

  // Cache config, share with all subscribers
  config$ = this.http.get<Config>('/api/config').pipe(
    shareReplay({ bufferSize: 1, refCount: true })
  );

  // All components get same config without extra HTTP calls
  getConfig() {
    return this.config$;
  }
}
```

## Quick Reference

| Use Case | Operator |
|----------|----------|
| Transform values | `map`, `pluck` |
| Filter values | `filter`, `distinctUntilChanged` |
| Time-based | `debounceTime`, `throttleTime`, `delay` |
| Cancel previous | `switchMap` |
| Process all | `mergeMap` |
| Sequential | `concatMap` |
| Ignore new | `exhaustMap` |
| Combine latest | `combineLatest` |
| Wait for all | `forkJoin` |
| Error handling | `catchError`, `retry` |
| Cleanup | `takeUntilDestroyed`, `takeUntil` |
| Share result | `shareReplay` |
