import { FC } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell
} from 'recharts';
import { AnalyticsData } from '../types';

interface Props {
  data: AnalyticsData;
  isLoading?: boolean;
  error?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export const AdvancedMetrics: FC<Props> = ({ data, isLoading, error }) => {
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Gerações Hoje
            </Typography>
            <Typography variant="h3" color="primary">
              {data.todayGenerations}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.generationTrend > 0 ? '+' : ''}{data.generationTrend}% vs. ontem
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Taxa de Sucesso
            </Typography>
            <Typography variant="h3" color="primary">
              {data.successRate}%
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.successTrend > 0 ? '+' : ''}{data.successTrend}% vs. ontem
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={4}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Tempo Médio
            </Typography>
            <Typography variant="h3" color="primary">
              {data.avgGenerationTime}s
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {data.timeTrend > 0 ? '+' : ''}{data.timeTrend}% vs. ontem
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Gerações Diárias
            </Typography>
            <LineChart
              width={500}
              height={300}
              data={data.dailyGenerations}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" stroke="#8884d8" name="Gerações" />
            </LineChart>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Taxa de Sucesso por Template
            </Typography>
            <BarChart
              width={500}
              height={300}
              data={data.templateSuccess}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="successRate" fill="#82ca9d" name="Taxa de Sucesso (%)" />
            </BarChart>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Tempo Médio por Template
            </Typography>
            <BarChart
              width={500}
              height={300}
              data={data.templateTimes}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="avgTime" fill="#8884d8" name="Tempo Médio (s)" />
            </BarChart>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Distribuição de Erros
            </Typography>
            <PieChart width={500} height={300}>
              <Pie
                data={data.errorDistribution}
                cx={250}
                cy={150}
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="count"
              >
                {data.errorDistribution.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}; 