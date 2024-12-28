import { FC } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
    Box,
    Flex,
    HStack,
    Link,
    IconButton,
    Button,
    Menu,
    MenuButton,
    MenuList,
    MenuItem,
    useDisclosure,
    useColorModeValue,
    Stack,
    useColorMode,
} from '@chakra-ui/react';
import { HamburgerIcon, CloseIcon, MoonIcon, SunIcon } from '@chakra-ui/icons';
import { useAuth } from '../contexts/AuthContext';

interface NavLinkProps {
    children: React.ReactNode;
    to: string;
}

const NavLink: FC<NavLinkProps> = ({ children, to }) => (
    <Link
        as={RouterLink}
        px={2}
        py={1}
        rounded={'md'}
        _hover={{
            textDecoration: 'none',
            bg: useColorModeValue('gray.200', 'gray.700'),
        }}
        to={to}
    >
        {children}
    </Link>
);

export const Navigation: FC = () => {
    const { isOpen, onOpen, onClose } = useDisclosure();
    const { colorMode, toggleColorMode } = useColorMode();
    const { signOut } = useAuth();

    const Links = [
        { name: 'Dashboard', to: '/dashboard' },
        { name: 'Templates', to: '/templates' },
        { name: 'Gerador', to: '/generator' },
        { name: 'Histórico', to: '/history' },
        { name: 'Analytics', to: '/analytics' },
    ];

    return (
        <Box bg={useColorModeValue('white', 'gray.900')} px={4} position="fixed" w="100%" zIndex={10}>
            <Flex h={16} alignItems={'center'} justifyContent={'space-between'}>
                <IconButton
                    size={'md'}
                    icon={isOpen ? <CloseIcon /> : <HamburgerIcon />}
                    aria-label={'Open Menu'}
                    display={{ md: 'none' }}
                    onClick={isOpen ? onClose : onOpen}
                />
                <HStack spacing={8} alignItems={'center'}>
                    <Box fontWeight="bold">AI Content Generator</Box>
                    <HStack as={'nav'} spacing={4} display={{ base: 'none', md: 'flex' }}>
                        {Links.map((link) => (
                            <NavLink key={link.name} to={link.to}>{link.name}</NavLink>
                        ))}
                    </HStack>
                </HStack>
                <Flex alignItems={'center'}>
                    <Stack direction={'row'} spacing={7}>
                        <Button onClick={toggleColorMode}>
                            {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
                        </Button>

                        <Menu>
                            <MenuButton
                                as={Button}
                                rounded={'full'}
                                variant={'link'}
                                cursor={'pointer'}
                                minW={0}>
                                Perfil
                            </MenuButton>
                            <MenuList>
                                <MenuItem onClick={signOut}>Sair</MenuItem>
                            </MenuList>
                        </Menu>
                    </Stack>
                </Flex>
            </Flex>

            {isOpen ? (
                <Box pb={4} display={{ md: 'none' }}>
                    <Stack as={'nav'} spacing={4}>
                        {Links.map((link) => (
                            <NavLink key={link.name} to={link.to}>{link.name}</NavLink>
                        ))}
                    </Stack>
                </Box>
            ) : null}
        </Box>
    );
}; 