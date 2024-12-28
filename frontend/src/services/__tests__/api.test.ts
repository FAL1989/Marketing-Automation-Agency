import { vi, describe, it, expect, beforeEach } from 'vitest';
import axios, { AxiosHeaders, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { setupApi } from '../api';

vi.mock('axios', () => {
  const mockAxiosInstance = {
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  };

  return {
    default: {
      create: vi.fn(() => mockAxiosInstance)
    },
    AxiosHeaders: vi.fn().mockImplementation(function() {
      const headers = new Map();
      return {
        set: (key: string, value: string) => headers.set(key, value),
        get: (key: string) => headers.get(key),
        delete: (key: string) => headers.delete(key)
      };
    })
  };
});

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('deve criar uma instância do axios com a configuração correta', () => {
    setupApi();
    expect(axios.create).toHaveBeenCalledWith({
      baseURL: expect.any(String),
      headers: {
        'Content-Type': 'application/json'
      }
    });
  });

  it('deve configurar os interceptors', () => {
    const api = setupApi();
    expect(api.interceptors.request.use).toHaveBeenCalled();
    expect(api.interceptors.response.use).toHaveBeenCalled();
  });

  describe('Request Interceptor', () => {
    it('deve adicionar o token de autenticação quando disponível', () => {
      const token = 'test-token';
      localStorage.setItem('token', token);

      const headers = new AxiosHeaders();
      const config: InternalAxiosRequestConfig = {
        headers,
        method: 'get',
        url: '/test'
      };

      const api = setupApi();
      const requestInterceptor = (api.interceptors.request.use as jest.Mock).mock.calls[0][0];
      const result = requestInterceptor(config);

      expect(result.headers.get('Authorization')).toBe(`Bearer ${token}`);
    });

    it('não deve adicionar o token quando não disponível', () => {
      const headers = new AxiosHeaders();
      const config: InternalAxiosRequestConfig = {
        headers,
        method: 'get',
        url: '/test'
      };

      const api = setupApi();
      const requestInterceptor = (api.interceptors.request.use as jest.Mock).mock.calls[0][0];
      const result = requestInterceptor(config);

      expect(result.headers.get('Authorization')).toBeUndefined();
    });
  });

  describe('Response Interceptor', () => {
    it('deve retornar a resposta quando bem-sucedida', () => {
      const headers = new AxiosHeaders();
      const response: AxiosResponse = {
        data: 'test',
        status: 200,
        statusText: 'OK',
        headers,
        config: {
          headers
        } as InternalAxiosRequestConfig
      };

      const api = setupApi();
      const responseInterceptor = (api.interceptors.response.use as jest.Mock).mock.calls[0][0];
      const result = responseInterceptor(response);

      expect(result).toBe(response);
    });

    it('deve redirecionar para login em caso de erro 401', async () => {
      const error = {
        response: {
          status: 401
        }
      };

      const api = setupApi();
      const errorInterceptor = (api.interceptors.response.use as jest.Mock).mock.calls[0][1];
      
      await expect(async () => {
        await errorInterceptor(error);
      }).rejects.toThrowError('Não autorizado');
      
      expect(localStorage.getItem('token')).toBeNull();
    });

    it('deve rejeitar outros erros normalmente', async () => {
      const error = {
        response: {
          status: 500,
          data: { message: 'Server error' }
        }
      };

      const api = setupApi();
      const errorInterceptor = (api.interceptors.response.use as jest.Mock).mock.calls[0][1];
      
      await expect(errorInterceptor(error)).rejects.toBe(error);
    });
  });
}); 