# API de clientes, produtos e pedidos

Este trabalho apresenta **três APIs HTTP separadas** para demonstração: clientes, produtos e pedidos. Cada uma roda em seu próprio processo e porta, e oferece **GET, POST, PUT e DELETE**. O projeto usa Python 3.10+ e SQLite, sem pacotes externos.

A arquitetura segue **Model / DAO**: `app/models` valida e representa os dados; `app/dao` concentra o acesso ao banco; `app/server.py` implementa o HTTP. Os três processos compartilham o arquivo SQLite para que a API de pedidos possa consultar clientes e produtos criados nas outras APIs.

## Executar

Abra três terminais na raiz do projeto e execute um comando em cada terminal:

```bash
python clientes_api.py
python produtos_api.py
python pedidos_api.py
```

| API | Endereço padrão | Arquivo de entrada |
| --- | --- | --- |
| Clientes | `http://127.0.0.1:8001` | `clientes_api.py` |
| Produtos | `http://127.0.0.1:8002` | `produtos_api.py` |
| Pedidos | `http://127.0.0.1:8003` | `pedidos_api.py` |

O banco é criado automaticamente em `data/api.sqlite3`. É possível mudar host, porta e caminho do banco em cada comando:

```bash
python clientes_api.py --host 127.0.0.1 --port 9001 --database data/meu_banco.sqlite3
```

Ao mudar o banco, use o **mesmo caminho** nos três processos caso queira criar pedidos. Para encerrar uma API, pressione `Ctrl+C` no terminal correspondente.

Todos os corpos enviados devem ser objetos JSON com `Content-Type: application/json`. Os IDs são inteiros positivos. Valores monetários são **centavos inteiros**: `2590` equivale a R$ 25,90.

## Endpoints

| API e endereço | Listar | Buscar por ID | Criar | Substituir | Excluir |
| --- | --- | --- | --- | --- | --- |
| Clientes, porta `8001` | `GET /clientes` | `GET /clientes/{id}` | `POST /clientes` | `PUT /clientes/{id}` | `DELETE /clientes/{id}` |
| Produtos, porta `8002` | `GET /produtos` | `GET /produtos/{id}` | `POST /produtos` | `PUT /produtos/{id}` | `DELETE /produtos/{id}` |
| Pedidos, porta `8003` | `GET /pedidos` | `GET /pedidos/{id}` | `POST /pedidos` | `PUT /pedidos/{id}` | `DELETE /pedidos/{id}` |

Cada porta atende somente às rotas da sua API. Por exemplo, `GET http://127.0.0.1:8001/produtos` retorna `404`.

`POST` e `PUT` exigem todos os campos da tabela abaixo e rejeitam campos extras. `id` é gerado pelo servidor. `PUT` substitui todos os campos editáveis do registro.

| Recurso | Campos do corpo JSON | Resposta adicional |
| --- | --- | --- |
| Cliente | `nome` (texto não vazio, até 120 caracteres), `email` (texto, único, até 255 caracteres) | `id` |
| Produto | `nome` (texto não vazio, até 120 caracteres), `preco_centavos` (inteiro positivo) | `id` |
| Pedido | `cliente_id`, `produto_id`, `quantidade` (inteiros positivos) | `id`, `total_centavos` |

Um pedido exige cliente e produto existentes. `total_centavos` é calculado no momento da criação ou atualização como `preco_centavos × quantidade` e permanece registrado mesmo se o preço do produto mudar depois. Não é possível excluir clientes ou produtos ligados a pedidos; exclua os pedidos primeiro.

## Exemplo completo com curl

Com as três APIs em execução, crie primeiro um cliente e um produto; em seguida, crie o pedido. Estes comandos são para Bash ou terminal com `curl` disponível:

```bash
curl -i -X POST http://127.0.0.1:8001/clientes -H "Content-Type: application/json" -d '{"nome":"Ana Silva","email":"ana@example.com"}'
curl -i -X POST http://127.0.0.1:8002/produtos -H "Content-Type: application/json" -d '{"nome":"Caderno","preco_centavos":2590}'
curl -i -X POST http://127.0.0.1:8003/pedidos -H "Content-Type: application/json" -d '{"cliente_id":1,"produto_id":1,"quantidade":2}'

curl -i http://127.0.0.1:8001/clientes
curl -i http://127.0.0.1:8002/produtos/1
curl -i http://127.0.0.1:8003/pedidos/1

curl -i -X PUT http://127.0.0.1:8001/clientes/1 -H "Content-Type: application/json" -d '{"nome":"Ana Souza","email":"ana@example.com"}'
curl -i -X PUT http://127.0.0.1:8002/produtos/1 -H "Content-Type: application/json" -d '{"nome":"Caderno grande","preco_centavos":2990}'
curl -i -X PUT http://127.0.0.1:8003/pedidos/1 -H "Content-Type: application/json" -d '{"cliente_id":1,"produto_id":1,"quantidade":3}'

curl -i -X DELETE http://127.0.0.1:8003/pedidos/1
curl -i -X DELETE http://127.0.0.1:8002/produtos/1
curl -i -X DELETE http://127.0.0.1:8001/clientes/1
```

Os comandos pressupõem um banco novo e, portanto, IDs `1`. Em um banco já usado, pegue os IDs retornados pelos comandos `POST`.

No PowerShell, também é possível usar `Invoke-RestMethod`:

```powershell
$cliente = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8001/clientes' -ContentType 'application/json' -Body '{"nome":"Ana Silva","email":"ana@example.com"}'
$produto = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8002/produtos' -ContentType 'application/json' -Body '{"nome":"Caderno","preco_centavos":2590}'
$dadosPedido = @{ cliente_id = $cliente.id; produto_id = $produto.id; quantidade = 2 } | ConvertTo-Json
$pedido = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8003/pedidos' -ContentType 'application/json' -Body $dadosPedido
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8003/pedidos/$($pedido.id)"
```

A criação do pedido do exemplo retorna um objeto como `{"id":1,"cliente_id":1,"produto_id":1,"quantidade":2,"total_centavos":5180}`.

## Respostas e erros

- `200 OK`: consultas e atualizações; corpo JSON com registro ou lista.
- `201 Created`: criação; registro JSON e cabeçalho `Location`.
- `204 No Content`: exclusão bem-sucedida, sem corpo.
- `400 Bad Request`: JSON ou campos inválidos, inclusive referência a cliente/produto inexistente.
- `404 Not Found`: rota ou registro inexistente.
- `405 Method Not Allowed`: método incompatível com a rota; cabeçalho `Allow`.
- `409 Conflict`: email duplicado ou tentativa de excluir cliente/produto usado em pedido.

Erros retornam JSON no formato `{"erro":"descrição"}`, exceto o `405`, que não tem corpo.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário e não alteram `data/api.sqlite3`.
