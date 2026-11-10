"""Gabaritos calculados à mão em dados/rede-teste/GABARITO.md."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path

from transporte.dados.leitor_gtfs import ler, validar
from transporte.dados.modelo import Frequencia, Linha, Padrao, Parada, Rede, Viagem

REDE = Path(__file__).resolve().parents[2] / "dados" / "rede-teste"


class TestGTFS(unittest.TestCase):
    def test_dia_padrao_e_partidas(self) -> None:
        rede = ler(REDE)
        self.assertEqual(rede.dia, "2026-11-04")
        self.assertEqual(set(rede.viagens_por_id), {"t1", "t2", "t3", "f1"})
        padrao = rede.viagens_por_id["t1"].padrao_id
        self.assertEqual(rede.padroes[padrao].paradas, ("A", "B", "C"))
        self.assertEqual(rede.partidas[(padrao, "A")], [28800, 30000, 87000])
        self.assertEqual(rede.viagens_por_id["t1"].horarios, (28800, 29100, 29400))
        self.assertEqual(
            rede.viagens[padrao],
            [(28800, 29100, 29400), (30000, 30300, 30600), (87000, 87300, 87600)],
        )

    def test_frequencia_expandida(self) -> None:
        rede = ler(REDE)
        padrao = rede.viagens_por_id["f1"].padrao_id
        self.assertEqual(rede.partidas[(padrao, "A")], list(range(32400, 36000, 600)))
        self.assertEqual(rede.partidas[(padrao, "D")], list(range(32880, 36480, 600)))
        self.assertEqual(
            rede.viagens[padrao],
            [(partida, partida + 480) for partida in range(32400, 36000, 600)],
        )
        self.assertEqual(set(rede.viagens_por_id), {"t1", "t2", "t3", "f1"})

    def test_excecao_do_calendario(self) -> None:
        rede = ler(REDE, date(2026, 11, 11))
        self.assertEqual(set(rede.viagens_por_id), {"extra"})

    def test_recorte_por_linha_e_caixa(self) -> None:
        rede = ler(REDE)
        rede.inconsistencias.append("erro de exemplo")
        recorte = rede.recortar((-19.9011, -43.9011, -19.8999, -43.8999), {"L1"})
        self.assertEqual(set(recorte.paradas), {"A", "B"})
        self.assertEqual(set(recorte.linhas), {"L1"})
        self.assertEqual({p.paradas for p in recorte.padroes.values()}, {("A", "B")})
        self.assertEqual(recorte.viagens_por_id["t1"].horarios, (28800, 29100))
        self.assertEqual(recorte.inconsistencias, ["erro de exemplo"])
        self.assertIsNot(recorte.inconsistencias, rede.inconsistencias)

    def test_recorte_nao_inventa_atralho(self) -> None:
        rede = ler(REDE)
        recorte = rede.recortar((-19.9021, -43.9001, -19.8999, -43.8999))
        self.assertEqual(set(recorte.paradas), {"A", "C"})
        self.assertFalse(recorte.padroes)
        self.assertFalse(recorte.viagens_por_id)

    def test_recorte_por_linha_remove_paradas_de_outras_linhas(self) -> None:
        rede = ler(REDE)
        recorte = rede.recortar(linhas={"L1"})
        self.assertEqual(set(recorte.paradas), {"A", "B", "C"})
        self.assertEqual(set(recorte.linhas), {"L1"})
        self.assertEqual({p.linha_id for p in recorte.padroes.values()}, {"L1"})

    def test_recorte_preserva_frequencias(self) -> None:
        recorte = ler(REDE).recortar(linhas={"L2"})
        padrao = recorte.viagens_por_id["f1"].padrao_id
        self.assertEqual(set(recorte.paradas), {"A", "D"})
        self.assertEqual(recorte.partidas[(padrao, "A")], list(range(32400, 36000, 600)))
        self.assertEqual(recorte.partidas[(padrao, "D")], list(range(32880, 36480, 600)))

    def test_recorte_divide_trechos_e_desloca_frequencia(self) -> None:
        rede = self._rede_com_trechos()
        recorte = rede.recortar((-1, -1, 1, 1))
        self.assertEqual(
            {p.id: p.paradas for p in recorte.padroes.values()},
            {"p1#trecho0": ("A", "B"), "p1#trecho1": ("D", "E")},
        )
        self.assertEqual(recorte.viagens_por_id["v1#trecho1"].horarios, (32760, 32880))
        self.assertEqual(
            recorte.frequencias,
            (
                Frequencia("v1#trecho0", 32400, 33600, 600),
                Frequencia("v1#trecho1", 32760, 33960, 600),
            ),
        )
        self.assertEqual(recorte.viagens["p1#trecho1"], [(32760, 32880), (33360, 33480)])
        self.assertEqual(recorte.partidas[("p1#trecho1", "D")], [32760, 33360])

    def test_recorte_unifica_padroes_iguais_e_preserva_viagens(self) -> None:
        rede = self._rede_com_trechos()
        rede.padroes["p2"] = Padrao("p2", "L", ("A", "B", "X", "D", "E"))
        rede.viagens_por_id["v2"] = Viagem(
            "v2", "p2", "UTIL", (32460, 32580, 32700, 32820, 32940)
        )
        rede.recalcular_partidas()

        recorte = rede.recortar((-1, -1, 1, 1))
        self.assertEqual(len(recorte.padroes), 2)
        self.assertEqual(
            {p.paradas for p in recorte.padroes.values()}, {("A", "B"), ("D", "E")}
        )
        self.assertEqual(
            {v.padrao_id for v in recorte.viagens_por_id.values()},
            set(recorte.padroes),
        )
        self.assertEqual(len(recorte.viagens_por_id), 4)
        self.assertEqual(recorte.partidas[("p1#trecho0", "A")], [32400, 32460, 33000])
        self.assertEqual(recorte.partidas[("p1#trecho1", "D")], [32760, 32820, 33360])

    @staticmethod
    def _rede_com_trechos() -> Rede:
        paradas = {
            ident: Parada(ident, ident, 0, 2 if ident in {"C", "X"} else 0)
            for ident in ("A", "B", "C", "D", "E", "X")
        }
        rede = Rede(
            paradas=paradas,
            linhas={"L": Linha("L", "Linha", 3)},
            padroes={"p1": Padrao("p1", "L", ("A", "B", "C", "D", "E"))},
            partidas={},
            viagens_por_id={
                "v1": Viagem("v1", "p1", "UTIL", (32400, 32520, 32640, 32760, 32880))
            },
            frequencias=(Frequencia("v1", 32400, 33600, 600),),
        )
        rede.recalcular_partidas()
        return rede

    def test_zip(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            caminho = Path(temporario) / "feed.zip"
            with zipfile.ZipFile(caminho, "w") as arquivo:
                for csv_path in REDE.glob("*.txt"):
                    arquivo.write(csv_path, f"gtfs/{csv_path.name}")
            self.assertEqual(ler(caminho).dia, "2026-11-04")
            self.assertEqual(validar(caminho), [])

    def test_inconsistencias(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            pasta = Path(temporario)
            for origem in REDE.glob("*.txt"):
                (pasta / origem.name).write_bytes(origem.read_bytes())
            with (pasta / "stops.txt").open("a") as arquivo:
                arquivo.write("ERR,Sem coordenada,,\n")
            with (pasta / "trips.txt").open("a") as arquivo:
                arquivo.write("L1,UTIL,sem_paradas\n")
            with (pasta / "stop_times.txt").open("a") as arquivo:
                arquivo.write("t1,99:99:00,99:99:00,B,4\n")
            erros = validar(pasta)
            self.assertTrue(any("parada ERR" in e for e in erros))
            self.assertTrue(any("viagem sem_paradas" in e for e in erros))
            self.assertTrue(any("viagem t1" in e for e in erros))

    def test_arquivo_obrigatorio_ausente(self) -> None:
        with tempfile.TemporaryDirectory() as temporario:
            self.assertTrue(any("ausentes" in e for e in validar(temporario)))


if __name__ == "__main__":
    unittest.main()
