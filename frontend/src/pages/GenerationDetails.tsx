import { FC } from 'react';
import {
    Container,
    Box,
    Heading,
    Text,
    VStack,
    useColorModeValue
} from '@chakra-ui/react';

export const GenerationDetails: FC = () => {
    const textColor = useColorModeValue('gray.600', 'gray.300');

    return (
        <Container maxW="container.xl" py={8}>
            <VStack spacing={4} align="stretch">
                <Box>
                    <Heading as="h1" size="lg" mb={2}>
                        Detalhes da Geração
                    </Heading>
                    <Text color={textColor}>
                        Visualize os detalhes do conteúdo gerado.
                    </Text>
                </Box>
            </VStack>
        </Container>
    );
}; 