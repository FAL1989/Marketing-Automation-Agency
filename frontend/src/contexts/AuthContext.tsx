import React, { createContext, useContext, useState, useCallback } from 'react';
import { User } from '../types';
import { api } from '../services/api';

export interface AuthContextData {
  user: User | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
  isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextData>({} as AuthContextData);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const storedUser = localStorage.getItem('@App:user');
    return storedUser ? JSON.parse(storedUser) : null;
  });

  const signIn = useCallback(async (email: string, password: string) => {
    try {
      // FastAPI OAuth2 form data format
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      const { access_token, user: userData } = response.data;

      localStorage.setItem('@App:token', access_token);
      localStorage.setItem('@App:user', JSON.stringify(userData));
      
      api.defaults.headers.common.Authorization = `Bearer ${access_token}`;
      setUser(userData);
    } catch (error: any) {
      console.error('Login error:', error.response?.data || error);
      if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail);
      } else if (error.response?.data?.message) {
        throw new Error(error.response.data.message);
      } else if (error.message) {
        throw new Error(error.message);
      } else {
        throw new Error('Falha na autenticação. Por favor, verifique suas credenciais.');
      }
    }
  }, []);

  const signOut = useCallback(() => {
    localStorage.removeItem('@App:token');
    localStorage.removeItem('@App:user');
    setUser(null);
    delete api.defaults.headers.common.Authorization;
  }, []);

  return (
    <AuthContext.Provider value={{ 
      user, 
      signIn, 
      signOut,
      isAuthenticated: !!user 
    }}>
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