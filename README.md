O APIsBR é um pacote Python para facilitar pedidos à APIs de dados do Brasil.
- [Homepage](https://github.com/G4brielMartins/APIs-BR/wiki)
- [Documentação](http://htmlpreview.github.io/?https://github.com/G4brielMartins/apis-br/blob/master/doc/apisbr/index.html)

As APIs disponibilizadas pelos orgãos brasileiros (IBGE e Dados Abertos, por exemplo), apresentam problemas:
- Modos de requisição que variam muito de API para API
- Respostas com árvores JSON convolutas
- Queries confusos pelo excesso de IDs empregados
- Entre outros...

Assim, requisitar dados se torna enviável sem antes preparar uma lista de queries. Mesmo com o auxílio de query builders, requisitar múltiplos conjuntos de dados e integrar as respostas obtidas é uma tarefa longa, principalmente quando informações de diferentes APIs são necessárias.

O APIsBR tem como objetivo padronizar o acesso a essas APIs. Ainda, métodos simples, com filtros de pesquisa integrados, agilizam a aprendizagem e fluxo de trabalho.

As APIs atualmente sendo implementadas são:  
(✓) [Dados Abertos](https://dados.gov.br/swagger-ui/index.html)  
(−) [IBGE Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)  
(−) [IBGE Agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3)  

TODO:
- Implementação de rotinas para tratar respostas inválidas do servidor
- Mais opções de filtragem e seleção de dados
- Ampliar catálogo de APIs

Sugestões de APIs para implementação e outras funcionalidades são bem vindas! Se possuir algum comentário deste tipo, por favor abra uma issue.