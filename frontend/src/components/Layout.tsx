import { FC, ReactNode } from 'react';
import { Box, useColorModeValue } from '@chakra-ui/react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { motion } from 'framer-motion';

interface LayoutProps {
    children: ReactNode;
}

const MotionBox = motion(Box);

export const Layout: FC<LayoutProps> = ({ children }) => {
    const bg = useColorModeValue('gray.50', 'gray.900');

    return (
        <Box minH="100vh" bg={bg} transition="background-color 0.2s">
            <Header />
            <Sidebar />
            <MotionBox
                as="main"
                ml="240px"
                pt="60px"
                p={8}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                transition={{ duration: 0.3 }}
            >
                {children}
            </MotionBox>
        </Box>
    );
}; 