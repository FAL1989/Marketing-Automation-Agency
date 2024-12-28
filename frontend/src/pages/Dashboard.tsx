import { FC } from 'react';
import {
    Container,
    Box,
    Heading,
    Text,
    SimpleGrid,
    Card,
    CardBody,
    Stat,
    StatLabel,
    StatNumber,
    StatHelpText,
    StatArrow,
    useColorModeValue,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';

export const Dashboard: FC = () => {
    const { user } = useAuth();
    const textColor = useColorModeValue('gray.600', 'gray.300');
    const bgCard = useColorModeValue('white', 'gray.700');

    return (
        <Container maxW="container.xl" py={8}>
            <Box mb={8}>
                <Heading as="h1" size="lg" mb={2}>
                    Bem-vindo, {user?.name || 'Usuário'}!
                </Heading>
                <Text color={textColor}>
                    Aqui está um resumo das suas atividades recentes.
                </Text>
            </Box>

            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
                <Card bg={bgCard}>
                    <CardBody>
                        <Stat>
                            <StatLabel>Gerações Hoje</StatLabel>
                            <StatNumber>45</StatNumber>
                            <StatHelpText>
                                <StatArrow type="increase" />
                                23.36%
                            </StatHelpText>
                        </Stat>
                    </CardBody>
                </Card>

                <Card bg={bgCard}>
                    <CardBody>
                        <Stat>
                            <StatLabel>Taxa de Sucesso</StatLabel>
                            <StatNumber>98.3%</StatNumber>
                            <StatHelpText>
                                <StatArrow type="increase" />
                                5.2%
                            </StatHelpText>
                        </Stat>
                    </CardBody>
                </Card>

                <Card bg={bgCard}>
                    <CardBody>
                        <Stat>
                            <StatLabel>Templates Ativos</StatLabel>
                            <StatNumber>12</StatNumber>
                            <StatHelpText>
                                <StatArrow type="increase" />
                                12.5%
                            </StatHelpText>
                        </Stat>
                    </CardBody>
                </Card>

                <Card bg={bgCard}>
                    <CardBody>
                        <Stat>
                            <StatLabel>Tempo Médio</StatLabel>
                            <StatNumber>2.4s</StatNumber>
                            <StatHelpText>
                                <StatArrow type="decrease" />
                                8.1%
                            </StatHelpText>
                        </Stat>
                    </CardBody>
                </Card>
            </SimpleGrid>
        </Container>
    );
}; 