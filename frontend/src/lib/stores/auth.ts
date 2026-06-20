import { writable } from 'svelte/store';
import type { User } from '$lib/types';

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

type AuthStoreMethods = {
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
};

type AuthStore = {
  subscribe: (cb: (value: AuthState) => void) => () => void;
} & AuthStoreMethods;

function createAuthStore(): AuthStore {
  const storedUser = typeof localStorage !== 'undefined' ? localStorage.getItem('user') : null;
  const storedToken = typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;

  const { subscribe, set, update } = writable<AuthState>({
    user: storedUser ? JSON.parse(storedUser) : null,
    token: storedToken,
    isAuthenticated: !!storedToken
  });

  const methods: AuthStoreMethods = {
    login: (user: User, token: string) => {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(user));
        localStorage.setItem('token', token);
      }
      set({ user, token, isAuthenticated: true });
    },
    logout: () => {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
      set({ user: null, token: null, isAuthenticated: false });
    },
    updateUser: (user: Partial<User>) => {
      update((state) => {
        const newUser = { ...state.user, ...user } as User;
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('user', JSON.stringify(newUser));
        }
        return { ...state, user: newUser };
      });
    }
  };

  return {
    subscribe,
    ...methods
  };
}

export const auth = createAuthStore();

