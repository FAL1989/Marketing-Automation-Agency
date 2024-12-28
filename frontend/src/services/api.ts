import axios, { AxiosRequestConfig } from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para adicionar o token nas requisições
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('@App:token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Interceptor para tratar erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('@App:token');
      localStorage.removeItem('@App:user');
    }
    
    console.error('Response error:', {
      status: error.response?.status,
      data: error.response?.data,
      error: error.message
    });
    
    return Promise.reject(error);
  }
);

export const get = <T>(url: string, config?: AxiosRequestConfig) => 
  api.get<any, T>(url, config);

export const post = <T>(url: string, data?: any, config?: AxiosRequestConfig) => 
  api.post<any, T>(url, data, config);

export const put = <T>(url: string, data: any, config?: AxiosRequestConfig) => 
  api.put<any, T>(url, data, config);

export const del = <T>(url: string, config?: AxiosRequestConfig) => 
  api.delete<any, T>(url, config);

export default api; 