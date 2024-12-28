import { FC, useState } from 'react';
import {
    Container,
    Box,
    Heading,
    Text,
    VStack,
    SimpleGrid,
    Select,
    useColorModeValue,
    Card,
    CardBody,
    Stat,
    StatLabel,
    StatNumber,
    StatHelpText,
    StatArrow,
} from '@chakra-ui/react';
import { AnalyticsPanel } from '../components/AnalyticsPanel';

export const Analytics: FC = () => {
    const textColor = useColorModeValue('gray.600', 'gray.300');
    const bgCard = useColorModeValue('white', 'gray.700');
    const [timeRange, setTimeRange] = useState<'day' | 'week' | 'month'>('week');

    return (
        <Container maxW="container.xl" py={8}>
            <VStack spacing={6} align="stretch">
                <Box>
                    <Heading as="h1" size="lg" mb={2}>
                        Analytics
                    </Heading>
                    <Text color={textColor}>
                        Visualize métricas e estatísticas de uso da plataforma.
                    </Text>
                </Box>

                <Box>
                    <Select
                        value={timeRange}
                        onChange={(e) => setTimeRange(e.target.value as 'day' | 'week' | 'month')}
                        maxW="200px"
                        mb={6}
                    >
                        <option value="day">Últimas 24 horas</option>
                        <option value="week">Última semana</option>
                        <option value="month">Último mês</option>
                    </Select>
                </Box>

                <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6}>
                    <Card bg={bgCard}>
                        <CardBody>
                            <Stat>
                                <StatLabel>Total de Gerações</StatLabel>
                                <StatNumber>1,234</StatNumber>
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
                                <StatLabel>Tempo Médio</StatLabel>
                                <StatNumber>2.4s</StatNumber>
                                <StatHelpText>
                                    <StatArrow type="decrease" />
                                    8.1%
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
                </SimpleGrid>

                <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
                    <AnalyticsPanel
                        title="Gerações por Período"
                        type="line"
                        timeRange={timeRange}
                    />

                    <AnalyticsPanel
                        title="Distribuição por Template"
                        type="pie"
                        timeRange={timeRange}
                    />
                </SimpleGrid>

                <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
                    <AnalyticsPanel
                        title="Taxa de Sucesso por Template"
                        type="bar"
                        timeRange={timeRange}
                    />

                    <AnalyticsPanel
                        title="Tempo Médio por Template"
                        type="bar"
                        timeRange={timeRange}
                    />
                </SimpleGrid>
            </VStack>
        </Container>
    );
}; 