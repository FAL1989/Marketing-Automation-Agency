import { FC, useState } from 'react';
import {
    Box,
    Button,
    Card,
    CardBody,
    FormControl,
    FormLabel,
    Heading,
    Textarea,
    VStack,
    useToast,
    useColorModeValue,
} from '@chakra-ui/react';
import { contentService } from '../services/contentService';
import { Template } from '../types';

interface ContentGeneratorProps {
    template: Template;
}

export const ContentGenerator: FC<ContentGeneratorProps> = ({ template }) => {
    const [parameters, setParameters] = useState<Record<string, string>>({});
    const [generatedContent, setGeneratedContent] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);
    const toast = useToast();
    const bgCard = useColorModeValue('white', 'gray.700');
    const bgContent = useColorModeValue('gray.50', 'gray.700');

    const handleParameterChange = (paramName: string, value: string) => {
        setParameters(prev => ({
            ...prev,
            [paramName]: value
        }));
    };

    const handleGenerate = async () => {
        try {
            setIsLoading(true);
            const response = await contentService.generateContent(template.id, parameters);
            setGeneratedContent(response.result || '');
            toast({
                title: 'Conteúdo gerado',
                description: 'O conteúdo foi gerado com sucesso.',
                status: 'success',
                duration: 3000,
                isClosable: true,
            });
        } catch (error) {
            toast({
                title: 'Erro ao gerar conteúdo',
                description: 'Não foi possível gerar o conteúdo.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Box>
            <Card bg={bgCard} mb={6}>
                <CardBody>
                    <VStack spacing={4} align="stretch">
                        <Heading size="md">{template.name}</Heading>
                        
                        {template.parameters.map((param) => (
                            <FormControl key={param.name}>
                                <FormLabel>{param.label || param.name}</FormLabel>
                                <Textarea
                                    value={parameters[param.name] || ''}
                                    onChange={(e) => handleParameterChange(param.name, e.target.value)}
                                    placeholder={param.placeholder}
                                />
                            </FormControl>
                        ))}

                        <Button
                            colorScheme="blue"
                            onClick={handleGenerate}
                            isLoading={isLoading}
                        >
                            Gerar Conteúdo
                        </Button>
                    </VStack>
                </CardBody>
            </Card>

            {generatedContent && (
                <Card bg={bgCard}>
                    <CardBody>
                        <VStack spacing={4} align="stretch">
                            <Heading size="md">Conteúdo Gerado</Heading>
                            <Box
                                p={4}
                                borderRadius="md"
                                bg={bgContent}
                                whiteSpace="pre-wrap"
                            >
                                {generatedContent}
                            </Box>
                            <Button
                                colorScheme="green"
                                onClick={() => {
                                    navigator.clipboard.writeText(generatedContent);
                                    toast({
                                        title: 'Copiado!',
                                        description: 'O conteúdo foi copiado para a área de transferência.',
                                        status: 'success',
                                        duration: 2000,
                                        isClosable: true,
                                    });
                                }}
                            >
                                Copiar Conteúdo
                            </Button>
                        </VStack>
                    </CardBody>
                </Card>
            )}
        </Box>
    );
}; 