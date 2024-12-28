import { FC } from 'react';
import { Container, Typography, Box } from '@mui/material';

export const HomePage: FC = () => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Bem-vindo ao Gerador de Conteúdo
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Utilize nossa plataforma para criar e gerenciar templates, gerar conteúdo e acompanhar métricas.
        </Typography>
      </Box>
    </Container>
  );
}; 