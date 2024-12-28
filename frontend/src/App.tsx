import { ChakraProvider, ColorModeScript } from '@chakra-ui/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { AppRoutes } from './routes/index';
import { Layout } from './components/Layout';
import theme from './styles/theme';

export function App() {
    return (
        <ChakraProvider theme={theme}>
            <ColorModeScript initialColorMode={theme.config.initialColorMode} />
            <AuthProvider>
                <BrowserRouter>
                    <Layout>
                        <AppRoutes />
                    </Layout>
                </BrowserRouter>
            </AuthProvider>
        </ChakraProvider>
    );
}
