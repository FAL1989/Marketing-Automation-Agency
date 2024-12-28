# Guia de Gerenciamento de Templates

## Introdução
Os templates são a base do AI Agency, permitindo a criação de estruturas reutilizáveis para geração de conteúdo. Este guia fornece instruções detalhadas sobre como criar e gerenciar templates efetivamente.

## Criando Templates

### Estrutura Básica
Um template é composto por:
- **Nome**: Identificador único do template
- **Descrição**: Explicação do propósito e uso
- **Prompt**: Texto base para geração
- **Parâmetros**: Variáveis que podem ser customizadas
- **Regras de Validação**: Critérios para validar entradas

### Passo a Passo

1. **Acessando o Editor**
   - Navegue até "Templates" no menu principal
   - Clique em "Novo Template"
   - O editor será aberto em modo de criação

2. **Informações Básicas**
   - Nome: Escolha um nome descritivo
   - Descrição: Explique o propósito do template
   - Tags: Adicione palavras-chave para organização

3. **Configurando o Prompt**
   ```
   Exemplo de prompt:
   Crie um texto para {tipo_conteudo} sobre {tema}, focando em {aspectos_principais}.
   O tom deve ser {tom} e o comprimento aproximado deve ser de {comprimento} palavras.
   ```

4. **Definindo Parâmetros**
   ```json
   {
     "tipo_conteudo": {
       "type": "select",
       "options": ["artigo", "post", "email"],
       "required": true
     },
     "tema": {
       "type": "text",
       "required": true,
       "minLength": 10
     },
     "aspectos_principais": {
       "type": "array",
       "minItems": 1,
       "maxItems": 5
     }
   }
   ```

## Melhores Práticas

### Estruturação de Prompts
1. **Seja Específico**
   - Use linguagem clara e direta
   - Defina o contexto adequadamente
   - Inclua exemplos quando necessário

2. **Use Variáveis Estrategicamente**
   - Identifique pontos de customização
   - Nomeie variáveis de forma intuitiva
   - Defina valores padrão apropriados

3. **Implemente Validações**
   - Valide tipos de dados
   - Defina limites e restrições
   - Forneça mensagens de erro claras

### Exemplos Práticos

#### Template para Post de Blog
```json
{
  "name": "Post de Blog SEO",
  "description": "Template para criar posts otimizados para SEO",
  "prompt": "Crie um post de blog sobre {tema} focando nas palavras-chave {keywords}. O texto deve ter aproximadamente {comprimento} palavras e incluir {num_subtopicos} subtópicos principais. O tom deve ser {tom} e o público-alvo é {publico_alvo}.",
  "parameters": {
    "tema": {
      "type": "text",
      "required": true,
      "description": "Tema principal do post"
    },
    "keywords": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "description": "Palavras-chave principais para SEO"
    },
    "comprimento": {
      "type": "number",
      "min": 500,
      "max": 2500,
      "default": 1000,
      "description": "Número de palavras desejado"
    }
  }
}
```

#### Template para Email Marketing
```json
{
  "name": "Email Marketing Promocional",
  "description": "Template para emails promocionais",
  "prompt": "Crie um email promocional para {produto} com desconto de {desconto}%. O email deve enfatizar {beneficios} e criar urgência para a ação. Use um tom {tom} e inclua uma chamada para ação clara.",
  "parameters": {
    "produto": {
      "type": "text",
      "required": true
    },
    "desconto": {
      "type": "number",
      "min": 5,
      "max": 90
    },
    "beneficios": {
      "type": "array",
      "minItems": 2,
      "maxItems": 5
    }
  }
}
```

## Versionamento e Histórico

### Controle de Versões
- Cada alteração cria uma nova versão
- Versões são numeradas sequencialmente
- Todas as versões ficam disponíveis para uso

### Comparando Versões
1. Acesse o histórico do template
2. Selecione duas versões para comparar
3. Analise as diferenças destacadas
4. Escolha a versão mais adequada

### Rollback
- Selecione a versão desejada
- Clique em "Restaurar Versão"
- Confirme a operação
- Uma nova versão será criada baseada na restaurada

## Dicas e Truques

### Otimização de Resultados
1. **Contexto Claro**
   - Forneça informações suficientes
   - Evite ambiguidades
   - Use exemplos quando necessário

2. **Parâmetros Efetivos**
   - Limite as opções quando possível
   - Use valores padrão apropriados
   - Implemente validações relevantes

3. **Testes e Iterações**
   - Teste diferentes variações
   - Colete feedback dos usuários
   - Ajuste baseado nos resultados

### Resolução de Problemas

#### Problemas Comuns
1. **Resultados Inconsistentes**
   - Verifique a clareza do prompt
   - Ajuste os parâmetros
   - Considere adicionar mais contexto

2. **Erros de Validação**
   - Verifique as regras definidas
   - Teste diferentes inputs
   - Atualize mensagens de erro

3. **Performance**
   - Otimize o tamanho do prompt
   - Ajuste limites de tokens
   - Configure cache quando apropriado

## Recursos Adicionais

### Templates de Exemplo
- Biblioteca de templates prontos
- Casos de uso comuns
- Melhores práticas por categoria

### Documentação Relacionada
- [API de Templates](/docs/api/templates)
- [Guia de Prompts](/docs/guides/prompts)
- [Referência de Parâmetros](/docs/reference/parameters)

### Suporte
- Fórum da comunidade
- Base de conhecimento
- Suporte técnico 