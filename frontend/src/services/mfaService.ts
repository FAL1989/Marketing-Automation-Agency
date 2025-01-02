import { post, get } from './api';
import { MFASetupResponse, MFAVerifyRequest, MFAResponse } from '../types';

export const enableMFA = () => 
  post<MFASetupResponse>('/api/v1/auth/mfa/enable');

export const verifyMFA = (code: string) =>
  post<MFAResponse>('/api/v1/auth/mfa/verify', { code });

export const disableMFA = (code: string) =>
  post<MFAResponse>('/api/v1/auth/mfa/disable', { code });

export const setRecoveryEmail = (recovery_email: string) =>
  post<MFAResponse>('/api/v1/auth/mfa/recovery-email', { recovery_email });

export const resetMFAAttempts = () =>
  post<MFAResponse>('/api/v1/auth/mfa/reset-attempts');

export const getMFAStatus = () =>
  get<{ mfa_enabled: boolean }>('/api/v1/auth/mfa/status'); 