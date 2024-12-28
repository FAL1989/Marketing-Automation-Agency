import React from 'react';
import {
  Box,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Progress,
  type AlertStatus,
} from '@chakra-ui/react';

interface RateLimitAlertProps {
  remainingRequests: number;
  maxRequests: number;
  resetTime?: Date;
  isBlocked?: boolean;
}

export const RateLimitAlert: React.FC<RateLimitAlertProps> = ({
  remainingRequests,
  maxRequests,
  resetTime,
  isBlocked = false,
}) => {
  const percentage = (remainingRequests / maxRequests) * 100;
  const status: AlertStatus = isBlocked ? 'error' : percentage < 20 ? 'warning' : 'info';
  
  const getTimeRemaining = () => {
    if (!resetTime) return '';
    const now = new Date();
    const diff = resetTime.getTime() - now.getTime();
    const minutes = Math.ceil(diff / (1000 * 60));
    return `Reset in ${minutes} minute${minutes !== 1 ? 's' : ''}`;
  };

  return (
    <Box
      role="alert"
      aria-live={isBlocked ? 'assertive' : 'polite'}
      data-testid="rate-limit-alert"
    >
      <Alert
        status={status}
        variant="left-accent"
        borderRadius="md"
        mb={4}
      >
        <AlertIcon />
        <Box flex="1">
          <AlertTitle>
            {isBlocked ? 'Rate Limit Exceeded' : 'API Usage'}
          </AlertTitle>
          <AlertDescription display="block">
            {isBlocked ? (
              <>
                You have exceeded the rate limit. Please wait {getTimeRemaining()}.
              </>
            ) : (
              <>
                {remainingRequests} of {maxRequests} requests remaining
                {resetTime && <Box as="span" ml={2}>{getTimeRemaining()}</Box>}
              </>
            )}
          </AlertDescription>
          <Progress
            value={percentage}
            size="sm"
            mt={2}
            colorScheme={status}
            aria-label="Rate limit progress"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percentage}
          />
        </Box>
      </Alert>
    </Box>
  );
}; 