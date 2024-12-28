import { get, put } from './api';
import { User, UserSettings } from '../types';

export const getUser = () => get<User>('/user');

export const getUserSettings = () => get<UserSettings>('/user/settings');

export const updateUserSettings = (settings: Partial<UserSettings>) =>
  put<UserSettings>('/user/settings', settings);

export const updateUser = (data: Partial<User>) =>
  put<User>('/user', data); 