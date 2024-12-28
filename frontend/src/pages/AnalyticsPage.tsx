import { FC, useState, useEffect } from 'react';
import { Container, Typography, Box, Paper, Grid, TextField } from '@mui/material';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { ptBR } from 'date-fns/locale';
import { format, subDays } from 'date-fns';
import { AnalyticsData } from '../types';
import { AdvancedMetrics } from '../components/AdvancedMetrics';
import { analyticsService } from '../services/analyticsService';
import { useNotifications } from '../hooks/useNotifications';

export const AnalyticsPage: FC = () => {
  const [metrics, setMetrics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState<Date>(subDays(new Date(), 7));
  const [endDate, setEndDate] = useState<Date>(new Date());
  const { showNotification } = useNotifications();

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await analyticsService.getMetricsByDateRange(
          format(startDate, 'yyyy-MM-dd'),
          format(endDate, 'yyyy-MM-dd')
        );
        setMetrics(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Erro ao carregar métricas';
        setError(message);
        showNotification({ type: 'error', message });
      } finally {
        setIsLoading(false);
      }
    };

    loadMetrics();
  }, [startDate, endDate, showNotification]);

  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Métricas Avançadas
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Visualize métricas detalhadas sobre o uso e desempenho do sistema.
        </Typography>

        <Paper sx={{ p: 2, mb: 4 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={5}>
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
                <DatePicker
                  label="Data Inicial"
                  value={startDate}
                  onChange={(newValue) => newValue && setStartDate(newValue)}
                  format="dd/MM/yyyy"
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      variant: 'outlined'
                    }
                  }}
                />
              </LocalizationProvider>
            </Grid>
            <Grid item xs={12} md={5}>
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
                <DatePicker
                  label="Data Final"
                  value={endDate}
                  onChange={(newValue) => newValue && setEndDate(newValue)}
                  format="dd/MM/yyyy"
                  slotProps={{
                    textField: {
                      fullWidth: true,
                      variant: 'outlined'
                    }
                  }}
                />
              </LocalizationProvider>
            </Grid>
          </Grid>
        </Paper>

        {metrics && (
          <AdvancedMetrics
            data={metrics}
            isLoading={isLoading}
            error={error || undefined}
          />
        )}
      </Box>
    </Container>
  );
}; 