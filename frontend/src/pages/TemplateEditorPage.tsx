import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Container,
    Box,
    Heading,
    Text,
    VStack,
    useColorModeValue,
    useToast,
    Spinner,
    Center,
    FormControl,
    FormLabel,
    Input,
    Textarea,
    Switch,
    Button,
    Card,
    CardBody,
    SimpleGrid,
    Select,
    IconButton,
    Flex,
    Divider
} from '@chakra-ui/react';
import { Template } from '../types';
import { contentService } from '../services/contentService';
import { AddIcon, DeleteIcon } from '@chakra-ui/icons';

export const TemplateEditorPage = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const toast = useToast();
    const bgColor = useColorModeValue('white', 'gray.800');
    const borderColor = useColorModeValue('gray.200', 'gray.600');
    
    const [template, setTemplate] = useState<Template>({
        id: 0,
        name: '',
        description: '',
        content: '',
        parameters: [],
        isPublic: false,
        isActive: true,
        createdAt: '',
        updatedAt: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (id) {
            fetchTemplate();
        }
    }, [id]);

    const fetchTemplate = async () => {
        try {
            setLoading(true);
            const fetchedTemplate = await contentService.getTemplate(Number(id));
            setTemplate(fetchedTemplate);
            setError(null);
        } catch (err) {
            console.error('Erro ao buscar template:', err);
            setError('Erro ao carregar template');
            toast({
                title: 'Erro',
                description: 'Não foi possível carregar o template',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async () => {
        try {
            setLoading(true);
            if (id) {
                await contentService.updateTemplate(Number(id), template);
                toast({
                    title: 'Sucesso',
                    description: 'Template atualizado com sucesso',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
            } else {
                await contentService.createTemplate(template);
                toast({
                    title: 'Sucesso',
                    description: 'Template criado com sucesso',
                    status: 'success',
                    duration: 3000,
                    isClosable: true,
                });
            }
            navigate('/templates');
        } catch (err) {
            console.error('Erro ao salvar template:', err);
            toast({
                title: 'Erro',
                description: 'Não foi possível salvar o template',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (field: keyof Template, value: any) => {
        setTemplate(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const addParameter = () => {
        setTemplate(prev => ({
            ...prev,
            parameters: [
                ...prev.parameters,
                {
                    name: '',
                    type: 'text',
                    description: '',
                    required: false
                }
            ]
        }));
    };

    const removeParameter = (index: number) => {
        setTemplate(prev => ({
            ...prev,
            parameters: prev.parameters.filter((_, i) => i !== index)
        }));
    };

    const updateParameter = (index: number, field: string, value: any) => {
        setTemplate(prev => ({
            ...prev,
            parameters: prev.parameters.map((param, i) => 
                i === index ? { ...param, [field]: value } : param
            )
        }));
    };

    if (loading) {
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
        <Container maxW="container.xl" py={8}>
            <VStack spacing={8} align="stretch">
                <Box>
                    <Heading as="h1" size="lg" mb={2}>
                        {id ? 'Editar Template' : 'Novo Template'}
                    </Heading>
                    <Text color={useColorModeValue('gray.600', 'gray.300')}>
                        {id ? 'Edite seu template de geração de conteúdo.' : 'Crie um novo template de geração de conteúdo.'}
                    </Text>
                </Box>

                <Card bg={bgColor} borderColor={borderColor} borderWidth="1px">
                    <CardBody>
                        <VStack spacing={6}>
                            <FormControl>
                                <FormLabel>Nome</FormLabel>
                                <Input
                                    value={template.name}
                                    onChange={(e) => handleChange('name', e.target.value)}
                                    placeholder="Nome do template"
                                />
                            </FormControl>

                            <FormControl>
                                <FormLabel>Descrição</FormLabel>
                                <Textarea
                                    value={template.description}
                                    onChange={(e) => handleChange('description', e.target.value)}
                                    placeholder="Descrição do template"
                                    rows={3}
                                />
                            </FormControl>

                            <FormControl>
                                <FormLabel>Conteúdo do Template</FormLabel>
                                <Textarea
                                    value={template.content}
                                    onChange={(e) => handleChange('content', e.target.value)}
                                    placeholder="Digite o conteúdo do template aqui..."
                                    rows={8}
                                    fontFamily="mono"
                                />
                            </FormControl>

                            <Box w="100%">
                                <Flex justify="space-between" align="center" mb={4}>
                                    <FormLabel mb={0}>Parâmetros</FormLabel>
                                    <Button
                                        leftIcon={<AddIcon />}
                                        colorScheme="blue"
                                        size="sm"
                                        onClick={addParameter}
                                    >
                                        Adicionar Parâmetro
                                    </Button>
                                </Flex>
                                
                                <VStack spacing={4} align="stretch">
                                    {template.parameters.map((param, index) => (
                                        <Card key={index} p={4} bg={useColorModeValue('gray.50', 'gray.700')}>
                                            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                                                <FormControl>
                                                    <FormLabel>Nome</FormLabel>
                                                    <Input
                                                        value={param.name}
                                                        onChange={(e) => updateParameter(index, 'name', e.target.value)}
                                                        placeholder="Nome do parâmetro"
                                                    />
                                                </FormControl>

                                                <FormControl>
                                                    <FormLabel>Tipo</FormLabel>
                                                    <Select
                                                        value={param.type}
                                                        onChange={(e) => updateParameter(index, 'type', e.target.value)}
                                                    >
                                                        <option value="text">Texto</option>
                                                        <option value="number">Número</option>
                                                        <option value="select">Seleção</option>
                                                    </Select>
                                                </FormControl>

                                                <FormControl>
                                                    <FormLabel>Descrição</FormLabel>
                                                    <Input
                                                        value={param.description}
                                                        onChange={(e) => updateParameter(index, 'description', e.target.value)}
                                                        placeholder="Descrição do parâmetro"
                                                    />
                                                </FormControl>

                                                <Flex align="center" gap={4}>
                                                    <FormControl display="flex" alignItems="center">
                                                        <FormLabel mb={0}>Obrigatório</FormLabel>
                                                        <Switch
                                                            isChecked={param.required}
                                                            onChange={(e) => updateParameter(index, 'required', e.target.checked)}
                                                        />
                                                    </FormControl>
                                                    <IconButton
                                                        aria-label="Remover parâmetro"
                                                        icon={<DeleteIcon />}
                                                        colorScheme="red"
                                                        variant="ghost"
                                                        onClick={() => removeParameter(index)}
                                                    />
                                                </Flex>
                                            </SimpleGrid>
                                        </Card>
                                    ))}
                                </VStack>
      </Box>

                            <Divider />

                            <FormControl display="flex" alignItems="center">
                                <FormLabel mb={0}>Tornar template público</FormLabel>
                                <Switch
                                    isChecked={template.isPublic}
                                    onChange={(e) => handleChange('isPublic', e.target.checked)}
                                />
                            </FormControl>

                            <Flex gap={4} justify="flex-end" w="100%">
                                <Button
                                    variant="outline"
                                    onClick={() => navigate('/templates')}
                                >
                                    Cancelar
                                </Button>
                                <Button
                                    colorScheme="blue"
                                    onClick={handleSubmit}
                                    isLoading={loading}
                                >
                                    {id ? 'Atualizar' : 'Criar'}
                                </Button>
                            </Flex>
                        </VStack>
                    </CardBody>
                </Card>
            </VStack>
    </Container>
  );
}; 