import React, { createContext, useContext, useState, useCallback } from 'react';
import { User, AuthResponse } from '../types';
import { post } from '../services/api';

interface AuthContextData {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<AuthResponse>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextData>({} as AuthContextData);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const signIn = useCallback(async (email: string, password: string): Promise<AuthResponse> => {
    const response = await post<AuthResponse>('/api/v1/auth/login', {
      email,
      password,
    });

    if (!response.requiresMfa) {
      setUser(response.user);
      localStorage.setItem('@AIAgency:token', response.token);
    }

    return response;
  }, []);

  const signOut = useCallback(() => {
    setUser(null);
    localStorage.removeItem('@AIAgency:token');
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        signIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}; 