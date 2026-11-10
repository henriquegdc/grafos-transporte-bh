# Rede de teste GTFS

Dia padrão: quarta-feira, 04/11/2026. A linha L1 tem três viagens no padrão
A → B → C: partidas de A às 08:00, 08:20 e 24:10; cada trecho dura 300 s.
Na faixa 06:00–09:00, as duas partidas de A estão separadas por 1200 s;
o intervalo estimado é 1200 s e a espera esperada é 600 s.

A linha L2 tem uma viagem de referência A → D com 480 s e frequência de
600 s entre 09:00 e 10:00 (última partida às 09:50). A espera esperada
nessa faixa é 300 s. Em 11/11, `calendar_dates.txt` retira UTIL e ativa
apenas a viagem EXTRA, A → B → C às 10:00.

No recorte A/B (caixa de latitude -19.9011 a -19.8999 e longitude
-43.9011 a -43.8999), L1 vira A → B; C e D ficam fora. A caixa de longitude
-43.9001 a -43.8999 contém A e C, mas exclui B: ela não deve criar
uma aresta direta A → C.

No recorte apenas pela linha L1, a parada D sai da rede porque só pertence a L2.
