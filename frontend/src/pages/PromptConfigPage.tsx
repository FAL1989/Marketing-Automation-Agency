import { FC } from 'react';
import {
    Container,
    Box,
    Heading,
    Text,
    VStack,
    useColorModeValue
} from '@chakra-ui/react';

export const PromptConfigPage: FC = () => {
    const textColor = useColorModeValue('gray.600', 'gray.300');

    return (
        <Container maxW="container.xl" py={8}>
            <VStack spacing={4} align="stretch">
                <Box>
                    <Heading as="h1" size="lg" mb={2}>
                        Configuração de Prompts
                    </Heading>
                    <Text color={textColor}>
                        Configure os prompts para geração de conteúdo.
                    </Text>
                </Box>
            </VStack>
        </Container>
    );
}; 