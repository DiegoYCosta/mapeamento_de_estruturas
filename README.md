# Mapeamento de Estruturas de Arquivos

Este projeto fornece uma interface gráfica simples para explorar e selecionar arquivos e diretórios em uma estrutura de pastas. Ele gera um arquivo de saída contendo o conteúdo dos arquivos selecionados e copia essas informações para a área de transferência.

---

## Funcionalidades

- Exibe uma interface gráfica para seleção de arquivos e diretórios.
- Permite selecionar arquivos específicos ou diretórios inteiros.
- Gera um arquivo de saída com o conteúdo dos arquivos selecionados.
- Ignora arquivos e pastas configurados no padrão de exclusão.

---

## Requisitos

Certifique-se de ter o Python 3.7 ou superior instalado em sua máquina.

---

## Como configurar o ambiente virtual (venv)

### Passo 1: Criar o ambiente virtual
No diretório do projeto, execute o seguinte comando para criar um ambiente virtual:

```bash
python -m venv venv
```

Isso criará uma pasta chamada `venv` no diretório do projeto, que conterá uma instalação isolada do Python.

### Passo 2: Ativar o ambiente virtual

#### Windows:
```bash
venv\Scripts\activate
```

#### macOS/Linux:
```bash
source venv/bin/activate
```

Após ativar, você verá algo como `(venv)` no início do prompt de comando.

### Passo 3: Instalar as dependências
Com o ambiente virtual ativado, instale as dependências do projeto usando o arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Como rodar o projeto

Após configurar o ambiente virtual e instalar as dependências:

1. Certifique-se de que o ambiente virtual está ativado.
2. Execute o script principal com o comando:

```bash
python index.py
```

3. Use a interface gráfica exibida para selecionar a pasta desejada.

---

## Gerar executável (opcional)

Se você quiser criar um executável para facilitar a distribuição, siga as etapas abaixo:

1. Instale o `pyinstaller` no ambiente virtual:

```bash
pip install pyinstaller
```

2. Execute o comando para gerar o executável:

```bash
pyinstaller --onefile index.py
```

3. O executável será criado na pasta `dist`.

---

## Estrutura de Arquivos

```
.
├── index.py                # Código principal do projeto
├── requirements.txt        # Lista de dependências do projeto
├── Readme.md               # Este arquivo de documentação
└── .gitignore              # Arquivos e pastas ignorados pelo Git
```

---

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request.

---

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

