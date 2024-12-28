import { useState } from 'react';
import { useNotifications } from '../components/common/Notifications';

interface RateLimitInfo {
  remainingRequests: number;
  maxRequests: number;
  resetTime: Date | null;
  isBlocked: boolean;
}

export const useRateLimit = () => {
  const [rateLimitInfo, setRateLimitInfo] = useState<RateLimitInfo>({
    remainingRequests: 0,
    maxRequests: 0,
    resetTime: null,
    isBlocked: false,
  });

  const { addNotification } = useNotifications();

  const updateRateLimitInfo = (headers: Headers) => {
    const remaining = parseInt(headers.get('X-RateLimit-Remaining') || '0', 10);
    const limit = parseInt(headers.get('X-RateLimit-Limit') || '0', 10);
    const reset = headers.get('X-RateLimit-Reset');
    const resetTime = reset ? new Date(parseInt(reset, 10) * 1000) : null;

    setRateLimitInfo({
      remainingRequests: remaining,
      maxRequests: limit,
      resetTime,
      isBlocked: remaining === 0,
    });

    // Notificar usuário quando estiver próximo do limite
    if (remaining > 0 && remaining <= Math.ceil(limit * 0.1)) {
      addNotification({
        type: 'rate-limit',
        title: 'API Rate Limit Warning',
        message: `You have ${remaining} requests remaining. The limit will reset ${resetTime ? `at ${resetTime.toLocaleTimeString()}` : 'soon'}.`,
        duration: 5000,
      });
    }
  };

  const handleResponse = (response: Response) => {
    if (response.status === 429) {
      const resetHeader = response.headers.get('X-RateLimit-Reset');
      const resetTime = resetHeader ? new Date(parseInt(resetHeader, 10) * 1000) : null;
      
      setRateLimitInfo(prev => ({
        ...prev,
        isBlocked: true,
        resetTime,
      }));

      addNotification({
        type: 'rate-limit',
        title: 'Rate Limit Exceeded',
        message: `You have exceeded the rate limit. Please try again ${resetTime ? `after ${resetTime.toLocaleTimeString()}` : 'later'}.`,
        duration: undefined,
      });
    } else {
      updateRateLimitInfo(response.headers);
    }
  };

  return {
    rateLimitInfo,
    handleResponse,
    updateRateLimitInfo,
  };
}; 