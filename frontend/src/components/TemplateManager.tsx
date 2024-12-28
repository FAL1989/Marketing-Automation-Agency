import { FC, useState, useEffect } from 'react';
import {
    Box,
    Button,
    Container,
    Heading,
    SimpleGrid,
    Text,
    useToast,
    Spinner,
    Center,
    Card,
    CardBody,
    CardHeader,
    CardFooter,
    Stack,
    useColorModeValue,
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalCloseButton,
} from '@chakra-ui/react';
import { Template, CreateTemplateData } from '../types';
import { AddIcon, EditIcon, DeleteIcon } from '@chakra-ui/icons';
import { useNavigate } from 'react-router-dom';
import { ContentGenerator } from './ContentGenerator';

interface TemplateManagerProps {
    templates: Template[];
    onCreateTemplate: (template: CreateTemplateData) => Promise<Template>;
    onEditTemplate: (template: Template) => Promise<Template>;
    onDeleteTemplate: (id: number) => Promise<void>;
    onSelectTemplate: (template: Template | null) => void;
    showGenerateButton?: boolean;
}

export const TemplateManager: FC<TemplateManagerProps> = ({
    templates,
    onCreateTemplate,
    onEditTemplate,
    onDeleteTemplate,
    onSelectTemplate,
    showGenerateButton = false
}): JSX.Element => {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
    const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);
    const toast = useToast();
    const navigate = useNavigate();
    const bgCard = useColorModeValue('white', 'gray.700');

    useEffect(() => {
        // Notify parent component when template selection changes
        onSelectTemplate(selectedTemplate);
    }, [selectedTemplate, onSelectTemplate]);

    const handleCreateTemplate = async () => {
        try {
            setIsLoading(true);
            setError(null);
            const newTemplate: CreateTemplateData = {
                name: 'Novo Template',
                description: 'Descrição do novo template',
                content: '',
                parameters: [],
                isPublic: false
            };
            await onCreateTemplate(newTemplate);
            navigate('/templates/new');
        } catch (err) {
            setError('Erro ao criar template');
            toast({
                title: 'Erro',
                description: 'Não foi possível criar o template',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleEditTemplate = async (id: number) => {
        try {
            setIsLoading(true);
            setError(null);
            const template = templates.find(t => t.id === id);
            if (template) {
                await onEditTemplate(template);
                navigate(`/templates/edit/${id}`);
            }
        } catch (err) {
            setError('Erro ao editar template');
            toast({
                title: 'Erro',
                description: 'Não foi possível editar o template',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteTemplate = async (id: number) => {
        try {
            setIsLoading(true);
            setError(null);
            await onDeleteTemplate(id);
            toast({
                title: 'Sucesso',
                description: 'Template excluído com sucesso',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        } catch (err) {
            setError('Erro ao excluir template');
            toast({
                title: 'Erro',
                description: 'Não foi possível excluir o template',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerateContent = (template: Template) => {
        setSelectedTemplate(template);
        setIsGenerateModalOpen(true);
    };

    if (isLoading) {
        return (
            <Center h="200px">
                <Spinner size="xl" />
            </Center>
        );
    }

    if (error) {
        return (
            <Center h="200px">
                <Text color="red.500">{error}</Text>
            </Center>
        );
    }

    return (
        <>
            <Container maxW="container.xl" py={8}>
                <Box mb={6} display="flex" justifyContent="space-between" alignItems="center">
                    <Heading size="lg">Meus Templates</Heading>
                    <Button
                        leftIcon={<AddIcon />}
                        colorScheme="blue"
                        onClick={handleCreateTemplate}
                    >
                        Novo Template
                    </Button>
                </Box>

                {templates.length === 0 ? (
                    <Card bg={bgCard}>
                        <CardBody>
                            <Center h="200px">
                                <Stack spacing={4} align="center">
                                    <Text>Nenhum template encontrado</Text>
                                    <Button
                                        colorScheme="blue"
                                        leftIcon={<AddIcon />}
                                        onClick={handleCreateTemplate}
                                    >
                                        Criar Primeiro Template
                                    </Button>
                                </Stack>
                            </Center>
                        </CardBody>
                    </Card>
                ) : (
                    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                        {templates.map((template) => (
                            <Card key={template.id} bg={bgCard}>
                                <CardHeader>
                                    <Heading size="md">{template.name}</Heading>
                                </CardHeader>
                                <CardBody>
                                    <Text noOfLines={3}>{template.description}</Text>
                                </CardBody>
                                <CardFooter justify="flex-end" gap={2}>
                                    {showGenerateButton && (
                                        <Button
                                            colorScheme="green"
                                            onClick={() => handleGenerateContent(template)}
                                            size="sm"
                                        >
                                            Gerar
                                        </Button>
                                    )}
                                    <Button
                                        leftIcon={<EditIcon />}
                                        onClick={() => handleEditTemplate(template.id)}
                                        size="sm"
                                    >
                                        Editar
                                    </Button>
                                    <Button
                                        leftIcon={<DeleteIcon />}
                                        colorScheme="red"
                                        variant="ghost"
                                        onClick={() => handleDeleteTemplate(template.id)}
                                        size="sm"
                                    >
                                        Excluir
                                    </Button>
                                </CardFooter>
                            </Card>
                        ))}
                    </SimpleGrid>
                )}
            </Container>

            <Modal
                isOpen={isGenerateModalOpen}
                onClose={() => {
                    setIsGenerateModalOpen(false);
                    setSelectedTemplate(null);
                }}
                size="xl"
            >
                <ModalOverlay />
                <ModalContent>
                    <ModalHeader>Gerar Conteúdo</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody pb={6}>
                        {selectedTemplate && (
                            <ContentGenerator template={selectedTemplate} />
                        )}
                    </ModalBody>
                </ModalContent>
            </Modal>
        </>
    );
}; 