import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

const config: ThemeConfig = {
  initialColorMode: 'light',
  useSystemColorMode: true,
};

const theme = extendTheme({
  config,
  styles: {
    global: (props: any) => ({
      body: {
        bg: props.colorMode === 'dark' ? 'gray.800' : 'white',
        color: props.colorMode === 'dark' ? 'white' : 'gray.800',
      },
    }),
  },
  colors: {
    brand: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      200: '#bae6fd',
      300: '#7dd3fc',
      400: '#38bdf8',
      500: '#0ea5e9',
      600: '#0284c7',
      700: '#0369a1',
      800: '#075985',
      900: '#0c4a6e',
    },
  },
  fonts: {
    heading: 'Inter, sans-serif',
    body: 'Inter, sans-serif',
  },
  components: {
    Button: {
      baseStyle: (props: any) => ({
        _hover: {
          bg: props.colorMode === 'dark' ? 'whiteAlpha.200' : 'blackAlpha.100',
        },
        transition: 'all 0.2s',
      }),
    },
    Card: {
      baseStyle: (props: any) => ({
        container: {
          bg: props.colorMode === 'dark' ? 'gray.700' : 'white',
          color: props.colorMode === 'dark' ? 'white' : 'gray.800',
          boxShadow: 'lg',
          borderRadius: 'lg',
          transition: 'all 0.2s ease-in-out',
          _hover: {
            transform: 'translateY(-2px)',
            boxShadow: 'xl',
          },
        },
      }),
    },
    Link: {
      baseStyle: (props: any) => ({
        transition: 'all 0.2s',
        _hover: {
          textDecoration: 'none',
          color: props.colorMode === 'dark' ? 'blue.200' : 'blue.600',
        },
      }),
    },
  },
  transitions: {
    easing: {
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
      easeOut: 'cubic-bezier(0.0, 0, 0.2, 1)',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    },
    duration: {
      ultra_fast: '0.05s',
      faster: '0.1s',
      fast: '0.2s',
      normal: '0.3s',
      slow: '0.4s',
      slower: '0.5s',
    },
  },
});

export default theme; 