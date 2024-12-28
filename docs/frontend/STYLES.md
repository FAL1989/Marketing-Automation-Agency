# Guia de Estilos do Frontend

## Sistema de Design

### Cores

#### Paleta Principal
```typescript
export const colors = {
  primary: {
    main: '#007AFF',
    light: '#4DA2FF',
    dark: '#0055B3',
    contrast: '#FFFFFF'
  },
  secondary: {
    main: '#5856D6',
    light: '#7A79E0',
    dark: '#3E3D95',
    contrast: '#FFFFFF'
  },
  success: {
    main: '#34C759',
    light: '#5FD37A',
    dark: '#248B3E',
    contrast: '#FFFFFF'
  },
  error: {
    main: '#FF3B30',
    light: '#FF6259',
    dark: '#B32921',
    contrast: '#FFFFFF'
  }
}
```

#### Tons de Cinza
```typescript
export const grays = {
  50: '#F9FAFB',
  100: '#F3F4F6',
  200: '#E5E7EB',
  300: '#D1D5DB',
  400: '#9CA3AF',
  500: '#6B7280',
  600: '#4B5563',
  700: '#374151',
  800: '#1F2937',
  900: '#111827'
}
```

### Tipografia

#### Fontes
```css
--font-primary: 'Inter', sans-serif;
--font-secondary: 'SF Pro Display', sans-serif;
--font-mono: 'SF Mono', monospace;
```

#### Tamanhos
```typescript
export const typography = {
  h1: {
    fontSize: '2.5rem',    // 40px
    lineHeight: '3rem',    // 48px
    fontWeight: 700
  },
  h2: {
    fontSize: '2rem',      // 32px
    lineHeight: '2.5rem',  // 40px
    fontWeight: 600
  },
  h3: {
    fontSize: '1.5rem',    // 24px
    lineHeight: '2rem',    // 32px
    fontWeight: 600
  },
  body1: {
    fontSize: '1rem',      // 16px
    lineHeight: '1.5rem',  // 24px
    fontWeight: 400
  },
  body2: {
    fontSize: '0.875rem',  // 14px
    lineHeight: '1.25rem', // 20px
    fontWeight: 400
  },
  caption: {
    fontSize: '0.75rem',   // 12px
    lineHeight: '1rem',    // 16px
    fontWeight: 400
  }
}
```

### Espaçamento

#### Sistema de Grid
```typescript
export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px'
}

export const grid = {
  container: '1200px',
  gutter: '24px',
  columns: 12
}
```

#### Breakpoints
```typescript
export const breakpoints = {
  xs: '0px',
  sm: '600px',
  md: '960px',
  lg: '1280px',
  xl: '1920px'
}
```

### Sombras

```typescript
export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
}
```

### Bordas

```typescript
export const borders = {
  radius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px'
  },
  width: {
    thin: '1px',
    medium: '2px',
    thick: '4px'
  }
}
```

## Componentes Base

### Botões

#### Variantes
```typescript
type ButtonVariant = 'contained' | 'outlined' | 'text';
type ButtonColor = 'primary' | 'secondary' | 'success' | 'error';
type ButtonSize = 'small' | 'medium' | 'large';
```

#### Estilos
```typescript
export const buttonStyles = {
  contained: {
    primary: {
      background: colors.primary.main,
      color: colors.primary.contrast,
      hover: colors.primary.dark
    },
    // ... outros estilos
  },
  // ... outras variantes
}
```

### Inputs

#### Variantes
```typescript
type InputVariant = 'outlined' | 'filled' | 'standard';
type InputSize = 'small' | 'medium' | 'large';
```

#### Estilos
```typescript
export const inputStyles = {
  outlined: {
    border: `${borders.width.thin} solid ${grays[300]}`,
    borderRadius: borders.radius.md,
    padding: spacing.md
  },
  // ... outras variantes
}
```

### Cards

#### Variantes
```typescript
type CardVariant = 'elevated' | 'outlined' | 'filled';
```

#### Estilos
```typescript
export const cardStyles = {
  elevated: {
    background: '#FFFFFF',
    boxShadow: shadows.md,
    borderRadius: borders.radius.lg,
    padding: spacing.lg
  },
  // ... outras variantes
}
```

## Animações

### Duração
```typescript
export const duration = {
  shortest: 150,
  shorter: 200,
  short: 250,
  standard: 300,
  complex: 375,
  enteringScreen: 225,
  leavingScreen: 195
}
```

### Easing
```typescript
export const easing = {
  easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
  easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
  sharp: 'cubic-bezier(0.4, 0, 0.6, 1)'
}
```

### Transições
```typescript
export const transitions = {
  fade: {
    enter: {
      opacity: 0
    },
    enterActive: {
      opacity: 1,
      transition: `opacity ${duration.standard}ms ${easing.easeInOut}`
    },
    exit: {
      opacity: 1
    },
    exitActive: {
      opacity: 0,
      transition: `opacity ${duration.standard}ms ${easing.easeInOut}`
    }
  }
}
```

## Modo Escuro

### Paleta Dark
```typescript
export const darkColors = {
  background: {
    default: '#121212',
    paper: '#1E1E1E'
  },
  text: {
    primary: 'rgba(255, 255, 255, 0.87)',
    secondary: 'rgba(255, 255, 255, 0.60)'
  }
}
```

### Alternância de Tema
```typescript
export const getTheme = (mode: 'light' | 'dark') => ({
  palette: {
    mode,
    ...(mode === 'light' ? colors : darkColors)
  }
})
```

## Guias de Uso

### 1. Componentes Estilizados
```typescript
import styled from 'styled-components';

export const Container = styled.div`
  padding: ${({ theme }) => theme.spacing.md};
  background: ${({ theme }) => theme.palette.background.default};
  border-radius: ${({ theme }) => theme.borders.radius.md};
  box-shadow: ${({ theme }) => theme.shadows.md};
`;
```

### 2. Utilitários CSS
```typescript
export const utils = {
  flexCenter: `
    display: flex;
    align-items: center;
    justify-content: center;
  `,
  textEllipsis: `
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  `
}
```

### 3. Mixins Responsivos
```typescript
export const media = {
  up: (breakpoint: keyof typeof breakpoints) => `
    @media (min-width: ${breakpoints[breakpoint]})
  `,
  down: (breakpoint: keyof typeof breakpoints) => `
    @media (max-width: ${breakpoints[breakpoint]})
  `
}
```

## Boas Práticas

### 1. Consistência
- Usar variáveis do tema ao invés de valores hardcoded
- Manter padrão de nomeação consistente
- Seguir sistema de design estabelecido

### 2. Responsividade
- Desenvolver mobile-first
- Usar breakpoints definidos
- Testar em múltiplos dispositivos

### 3. Performance
- Minimizar uso de aninhamento CSS
- Evitar animações complexas
- Otimizar assets e imagens

### 4. Manutenibilidade
- Documentar decisões de design
- Manter componentes modulares
- Usar padrões de nomenclatura BEM 