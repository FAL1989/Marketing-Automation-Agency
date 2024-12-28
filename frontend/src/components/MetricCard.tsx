import { Box, Typography, Card, CardContent } from '@mui/material';
import type { MetricIcon } from '../types';

export interface MetricCardProps {
  title: string;
  value: string | number;
  icon: MetricIcon;
}

export const MetricCard = ({ title, value, icon: Icon }: MetricCardProps) => (
  <Card>
    <CardContent>
      <Box display="flex" alignItems="center" mb={2}>
        <Icon className="h-6 w-6 text-gray-500" aria-hidden={true} />
        <Typography variant="h6" component="h3" ml={1}>
          {title}
        </Typography>
      </Box>
      <Typography variant="h4" component="p">
        {value}
      </Typography>
    </CardContent>
  </Card>
); 