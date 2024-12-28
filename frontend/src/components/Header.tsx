import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
    Box,
    Flex,
    Button,
    useColorModeValue,
    Stack,
    useColorMode,
    IconButton,
    useToast,
    Text
} from '@chakra-ui/react';
import { FiMoon, FiSun, FiLogOut } from 'react-icons/fi';

export const Header: React.FC = () => {
    const { colorMode, toggleColorMode } = useColorMode();
    const { signOut, user } = useAuth();
    const navigate = useNavigate();
    const toast = useToast();

    const bgHeader = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.700');
    const textColor = useColorModeValue('gray.800', 'white');

    const handleSignOut = () => {
        try {
            signOut();
            navigate('/login');
        } catch (err) {
            toast({
                title: 'Erro ao sair',
                description: 'Ocorreu um erro ao tentar sair da aplicação',
                status: 'error',
                duration: 5000,
                isClosable: true,
                position: 'top-right'
            });
        }
    };

    return (
        <Box
            px={4}
            bg={bgHeader}
            borderBottom={1}
            borderStyle="solid"
            borderColor={borderColor}
            position="fixed"
            top={0}
            left={0}
            right={0}
            zIndex={1}
        >
            <Flex h={16} alignItems="center" justifyContent="space-between">
                <Text fontSize="lg" fontWeight="bold" color={textColor}>
                    Sistema de Gestão
                </Text>
                <Stack direction="row" spacing={4} align="center">
                    <Text color={textColor} fontSize="sm">
                        {user?.name || user?.email}
                    </Text>
                    <IconButton
                        aria-label="Toggle color mode"
                        icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
                        onClick={toggleColorMode}
                        variant="ghost"
                        color={textColor}
                    />
                    <Button
                        leftIcon={<FiLogOut />}
                        onClick={handleSignOut}
                        variant="ghost"
                        colorScheme="red"
                    >
                        Sair
                    </Button>
                </Stack>
            </Flex>
        </Box>
    );
}; 