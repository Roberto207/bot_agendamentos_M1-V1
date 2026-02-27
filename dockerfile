#fazer dockerfile para o backend

#imagem oficial python 3.11
FROM python:3.11

#configurando o diretório de trabalho dentro do container
WORKDIR /app

# 3️⃣ copia apenas o requirements primeiro (melhora cache),esse ponto dps do arquivo é para indicar que o arquivo está na raiz do projeto
#devemos copialo antes pq esta fora da pasta de trabalho principal (/app), se tentarmos copiar o restante do código antes, ele não vai encontrar o requirements.txt
COPY requirements.txt . 

# 4️⃣ instala dependências (com o pip install copiado dentro do container,instalamos ele)
RUN pip install --no-cache-dir -r requirements.txt 

# 5️⃣ copia o restante do código. como ja definimos o local de trabalho como /app, o ponto indica que o conteúdo do diretório atual (raiz do projeto) será copiado para dentro do container
COPY . .

#opcional,so expoe a porta pro docker que vai ser usada pela API, nesse caso a porta 8000
EXPOSE 8000 

# 6️⃣ comando para iniciar a API
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

#docker build -t nome-da-imagem .

#docker run -it -p 8000:8000 api-padrao-agendamentos
