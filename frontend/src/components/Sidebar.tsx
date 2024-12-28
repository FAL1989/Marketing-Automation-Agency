import React from 'react';
import { Box, VStack, Icon, Link, Text, useColorModeValue } from '@chakra-ui/react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  FiHome,
  FiList,
  FiPlusCircle,
  FiClock,
  FiBarChart2,
} from 'react-icons/fi';

interface NavItemProps {
  to: string;
  icon: any;
  children: React.ReactNode;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  const activeBg = useColorModeValue('blue.100', 'blue.800');
  const activeColor = useColorModeValue('blue.500', 'blue.200');
  const inactiveColor = useColorModeValue('gray.600', 'gray.300');
  const hoverBg = useColorModeValue('gray.100', 'gray.700');

  return (
    <Link
      as={RouterLink}
      to={to}
      style={{ textDecoration: 'none' }}
      _focus={{ boxShadow: 'none' }}
      width="100%"
    >
      <Box
        display="flex"
        alignItems="center"
        p={3}
        borderRadius="lg"
        bg={isActive ? activeBg : 'transparent'}
        color={isActive ? activeColor : inactiveColor}
        transition="all 0.2s"
        _hover={{
          bg: isActive ? activeBg : hoverBg,
          color: isActive ? activeColor : inactiveColor,
          transform: 'translateX(4px)',
        }}
      >
        <Icon as={icon} mr={4} boxSize={5} />
        <Text fontSize="md" fontWeight={isActive ? "semibold" : "normal"}>{children}</Text>
      </Box>
    </Link>
  );
};

export const Sidebar: React.FC = () => {
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box
      as="nav"
      pos="fixed"
      top="60px"
      left="0"
      h="calc(100vh - 60px)"
      w="240px"
      bg={bg}
      borderRight="1px"
      borderColor={borderColor}
      p={4}
      transition="all 0.3s"
      shadow="md"
    >
      <VStack spacing={3} align="stretch">
        <NavItem to="/" icon={FiHome}>
          Dashboard
        </NavItem>
        <NavItem to="/templates" icon={FiList}>
          Templates
        </NavItem>
        <NavItem to="/generator" icon={FiPlusCircle}>
          Gerador
        </NavItem>
        <NavItem to="/history" icon={FiClock}>
          Histórico
        </NavItem>
        <NavItem to="/analytics" icon={FiBarChart2}>
          Analytics
        </NavItem>
      </VStack>
    </Box>
  );
}; 