# NgRx State Management

## Store Setup

```typescript
// app.config.ts
import { provideStore } from '@ngrx/store';
import { provideEffects } from '@ngrx/effects';
import { provideStoreDevtools } from '@ngrx/store-devtools';

export const appConfig: ApplicationConfig = {
  providers: [
    provideStore({
      users: usersReducer,
      products: productsReducer
    }),
    provideEffects([UsersEffects, ProductsEffects]),
    provideStoreDevtools({
      maxAge: 25,
      logOnly: !isDevMode()
    })
  ]
};
```

## Actions (Modern)

```typescript
// users.actions.ts
import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { User } from './user.model';

export const UsersActions = createActionGroup({
  source: 'Users',
  events: {
    'Load Users': emptyProps(),
    'Load Users Success': props<{ users: User[] }>(),
    'Load Users Failure': props<{ error: string }>(),

    'Add User': props<{ user: User }>(),
    'Add User Success': props<{ user: User }>(),
    'Add User Failure': props<{ error: string }>(),

    'Update User': props<{ id: string; changes: Partial<User> }>(),
    'Update User Success': props<{ user: User }>(),

    'Delete User': props<{ id: string }>(),
    'Delete User Success': props<{ id: string }>()
  }
});
```

## Reducer with Entity Adapter

```typescript
// users.reducer.ts
import { createReducer, on } from '@ngrx/store';
import { createEntityAdapter, EntityAdapter, EntityState } from '@ngrx/entity';
import { UsersActions } from './users.actions';
import { User } from './user.model';

export interface UsersState extends EntityState<User> {
  loading: boolean;
  error: string | null;
  selectedUserId: string | null;
}

export const usersAdapter: EntityAdapter<User> = createEntityAdapter<User>({
  selectId: (user: User) => user.id,
  sortComparer: (a, b) => a.name.localeCompare(b.name)
});

const initialState: UsersState = usersAdapter.getInitialState({
  loading: false,
  error: null,
  selectedUserId: null
});

export const usersReducer = createReducer(
  initialState,

  // Load users
  on(UsersActions.loadUsers, (state) => ({
    ...state,
    loading: true,
    error: null
  })),

  on(UsersActions.loadUsersSuccess, (state, { users }) =>
    usersAdapter.setAll(users, {
      ...state,
      loading: false
    })
  ),

  on(UsersActions.loadUsersFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error
  })),

  // Add user
  on(UsersActions.addUserSuccess, (state, { user }) =>
    usersAdapter.addOne(user, state)
  ),

  // Update user
  on(UsersActions.updateUserSuccess, (state, { user }) =>
    usersAdapter.updateOne(
      { id: user.id, changes: user },
      state
    )
  ),

  // Delete user
  on(UsersActions.deleteUserSuccess, (state, { id }) =>
    usersAdapter.removeOne(id, state)
  )
);
```

## Selectors

```typescript
// users.selectors.ts
import { createFeatureSelector, createSelector } from '@ngrx/store';
import { usersAdapter, UsersState } from './users.reducer';

export const selectUsersState = createFeatureSelector<UsersState>('users');

// Entity adapter selectors
const {
  selectIds,
  selectEntities,
  selectAll,
  selectTotal
} = usersAdapter.getSelectors();

export const selectUserIds = createSelector(
  selectUsersState,
  selectIds
);

export const selectUserEntities = createSelector(
  selectUsersState,
  selectEntities
);

export const selectAllUsers = createSelector(
  selectUsersState,
  selectAll
);

export const selectUsersTotal = createSelector(
  selectUsersState,
  selectTotal
);

export const selectUsersLoading = createSelector(
  selectUsersState,
  (state) => state.loading
);

export const selectUsersError = createSelector(
  selectUsersState,
  (state) => state.error
);

// Parameterized selector
export const selectUserById = (id: string) =>
  createSelector(
    selectUserEntities,
    (entities) => entities[id]
  );

// Composed selector
export const selectActiveUsers = createSelector(
  selectAllUsers,
  (users) => users.filter(user => user.isActive)
);

// Selector with multiple inputs
export const selectUserWithPosts = createSelector(
  selectUserById,
  selectAllPosts,
  (user, posts) => ({
    user,
    posts: posts.filter(post => post.userId === user?.id)
  })
);
```

## Effects

```typescript
// users.effects.ts
import { Injectable, inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, mergeMap, exhaustMap } from 'rxjs/operators';
import { of } from 'rxjs';
import { UsersService } from './users.service';
import { UsersActions } from './users.actions';

@Injectable()
export class UsersEffects {
  private actions$ = inject(Actions);
  private usersService = inject(UsersService);

  // Load users effect
  loadUsers$ = createEffect(() =>
    this.actions$.pipe(
      ofType(UsersActions.loadUsers),
      mergeMap(() =>
        this.usersService.getAll().pipe(
          map(users => UsersActions.loadUsersSuccess({ users })),
          catchError(error =>
            of(UsersActions.loadUsersFailure({ error: error.message }))
          )
        )
      )
    )
  );

  // Add user effect (exhaustMap prevents duplicate submits)
  addUser$ = createEffect(() =>
    this.actions$.pipe(
      ofType(UsersActions.addUser),
      exhaustMap(({ user }) =>
        this.usersService.create(user).pipe(
          map(createdUser => UsersActions.addUserSuccess({ user: createdUser })),
          catchError(error =>
            of(UsersActions.addUserFailure({ error: error.message }))
          )
        )
      )
    )
  );

  // Update user effect
  updateUser$ = createEffect(() =>
    this.actions$.pipe(
      ofType(UsersActions.updateUser),
      mergeMap(({ id, changes }) =>
        this.usersService.update(id, changes).pipe(
          map(user => UsersActions.updateUserSuccess({ user })),
          catchError(error =>
            of(UsersActions.loadUsersFailure({ error: error.message }))
          )
        )
      )
    )
  );

  // Delete user effect
  deleteUser$ = createEffect(() =>
    this.actions$.pipe(
      ofType(UsersActions.deleteUser),
      mergeMap(({ id }) =>
        this.usersService.delete(id).pipe(
          map(() => UsersActions.deleteUserSuccess({ id })),
          catchError(error =>
            of(UsersActions.loadUsersFailure({ error: error.message }))
          )
        )
      )
    )
  );

  // Non-dispatching effect (side effect only)
  logUserActions$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(
          UsersActions.addUserSuccess,
          UsersActions.updateUserSuccess,
          UsersActions.deleteUserSuccess
        ),
        tap(action => console.log('User action:', action))
      ),
    { dispatch: false }
  );
}
```

## Component Integration

```typescript
// users-list.component.ts
import { Component, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { UsersActions } from './store/users.actions';
import {
  selectAllUsers,
  selectUsersLoading,
  selectUsersError
} from './store/users.selectors';

@Component({
  selector: 'app-users-list',
  standalone: true,
  template: `
    @if (loading()) {
      <div>Loading...</div>
    } @else if (error(); as err) {
      <div>Error: {{ err }}</div>
    } @else {
      @for (user of users(); track user.id) {
        <div>
          {{ user.name }}
          <button (click)="onDelete(user.id)">Delete</button>
        </div>
      }
    }
  `
})
export class UsersListComponent {
  private store = inject(Store);

  // Select data as signals
  users = toSignal(this.store.select(selectAllUsers), { initialValue: [] });
  loading = toSignal(this.store.select(selectUsersLoading), { initialValue: false });
  error = toSignal(this.store.select(selectUsersError), { initialValue: null });

  ngOnInit() {
    this.store.dispatch(UsersActions.loadUsers());
  }

  onDelete(id: string) {
    this.store.dispatch(UsersActions.deleteUser({ id }));
  }
}
```

## Facade Pattern

```typescript
// users.facade.ts
@Injectable({ providedIn: 'root' })
export class UsersFacade {
  private store = inject(Store);

  // Selectors
  users$ = this.store.select(selectAllUsers);
  loading$ = this.store.select(selectUsersLoading);
  error$ = this.store.select(selectUsersError);

  // Actions
  loadUsers() {
    this.store.dispatch(UsersActions.loadUsers());
  }

  addUser(user: User) {
    this.store.dispatch(UsersActions.addUser({ user }));
  }

  updateUser(id: string, changes: Partial<User>) {
    this.store.dispatch(UsersActions.updateUser({ id, changes }));
  }

  deleteUser(id: string) {
    this.store.dispatch(UsersActions.deleteUser({ id }));
  }

  getUserById(id: string) {
    return this.store.select(selectUserById(id));
  }
}

// Usage in component
@Component({
  selector: 'app-users',
  standalone: true
})
export class UsersComponent {
  private facade = inject(UsersFacade);

  users = toSignal(this.facade.users$, { initialValue: [] });
  loading = toSignal(this.facade.loading$, { initialValue: false });

  ngOnInit() {
    this.facade.loadUsers();
  }

  onAdd(user: User) {
    this.facade.addUser(user);
  }
}
```

## Quick Reference

| Concept | Usage |
|---------|-------|
| Actions | `createActionGroup()` |
| Reducer | `createReducer()`, `on()` |
| Entity | `createEntityAdapter()` |
| Selectors | `createSelector()`, `createFeatureSelector()` |
| Effects | `createEffect()`, `ofType()` |
| Store | `inject(Store)`, `store.select()`, `store.dispatch()` |
| DevTools | `provideStoreDevtools()` |
| Testing | Mock store, marble testing |
