# Rover Simulator 

Um simulador interativo de Rover espacial controlado por uma linguagem de programação customizada (em português). Desenvolvido em Python utilizando a biblioteca Pygame, o projeto combina um interpretador léxico/sintático (Parser) com uma interface gráfica para visualizar a execução dos scripts em tempo real.

## Sobre o Projeto

O objetivo do simulador é permitir que o usuário escreva blocos de código para controlar os movimentos, repetições e tomadas de decisão de um Rover em uma malha (grid). O programa avalia o código em tempo real, indicando erros de sintaxe e permitindo a execução do algoritmo para coletar "Diskets" e desviar de obstáculos espalhados proceduralmente pelo mapa.

## Principais Funcionalidades

* **Interpretador Próprio:** Analisador léxico e sintático feito do zero para validar uma linguagem em português estruturada em blocos.
* **Editor de Código Integrado:** Interface de edição direto no simulador, com suporte a numeração de linhas, realce de erros de sintaxe em tempo real e atalhos de teclado (Ctrl+C, Ctrl+V, Ctrl+Z).
* **Paleta de Comandos Dinâmica:** Arraste e solte comandos da paleta lateral diretamente para o editor de texto.
* **Câmera Dinâmica:** O simulador acompanha o Rover automaticamente, ou permite o modo de exploração livre usando as setas do teclado.
* **Suporte Avançado a Monitores:** Adaptabilidade ao DPI (escalonamento) do Windows 10/11 e modo "Borderless" para tela cheia fluida sem quebrar resoluções nativas de outros softwares.

## Linguagem do Rover (Sintaxe)

A linguagem não é sensível a maiúsculas/minúsculas no momento da digitação (o editor converte automaticamente), mas exige espaçamento correto e chaves `{ }` para blocos de código.

### Comandos de Movimento
* `AVANCA = X` : Move o Rover `X` casas para frente.
* `RECUA = X` : Move o Rover `X` casas para trás.
* `ESQUERDA` ou `ESQUERDA = X` : Gira o Rover 90 graus para a esquerda (`X` vezes).
* `DIREITA` ou `DIREITA = X` : Gira o Rover 90 graus para a direita (`X` vezes).

### Comandos de Ação
* `EXPLORAR` : Faz o Rover explorar automaticamente uma célula vizinha que não seja um obstáculo ou que não tenha sido visitada, empilhando o caminho de retorno (backtracking).
* `DETECTA` : Simula o sensor do Rover (uso interno para debug/lógica).

### Laços de Repetição (Loops)
* `REPITA = X { [comandos] }` : Repete o bloco de código `X` vezes.
* `REPITA { [comandos] }` : Repete o bloco indefinidamente (loop infinito).
* `ENQUANTO NAO OBSTACULO { [comandos] }` : Continua executando os comandos até que haja um obstáculo na casa imediatamente à frente.

### Estruturas de Decisão (If/Else)
* `SE OBSTACULO ENTAO [comando]` : Executa o comando único à frente caso haja um obstáculo.
* `SE OBSTACULO ENTAO { [comandos] } SENAO { [comandos] }` : Executa o primeiro bloco se houver um obstáculo, caso contrário, executa o bloco do `SENAO`.

### Modificadores de Mapa
* `INFINITO` : (Deve ser colocado na linha 1). Define o mapa gerado como infinito. Sem essa flag, o Rover estará preso dentro de uma parede limite (15x10).

---

## Controles e Interface

### Modo de Edição (Editor)
* **Clique no código:** Move o cursor e edita livremente.
* **Atalhos suportados:** `Ctrl+A` (Selecionar tudo), `Ctrl+C` (Copiar), `Ctrl+X` (Recortar), `Ctrl+V` (Colar), `Ctrl+Z` (Desfazer).
* **Paleta de UI (Direita):** Clique em um bloco da direita para "pegar" o comando e clique no editor para colar.

### Modo Simulador
* **Setas Direcionais:** Movem a câmera pelo mapa livremente.
* **Barra de Espaço:** Centraliza e trava a câmera de volta no Rover.
* **Painel Superior:**
  * `Pausar / Cont.` : Interrompe a animação momentaneamente.
  * `Editor` : Abre ou fecha o editor de código.
  * `Rodar` : Salva o script atual, compila e reinicia a execução do Rover.
  * `Tela Cheia` : Alterna para o modo janela sem bordas maximizada.
  * `Regerar` : Mantém o script atual, mas recria a distribuição procedural do mapa (seed aleatória).
  * `Luz: ON/OFF` : Alterna a cor dos obstáculos e do chão para facilitar a visualização.

## Instalação e Execução

### Opção 1: Usando o Executável (.exe) - *Recomendado*
O programa foi compilado e é totalmente portátil, não exigindo a instalação do Python ou de bibliotecas extras.
1. Baixe o arquivo `interpretador.exe`.
2. Dê um duplo clique para iniciar.
*Nota: Ao abrir pela primeira vez, o Windows pode demorar cerca de 1 a 2 segundos para descompactar o ambiente de execução temporário.*

### Opção 2: Executando via Código Fonte (Python)
Se você deseja modificar o código e rodar na sua máquina, precisará do Python instalado.

1. Clone ou baixe este repositório.
2. Instale o Pygame usando o pip:
   ```bash
   pip install pygame
Execute o script principal:

Bash
python interpretador.py
(Opcionalmente, você pode passar um arquivo de texto como parâmetro: python interpretador.py script.txt)


🛠️ Tecnologias Utilizadas
Python 3

Pygame (Renderização gráfica, fonte, inputs)

Expressões Regulares (Re) (Tokenização léxica)

Ctypes (Integração com a API do Windows para DPI e Janelas Maximizadas)