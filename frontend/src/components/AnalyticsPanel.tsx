import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { api } from '../services/api';
import { Box, Spinner, Text, Card, useColorModeValue } from '@chakra-ui/react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export interface AnalyticsPanelProps {
  title: string;
  type: 'line' | 'bar' | 'pie';
  timeRange: 'day' | 'week' | 'month';
}

interface ChartDataResponse {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
  }[];
}

export const AnalyticsPanel: React.FC<AnalyticsPanelProps> = ({
  title,
  type,
  timeRange
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ChartDataResponse>({
    labels: [],
    datasets: []
  });

  const bgCard = useColorModeValue('white', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const gridColor = useColorModeValue('gray.200', 'gray.600');

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await api.get<ChartDataResponse>(`/analytics/chart/${type}`, {
          params: { time_range: timeRange }
        });
        setData(response.data);
      } catch (err) {
        setError('Erro ao carregar dados do gráfico');
        console.error('Erro ao carregar dados:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [type, timeRange]);

  const chartData = {
    labels: data.labels,
    datasets: data.datasets.map(dataset => ({
      ...dataset,
      backgroundColor: type === 'pie' 
        ? ['rgba(99, 102, 241, 0.7)', 'rgba(59, 130, 246, 0.7)', 'rgba(147, 51, 234, 0.7)', 'rgba(236, 72, 153, 0.7)']
        : 'rgba(99, 102, 241, 0.3)',
      borderColor: type === 'pie'
        ? ['rgb(99, 102, 241)', 'rgb(59, 130, 246)', 'rgb(147, 51, 234)', 'rgb(236, 72, 153)']
        : 'rgb(99, 102, 241)',
      borderWidth: 2,
      tension: 0.4
    }))
  };

  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: textColor,
          font: {
            family: 'Inter',
            size: 12
          }
        }
      },
      title: {
        display: true,
        text: title,
        color: textColor,
        font: {
          family: 'Inter',
          size: 16,
          weight: 'bold' as const
        }
      },
      tooltip: {
        backgroundColor: bgCard,
        titleColor: textColor,
        bodyColor: textColor,
        borderColor: gridColor,
        borderWidth: 1,
        padding: 12,
        boxPadding: 4,
        usePointStyle: true
      }
    }
  };

  const lineOptions: ChartOptions<'line'> = {
    ...baseOptions,
    scales: {
      x: {
        grid: {
          color: gridColor,
          display: true
        },
        ticks: {
          color: textColor,
          font: {
            family: 'Inter'
          }
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: gridColor,
          display: true
        },
        ticks: {
          color: textColor,
          font: {
            family: 'Inter'
          }
        }
      }
    }
  };

  const barOptions: ChartOptions<'bar'> = {
    ...baseOptions,
    scales: {
      x: {
        grid: {
          display: false
        },
        ticks: {
          color: textColor,
          font: {
            family: 'Inter'
          }
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: gridColor,
          display: true
        },
        ticks: {
          color: textColor,
          font: {
            family: 'Inter'
          }
        }
      }
    }
  };

  const pieOptions: ChartOptions<'pie'> = {
    ...baseOptions,
    cutout: '0%'
  };

  if (loading) {
    return (
      <Card bg={bgCard} p={6} h="300px">
        <Box h="100%" display="flex" alignItems="center" justifyContent="center">
          <Spinner size="xl" color="blue.500" thickness="4px" />
        </Box>
      </Card>
    );
  }

  if (error) {
    return (
      <Card bg={bgCard} p={6} h="300px">
        <Box h="100%" display="flex" alignItems="center" justifyContent="center">
          <Text color="red.500" fontSize="lg">{error}</Text>
        </Box>
      </Card>
    );
  }

  return (
    <Card bg={bgCard} p={6}>
      <Box h="300px">
        {type === 'line' && (
          <Line 
            options={lineOptions} 
            data={chartData as ChartData<'line'>} 
          />
        )}
        {type === 'bar' && (
          <Bar 
            options={barOptions} 
            data={chartData as ChartData<'bar'>} 
          />
        )}
        {type === 'pie' && (
          <Pie 
            options={pieOptions} 
            data={chartData as ChartData<'pie'>} 
          />
        )}
      </Box>
    </Card>
  );
}; 