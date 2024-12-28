import { FC, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Slider,
  TextField,
  Typography,
  Button,
  CircularProgress
} from '@mui/material';
import { PromptConfig as PromptConfigType } from '../types';
import { usePromptConfig } from '../hooks/usePromptConfig';

interface Props {
  initialConfig?: PromptConfigType;
  onSave: (config: PromptConfigType) => Promise<void>;
  isLoading?: boolean;
  error?: string;
}

export const PromptConfig: FC<Props> = ({
  initialConfig,
  onSave,
  isLoading: externalIsLoading,
  error: externalError
}) => {
  const {
    config,
    isLoading: internalIsLoading,
    error: internalError,
    loadConfig,
    updateConfig
  } = usePromptConfig();

  const isLoading = externalIsLoading || internalIsLoading;
  const error = externalError || internalError;

  useEffect(() => {
    if (!initialConfig) {
      loadConfig();
    }
  }, [initialConfig, loadConfig]);

  const handleSave = async () => {
    if (config) {
      await updateConfig(config);
      if (onSave) {
        await onSave(config);
      }
    }
  };

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

  if (!config) {
    return null;
  }

  return (
    <Card>
      <CardContent>
        <Box component="form" sx={{ '& > :not(style)': { m: 1 } }}>
          <FormControl fullWidth>
            <InputLabel>Provedor</InputLabel>
            <Select
              value={config.provider}
              label="Provedor"
              onChange={(e) => updateConfig({ ...config, provider: e.target.value })}
            >
              <MenuItem value="openai">OpenAI</MenuItem>
              <MenuItem value="anthropic">Anthropic</MenuItem>
              <MenuItem value="cohere">Cohere</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Modelo</InputLabel>
            <Select
              value={config.model}
              label="Modelo"
              onChange={(e) => updateConfig({ ...config, model: e.target.value })}
            >
              <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
              <MenuItem value="gpt-4">GPT-4</MenuItem>
              <MenuItem value="claude-2">Claude 2</MenuItem>
              <MenuItem value="command">Command</MenuItem>
            </Select>
          </FormControl>

          <Box>
            <Typography gutterBottom>Temperatura</Typography>
            <Slider
              value={config.temperature}
              min={0}
              max={1}
              step={0.1}
              onChange={(_, value) => updateConfig({ ...config, temperature: value as number })}
              valueLabelDisplay="auto"
            />
          </Box>

          <FormControl fullWidth>
            <TextField
              label="Máximo de Tokens"
              type="number"
              value={config.maxTokens}
              onChange={(e) => updateConfig({ ...config, maxTokens: Number(e.target.value) })}
            />
          </FormControl>

          <Box>
            <Typography gutterBottom>Top P</Typography>
            <Slider
              value={config.topP}
              min={0}
              max={1}
              step={0.1}
              onChange={(_, value) => updateConfig({ ...config, topP: value as number })}
              valueLabelDisplay="auto"
            />
          </Box>

          <Box>
            <Typography gutterBottom>Penalidade de Frequência</Typography>
            <Slider
              value={config.frequencyPenalty}
              min={0}
              max={2}
              step={0.1}
              onChange={(_, value) => updateConfig({ ...config, frequencyPenalty: value as number })}
              valueLabelDisplay="auto"
            />
          </Box>

          <Box>
            <Typography gutterBottom>Penalidade de Presença</Typography>
            <Slider
              value={config.presencePenalty}
              min={0}
              max={2}
              step={0.1}
              onChange={(_, value) => updateConfig({ ...config, presencePenalty: value as number })}
              valueLabelDisplay="auto"
            />
          </Box>

          <Box display="flex" justifyContent="flex-end" mt={2}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSave}
              disabled={isLoading}
            >
              {isLoading ? <CircularProgress size={24} /> : 'Salvar'}
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}; 