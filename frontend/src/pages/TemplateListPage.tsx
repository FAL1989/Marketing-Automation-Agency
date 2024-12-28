import { FC, useState, useEffect } from 'react';
import {
    Container,
    Box,
    Heading,
    Text,
    VStack,
    useColorModeValue,
    useToast,
    Spinner,
} from '@chakra-ui/react';
import { TemplateManager } from '../components/TemplateManager';
import { contentService } from '../services/contentService';
import { Template, CreateTemplateData } from '../types';

export const TemplateListPage: FC = () => {
    const textColor = useColorModeValue('gray.600', 'gray.300');
    const [templates, setTemplates] = useState<Template[]>([]);
    const [loading, setLoading] = useState(true);
    const toast = useToast();

    useEffect(() => {
        loadTemplates();
    }, []);

    const loadTemplates = async () => {
        try {
            setLoading(true);
            const response = await contentService.getTemplates();
            setTemplates(response);
        } catch (error) {
            toast({
                title: 'Erro ao carregar templates',
                description: 'Não foi possível carregar a lista de templates.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setLoading(false);
        }
    };

    const handleCreateTemplate = async (template: CreateTemplateData) => {
        try {
            const newTemplate = await contentService.createTemplate(template);
            setTemplates(prev => [...prev, newTemplate]);
            toast({
                title: 'Template criado',
                description: 'O template foi criado com sucesso.',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
            return newTemplate;
        } catch (error) {
            toast({
                title: 'Erro ao criar template',
                description: 'Não foi possível criar o template.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
            throw error;
        }
    };

    const handleEditTemplate = async (template: Template) => {
        try {
            const updatedTemplate = await contentService.updateTemplate(template.id, template);
            setTemplates(prev => prev.map(t => t.id === template.id ? updatedTemplate : t));
            toast({
                title: 'Template atualizado',
                description: 'O template foi atualizado com sucesso.',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
            return updatedTemplate;
        } catch (error) {
            toast({
                title: 'Erro ao atualizar template',
                description: 'Não foi possível atualizar o template.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
            throw error;
        }
    };

    const handleDeleteTemplate = async (id: number) => {
        try {
            await contentService.deleteTemplate(id);
            setTemplates(prev => prev.filter(t => t.id !== id));
            toast({
                title: 'Template excluído',
                description: 'O template foi excluído com sucesso.',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        } catch (error) {
            toast({
                title: 'Erro ao excluir template',
                description: 'Não foi possível excluir o template.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
            throw error;
        }
    };

    const handleSelectTemplate = (template: Template | null) => {
        // Implementar navegação para a página de edição do template
        if (template) {
            console.log('Template selecionado:', template);
        }
    };

    if (loading) {
        return (
            <Container maxW="container.xl" py={8}>
                <VStack spacing={6} align="stretch">
                    <Box>
                        <Heading as="h1" size="lg" mb={2}>
                            Templates
                        </Heading>
                        <Text color={textColor}>
                            Gerencie seus templates de geração de conteúdo.
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
                        Templates
                    </Heading>
                    <Text color={textColor}>
                        Gerencie seus templates de geração de conteúdo.
                    </Text>
                </Box>

                <TemplateManager
                    templates={templates}
                    onCreateTemplate={handleCreateTemplate}
                    onEditTemplate={handleEditTemplate}
                    onDeleteTemplate={handleDeleteTemplate}
                    onSelectTemplate={handleSelectTemplate}
                />
            </VStack>
        </Container>
    );
}; 