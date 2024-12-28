import React, { useState, useEffect } from 'react';
import { contentService } from '../services/contentService';
import { TemplateManager } from '../components/TemplateManager';
import { TemplateForm } from '../components/TemplateForm';
import { Template, CreateTemplateData } from '../types';
import { Box, useToast, Text } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';

export const Templates: React.FC = () => {
    const [templates, setTemplates] = useState<Template[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
    const toast = useToast();
    const navigate = useNavigate();

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = async () => {
        try {
            setLoading(true);
            const response = await contentService.getTemplates();
            setTemplates(response);
            setError(null);
        } catch (err) {
            setError('Erro ao carregar templates');
            console.error('Erro ao buscar templates:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateTemplate = async (template: CreateTemplateData): Promise<Template> => {
        try {
            const newTemplate = await contentService.createTemplate(template);
            await fetchTemplates();
            navigate('/templates/new');
            return newTemplate;
        } catch (err) {
            console.error('Erro ao criar template:', err);
            toast({
                title: 'Erro ao criar template',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
            throw err;
        }
    };

    const handleEditTemplate = async (template: Template): Promise<Template> => {
        try {
            const updatedTemplate = await contentService.updateTemplate(template.id, template);
            await fetchTemplates();
            navigate(`/templates/edit/${template.id}`);
            return updatedTemplate;
        } catch (err) {
            console.error('Erro ao editar template:', err);
            toast({
                title: 'Erro ao editar template',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
            throw err;
        }
    };

    const handleDeleteTemplate = async (id: number): Promise<void> => {
        if (!window.confirm('Tem certeza que deseja excluir este template?')) {
            return;
        }

        try {
            await contentService.deleteTemplate(id);
            setTemplates(templates.filter(template => template.id !== id));
            toast({
                title: 'Template excluído',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        } catch (err) {
            console.error('Erro ao excluir template:', err);
            toast({
                title: 'Erro ao excluir template',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        }
    };

    const handleSubmitTemplate = async (template: Omit<Template, 'id' | 'createdAt' | 'updatedAt'>) => {
        try {
            setLoading(true);
            if (selectedTemplate) {
                await contentService.updateTemplate(selectedTemplate.id, template);
                toast({
                    title: 'Template atualizado',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
            } else {
                await contentService.createTemplate(template);
                toast({
                    title: 'Template criado',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
            }
            await fetchTemplates();
            setIsFormOpen(false);
            setSelectedTemplate(null);
        } catch (err) {
            console.error('Erro ao salvar template:', err);
            toast({
                title: 'Erro ao salvar template',
                description: 'Tente novamente mais tarde',
                status: 'error',
                duration: 3000,
                isClosable: true,
            });
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" h="64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </Box>
        );
    }

    if (error) {
        return (
            <Box p={4} bg="red.50" rounded="md">
                <Box ml={3}>
                    <Text fontSize="sm" fontWeight="medium" color="red.800">{error}</Text>
                </Box>
            </Box>
        );
    }

    return (
        <Box>
            <Box mb={6}>
                <Box>
                    <h1 className="text-xl font-semibold text-gray-900">Templates</h1>
                    <p className="mt-2 text-sm text-gray-700">
                        Gerencie seus templates de geração de conteúdo
                    </p>
                </Box>
            </Box>

            <TemplateManager
                templates={templates}
                onCreateTemplate={handleCreateTemplate}
                onEditTemplate={handleEditTemplate}
                onDeleteTemplate={handleDeleteTemplate}
                onSelectTemplate={setSelectedTemplate}
                showGenerateButton={false}
            />

            {isFormOpen && (
                <TemplateForm
                    template={selectedTemplate}
                    onSubmit={handleSubmitTemplate}
                    onCancel={() => {
                        setIsFormOpen(false);
                        setSelectedTemplate(null);
                    }}
                />
            )}
        </Box>
    );
}; 