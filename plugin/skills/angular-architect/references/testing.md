# Angular Testing

## Component Testing

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { UserListComponent } from './user-list.component';
import { UsersService } from './users.service';
import { of } from 'rxjs';

describe('UserListComponent', () => {
  let component: UserListComponent;
  let fixture: ComponentFixture<UserListComponent>;
  let usersService: jasmine.SpyObj<UsersService>;

  const mockUsers = [
    { id: '1', name: 'John Doe', email: 'john@example.com' },
    { id: '2', name: 'Jane Smith', email: 'jane@example.com' }
  ];

  beforeEach(async () => {
    // Create spy object
    const usersServiceSpy = jasmine.createSpyObj('UsersService', ['getAll', 'delete']);

    await TestBed.configureTestingModule({
      imports: [UserListComponent],  // Standalone component
      providers: [
        { provide: UsersService, useValue: usersServiceSpy }
      ]
    }).compileComponents();

    usersService = TestBed.inject(UsersService) as jasmine.SpyObj<UsersService>;
    fixture = TestBed.createComponent(UserListComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load users on init', () => {
    usersService.getAll.and.returnValue(of(mockUsers));

    fixture.detectChanges();  // Trigger ngOnInit

    expect(usersService.getAll).toHaveBeenCalled();
    expect(component.users()).toEqual(mockUsers);
  });

  it('should display users in template', () => {
    component.users.set(mockUsers);
    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    const userElements = compiled.querySelectorAll('.user-item');

    expect(userElements.length).toBe(2);
    expect(userElements[0].textContent).toContain('John Doe');
  });

  it('should emit userSelected when user clicked', () => {
    const emitSpy = spyOn(component.userSelected, 'emit');

    component.onUserClick(mockUsers[0]);

    expect(emitSpy).toHaveBeenCalledWith(mockUsers[0]);
  });

  it('should show loading state', () => {
    component.loading.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement;
    expect(compiled.querySelector('.loading')).toBeTruthy();
  });
});
```

## Service Testing

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { UsersService } from './users.service';
import { User } from './user.model';

describe('UsersService', () => {
  let service: UsersService;
  let httpMock: HttpTestingController;

  const mockUsers: User[] = [
    { id: '1', name: 'John', email: 'john@example.com' },
    { id: '2', name: 'Jane', email: 'jane@example.com' }
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [UsersService]
    });

    service = TestBed.inject(UsersService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();  // Verify no outstanding requests
  });

  it('should fetch all users', (done) => {
    service.getAll().subscribe(users => {
      expect(users).toEqual(mockUsers);
      done();
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('GET');
    req.flush(mockUsers);
  });

  it('should create a user', (done) => {
    const newUser: User = { id: '3', name: 'Bob', email: 'bob@example.com' };

    service.create(newUser).subscribe(user => {
      expect(user).toEqual(newUser);
      done();
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(newUser);
    req.flush(newUser);
  });

  it('should handle error', (done) => {
    service.getAll().subscribe({
      next: () => fail('should have failed'),
      error: (error) => {
        expect(error.status).toBe(500);
        done();
      }
    });

    const req = httpMock.expectOne('/api/users');
    req.flush('Server error', { status: 500, statusText: 'Internal Server Error' });
  });
});
```

## RxJS Marble Testing

```typescript
import { TestScheduler } from 'rxjs/testing';
import { delay, map } from 'rxjs/operators';

describe('RxJS Operators', () => {
  let testScheduler: TestScheduler;

  beforeEach(() => {
    testScheduler = new TestScheduler((actual, expected) => {
      expect(actual).toEqual(expected);
    });
  });

  it('should map values', () => {
    testScheduler.run(({ cold, expectObservable }) => {
      const source$ = cold('--a--b--c--|', { a: 1, b: 2, c: 3 });
      const expected = '    --x--y--z--|';
      const result$ = source$.pipe(map(x => x * 10));

      expectObservable(result$).toBe(expected, { x: 10, y: 20, z: 30 });
    });
  });

  it('should delay emissions', () => {
    testScheduler.run(({ cold, expectObservable }) => {
      const source$ = cold('--a--b--|', { a: 1, b: 2 });
      const expected = '    ----a--b--|';
      const result$ = source$.pipe(delay(20));

      expectObservable(result$).toBe(expected, { a: 1, b: 2 });
    });
  });
});
```

## Testing with Signals

```typescript
import { signal } from '@angular/core';

describe('Counter Component', () => {
  it('should update signal value', () => {
    const count = signal(0);

    expect(count()).toBe(0);

    count.set(5);
    expect(count()).toBe(5);

    count.update(val => val + 1);
    expect(count()).toBe(6);
  });

  it('should compute derived value', () => {
    const count = signal(5);
    const doubled = computed(() => count() * 2);

    expect(doubled()).toBe(10);

    count.set(10);
    expect(doubled()).toBe(20);
  });
});
```

## Testing NgRx

```typescript
import { TestBed } from '@angular/core/testing';
import { provideMockStore, MockStore } from '@ngrx/store/testing';
import { UsersComponent } from './users.component';
import { selectAllUsers, selectUsersLoading } from './store/users.selectors';

describe('UsersComponent with NgRx', () => {
  let component: UsersComponent;
  let fixture: ComponentFixture<UsersComponent>;
  let store: MockStore;

  const initialState = {
    users: {
      ids: ['1', '2'],
      entities: {
        '1': { id: '1', name: 'John' },
        '2': { id: '2', name: 'Jane' }
      },
      loading: false
    }
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UsersComponent],
      providers: [
        provideMockStore({ initialState })
      ]
    }).compileComponents();

    store = TestBed.inject(MockStore);
    fixture = TestBed.createComponent(UsersComponent);
    component = fixture.componentInstance;
  });

  it('should select users from store', () => {
    store.overrideSelector(selectAllUsers, [
      { id: '1', name: 'John' },
      { id: '2', name: 'Jane' }
    ]);

    fixture.detectChanges();

    expect(component.users().length).toBe(2);
  });

  it('should dispatch action on delete', () => {
    const dispatchSpy = spyOn(store, 'dispatch');

    component.onDelete('1');

    expect(dispatchSpy).toHaveBeenCalledWith(
      UsersActions.deleteUser({ id: '1' })
    );
  });
});
```

## Testing Effects

```typescript
import { TestBed } from '@angular/core/testing';
import { provideMockActions } from '@ngrx/effects/testing';
import { Observable, of, throwError } from 'rxjs';
import { UsersEffects } from './users.effects';
import { UsersService } from './users.service';
import { UsersActions } from './users.actions';
import { hot, cold } from 'jasmine-marbles';

describe('UsersEffects', () => {
  let actions$: Observable<any>;
  let effects: UsersEffects;
  let usersService: jasmine.SpyObj<UsersService>;

  beforeEach(() => {
    const usersServiceSpy = jasmine.createSpyObj('UsersService', ['getAll']);

    TestBed.configureTestingModule({
      providers: [
        UsersEffects,
        provideMockActions(() => actions$),
        { provide: UsersService, useValue: usersServiceSpy }
      ]
    });

    effects = TestBed.inject(UsersEffects);
    usersService = TestBed.inject(UsersService) as jasmine.SpyObj<UsersService>;
  });

  it('should load users successfully', () => {
    const users = [{ id: '1', name: 'John' }];
    const action = UsersActions.loadUsers();
    const outcome = UsersActions.loadUsersSuccess({ users });

    actions$ = hot('-a', { a: action });
    const response = cold('-b|', { b: users });
    const expected = cold('--c', { c: outcome });

    usersService.getAll.and.returnValue(response);

    expect(effects.loadUsers$).toBeObservable(expected);
  });

  it('should handle load users failure', () => {
    const action = UsersActions.loadUsers();
    const error = new Error('Failed to load');
    const outcome = UsersActions.loadUsersFailure({ error: error.message });

    actions$ = hot('-a', { a: action });
    const response = cold('-#|', {}, error);
    const expected = cold('--c', { c: outcome });

    usersService.getAll.and.returnValue(response);

    expect(effects.loadUsers$).toBeObservable(expected);
  });
});
```

## Testing Guards

```typescript
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('authGuard', () => {
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    const authServiceSpy = jasmine.createSpyObj('AuthService', ['isAuthenticated']);
    const routerSpy = jasmine.createSpyObj('Router', ['createUrlTree']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy }
      ]
    });

    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    router = TestBed.inject(Router) as jasmine.SpyObj<Router>;
  });

  it('should allow access when authenticated', () => {
    authService.isAuthenticated.and.returnValue(true);

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as any, {} as any)
    );

    expect(result).toBe(true);
  });

  it('should redirect when not authenticated', () => {
    authService.isAuthenticated.and.returnValue(false);
    const urlTree = {} as any;
    router.createUrlTree.and.returnValue(urlTree);

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as any, { url: '/protected' } as any)
    );

    expect(result).toBe(urlTree);
    expect(router.createUrlTree).toHaveBeenCalledWith(
      ['/login'],
      { queryParams: { returnUrl: '/protected' } }
    );
  });
});
```

## Quick Reference

| Test Type | Key Tools |
|-----------|-----------|
| Component | `TestBed`, `ComponentFixture`, `detectChanges()` |
| Service | `HttpClientTestingModule`, `HttpTestingController` |
| RxJS | `TestScheduler`, marble diagrams |
| NgRx Store | `provideMockStore`, `MockStore` |
| Effects | `provideMockActions`, jasmine-marbles |
| Guards | `TestBed.runInInjectionContext()` |
| Signals | Direct value checks with `()` |
| Spies | `jasmine.createSpyObj()`, `spyOn()` |
