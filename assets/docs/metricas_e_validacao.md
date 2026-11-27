Estratégia de validação

1. Conjunto de teste com referência. São 20 perguntas, cada uma com o artigo correto (o ground truth), de três tipos:

15 factuais;
3 interpretativas;
2 fora do âmbito, para testar se o sistema recusa.

2. Avaliação em dois níveis separados: recuperação e geração. Assim sabe-se onde nasce cada erro. Foi esta separação que mostrou que 3 das 4 falhas do RAG não vinham da recuperação, mas do LLM.

3. Comparações controladas: muda-se uma só variável de cada vez.

QI1 (com RAG contra sem RAG): mesmas perguntas, mesmo LLM (Llama 3.1 8B) e mesma temperatura (0,1). Só muda a existência de contexto.
QI2 (por artigo contra tamanho fixo): mesmo modelo de embeddings (BGE-M3), mesmo k = 5 e mesma distância (cosseno). Só muda a forma de cortar o texto.
Métricas de recuperação
Métrica	Porquê esta
Hit@5	O LLM recebe exatamente 5 excertos. Se o artigo certo não estiver entre eles, o LLM não tem como responder bem. Por isso, o Hit@5 mede diretamente se o sistema "deu ao LLM o que ele precisa".
MRR	A ordem também conta: um artigo em 1.º lugar é mais útil do que em 5.º, porque fica no início do contexto. O MRR distingue estes casos e o Hit@5 não.
Porque não precisão/recall	Cada pergunta tem só 1 ou 2 artigos certos. O Recall@5 seria praticamente igual ao Hit@5, e a Precisão@5 nunca passaria de 0,2–0,4. Nenhuma das duas acrescentaria informação.
Métricas de geração

Avaliação manual de cada resposta segundo três critérios:

Correção: a resposta está certa face ao texto da CRP?
Citação: indica o artigo certo?
Alucinação: inventou texto, artigos ou factos?

Nas perguntas fora do âmbito, o que se mede é se o sistema recusa corretamente.

Porquê avaliação manual: com 20 perguntas é viável e é a forma mais fiável de julgar a correção jurídica.

Porque não as alternativas:

BLEU e ROUGE medem quantas palavras a resposta tem em comum com uma resposta de referência, e não se o que diz é verdade. Uma resposta pode partilhar muitas palavras com a referência e estar juridicamente errada.
RAGAS exige um LLM a servir de juiz, o que no CPU é lento e pouco fiável com modelos pequenos. Fica para a 3.ª fase, como estava planeado.
Resultados
	Por artigo	Tamanho fixo
Hit@5	94%	94%
MRR	0,86	0,87
	Com RAG	Sem RAG
Respostas corretas	75%	5%
Citações inventadas	nenhuma	em quase todas
Recusa fora do âmbito	2 de 2	0 de 2
Limitações da validação (diz isto antes que te perguntem)
O conjunto é pequeno. Com 18 perguntas no âmbito, cada pergunta vale 5,6 pontos percentuais, por isso a diferença de 0,86 para 0,87 no MRR não é significativa.
A avaliação foi feita por uma só pessoa, o que introduz alguma subjetividade.
A métrica favorece os chunks fixos: um pedaço com vários artigos conta como acerto se contiver qualquer um deles.
Para a 3.ª fase: alargar para 50–100 perguntas, escrever critérios de avaliação explícitos e acrescentar o RAGAS.