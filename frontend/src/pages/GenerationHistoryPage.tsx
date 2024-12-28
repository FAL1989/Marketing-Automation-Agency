import { FC, useState, useEffect } from 'react';
import {
    Container,
    Box,
    Heading,
    Text,
    VStack,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Badge,
    useColorModeValue,
    Button,
    HStack,
    Select,
    useToast,
    Spinner,
} from '@chakra-ui/react';
import { contentService } from '../services/contentService';
import { Generation } from '../types';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const GenerationHistoryPage: FC = () => {
    const textColor = useColorModeValue('gray.600', 'gray.300');
    const [generations, setGenerations] = useState<Generation[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [totalPages, setTotalPages] = useState(1);
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const toast = useToast();

    useEffect(() => {
        loadGenerations();
    }, [page, statusFilter]);

    const loadGenerations = async () => {
        try {
            setLoading(true);
            const response = await contentService.getGenerations(page, pageSize);
            setGenerations(response.data);
            setTotalPages(response.totalPages);
        } catch (error) {
            toast({
                title: 'Erro ao carregar histórico',
                description: 'Não foi possível carregar o histórico de gerações.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setLoading(false);
        }
    };

    const getStatusBadge = (status: string) => {
        const props = {
            success: { colorScheme: 'green', text: 'Sucesso' },
            error: { colorScheme: 'red', text: 'Erro' },
            pending: { colorScheme: 'yellow', text: 'Pendente' },
        }[status] || { colorScheme: 'gray', text: status };

        return <Badge colorScheme={props.colorScheme}>{props.text}</Badge>;
    };

    const formatDate = (date: string) => {
        return format(new Date(date), "dd 'de' MMMM 'de' yyyy 'às' HH:mm", { locale: ptBR });
    };

    if (loading) {
        return (
            <Container maxW="container.xl" py={8}>
                <VStack spacing={6} align="stretch">
                    <Box>
                        <Heading as="h1" size="lg" mb={2}>
                            Histórico de Gerações
                        </Heading>
                        <Text color={textColor}>
                            Visualize e gerencie o histórico de conteúdos gerados.
                        </Text>
                    </Box>
                    <Box display="flex" justifyContent="center" py={8}>
                        <Spinner size="xl" />
                    </Box>
                </VStack>
            </Container>
        );
    }

    return (
        <Container maxW="container.xl" py={8}>
            <VStack spacing={6} align="stretch">
                <Box>
                    <Heading as="h1" size="lg" mb={2}>
                        Histórico de Gerações
                    </Heading>
                    <Text color={textColor}>
                        Visualize e gerencie o histórico de conteúdos gerados.
                    </Text>
                </Box>

                <HStack spacing={4}>
                    <Select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        maxW="200px"
                    >
                        <option value="all">Todos os status</option>
                        <option value="success">Sucesso</option>
                        <option value="error">Erro</option>
                        <option value="pending">Pendente</option>
                    </Select>
                </HStack>

                <Box overflowX="auto">
                    <Table variant="simple">
                        <Thead>
                            <Tr>
                                <Th>ID</Th>
                                <Th>Template</Th>
                                <Th>Status</Th>
                                <Th>Data de Criação</Th>
                                <Th>Ações</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {generations.map((generation) => (
                                <Tr key={generation.id}>
                                    <Td>{generation.id}</Td>
                                    <Td>{generation.templateId}</Td>
                                    <Td>{getStatusBadge(generation.status)}</Td>
                                    <Td>{formatDate(generation.createdAt)}</Td>
                                    <Td>
                                        <Button
                                            size="sm"
                                            colorScheme="blue"
                                            onClick={() => console.log('Ver detalhes:', generation.id)}
                                        >
                                            Ver Detalhes
                                        </Button>
                                    </Td>
                                </Tr>
                            ))}
                        </Tbody>
                    </Table>
                </Box>

                <HStack spacing={4} justify="center">
                    <Button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        isDisabled={page === 1}
                    >
                        Anterior
                    </Button>
                    <Text>Página {page} de {totalPages}</Text>
                    <Button
                        onClick={() => setPage(p => p + 1)}
                        isDisabled={page >= totalPages}
                    >
                        Próxima
                    </Button>
                </HStack>
            </VStack>
        </Container>
    );
}; 