import { FC, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Button,
    Container,
    FormControl,
    FormLabel,
    Input,
    Stack,
    Heading,
    Text,
    useColorModeValue,
    useToast,
    FormErrorMessage,
    Alert,
    AlertIcon,
    AlertTitle,
    AlertDescription,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';

export const Login: FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [emailError, setEmailError] = useState('');
    const [passwordError, setPasswordError] = useState('');
    const [loginError, setLoginError] = useState('');
    const navigate = useNavigate();
    const toast = useToast();
    const { signIn } = useAuth();

    const validateForm = () => {
        let isValid = true;
        setEmailError('');
        setPasswordError('');
        setLoginError('');

        if (!email) {
            setEmailError('O email é obrigatório');
            isValid = false;
        } else if (!/\S+@\S+\.\S+/.test(email)) {
            setEmailError('Email inválido');
            isValid = false;
        }

        if (!password) {
            setPasswordError('A senha é obrigatória');
            isValid = false;
        }

        return isValid;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        setIsLoading(true);
        setLoginError('');

        try {
            console.log('Tentando fazer login...');
            await signIn(email, password);
            console.log('Login bem-sucedido, redirecionando...');
            navigate('/');
        } catch (error) {
            console.error('Erro no componente Login:', error);
            const message = error instanceof Error ? error.message : 'Erro ao fazer login';
            setLoginError(message);
            toast({
                title: 'Erro no login',
                description: message,
                status: 'error',
                duration: 5000,
                isClosable: true,
                position: 'top-right'
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Container maxW="lg" py={{ base: '12', md: '24' }} px={{ base: '0', sm: '8' }}>
            <Stack spacing="8">
                <Stack spacing="6">
                    <Stack spacing={{ base: '2', md: '3' }} textAlign="center">
                        <Heading size={{ base: 'xs', md: 'sm' }}>
                            AI Content Generator
                        </Heading>
                        <Text color={useColorModeValue('gray.600', 'gray.400')}>
                            Entre com suas credenciais para acessar a plataforma
                        </Text>
                    </Stack>
                </Stack>
                <Box
                    py={{ base: '0', sm: '8' }}
                    px={{ base: '4', sm: '10' }}
                    bg={useColorModeValue('white', 'gray.700')}
                    boxShadow={{ base: 'none', sm: 'md' }}
                    borderRadius={{ base: 'none', sm: 'xl' }}
                >
                    {loginError && (
                        <Alert status="error" mb={4} borderRadius="md">
                            <AlertIcon />
                            <Box flex="1">
                                <AlertTitle>Erro no Login</AlertTitle>
                                <AlertDescription display="block">
                                    {loginError}
                                </AlertDescription>
                            </Box>
                        </Alert>
                    )}
                    <form onSubmit={handleSubmit}>
                        <Stack spacing="6">
                            <Stack spacing="5">
                                <FormControl isInvalid={!!emailError}>
                                    <FormLabel htmlFor="email">Email</FormLabel>
                                    <Input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => {
                                            setEmail(e.target.value);
                                            setEmailError('');
                                            setLoginError('');
                                        }}
                                        placeholder="seu@email.com"
                                    />
                                    <FormErrorMessage>{emailError}</FormErrorMessage>
                                </FormControl>
                                <FormControl isInvalid={!!passwordError}>
                                    <FormLabel htmlFor="password">Senha</FormLabel>
                                    <Input
                                        id="password"
                                        type="password"
                                        value={password}
                                        onChange={(e) => {
                                            setPassword(e.target.value);
                                            setPasswordError('');
                                            setLoginError('');
                                        }}
                                        placeholder="******"
                                    />
                                    <FormErrorMessage>{passwordError}</FormErrorMessage>
                                </FormControl>
                            </Stack>
                            <Button
                                type="submit"
                                colorScheme="blue"
                                size="lg"
                                fontSize="md"
                                isLoading={isLoading}
                                loadingText="Entrando..."
                            >
                                Entrar
                            </Button>
                        </Stack>
                    </form>
                </Box>
            </Stack>
        </Container>
    );
}; 