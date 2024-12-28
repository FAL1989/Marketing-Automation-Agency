import { FC, useState, useEffect } from 'react';
import { Container, Heading, Text, Box, useToast } from '@chakra-ui/react';
import { TemplateManager } from '../components/TemplateManager';
import { Template, CreateTemplateData } from '../types';
import { contentService } from '../services/contentService';

export const ContentGeneratorPage: FC = () => {
    const [templates, setTemplates] = useState<Template[]>([]);
    const toast = useToast();

    useEffect(() => {
        loadTemplates();
    }, []);

    const loadTemplates = async () => {
        try {
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
        }
    };

    const handleCreateTemplate = async (template: CreateTemplateData) => {
        try {
            const newTemplate = await contentService.createTemplate(template);
            setTemplates(prev => [...prev, newTemplate]);
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
        // Implementar lógica de seleção se necessário
        console.log('Template selecionado:', template);
    };

    return (
        <Container maxW="container.xl" py={8}>
            <Box mb={8}>
                <Heading size="lg" mb={2}>
                    Gerador de Conteúdo
                </Heading>
                <Text color="gray.600">
                    Selecione um template e gere conteúdo personalizado.
                </Text>
            </Box>
            
            <TemplateManager
                templates={templates}
                onCreateTemplate={handleCreateTemplate}
                onEditTemplate={handleEditTemplate}
                onDeleteTemplate={handleDeleteTemplate}
                onSelectTemplate={handleSelectTemplate}
                showGenerateButton={true}
            />
        </Container>
    );
}; 