"""Ejecutar: python -m unittest -v. No usa paquetes externos."""
import random
import re
import unittest

from automatas import (Automata, VACIO, LAMBDA, clausura, concatenar, convertir,
                       ejemplos, estrella, indice, literal, mostrar, obtener_er,
                       palabras, preparar_verificacion, reconocedor_afnd, thompson,
                       union, verificar)


class PruebasAutomatas(unittest.TestCase):
    def setUp(self):
        self.ej = ejemplos()

    def comprobar(self, af, n=6, fuente_afd=False):
        afd = convertir(af)['afd']
        r = obtener_er(afd if fuente_afd else af)
        resultado = verificar(af, afd, r['er'], n)
        self.assertEqual(resultado['diferencias'], [])
        return resultado, r

    def test_caso_1_tabla_exacta(self):
        c = convertir(self.ej['Caso 1 del anexo'])
        self.assertEqual([f['conjunto'] for f in c['tabla']], [('q0',), ('q0', 'q1'), (), ('q2',)])
        self.assertEqual([list(f['destinos'].values()) for f in c['tabla']], [['D1', 'D2'], ['D1', 'D3'], ['D2', 'D2'], ['D2', 'D2']])
        self.assertEqual(c['afd'].finales, ['D3'])
        self.assertEqual(len(c['pasos']), 8)

    def test_caso_1_er_y_511_palabras(self):
        af = self.ej['Caso 1 del anexo']
        v, r = self.comprobar(af, 8, True)
        self.assertEqual(v['total'], 511)
        self.assertEqual(v['aceptadas'], [7, 7, 7])
        acepta = reconocedor_afnd(thompson(r['er']))
        for p in palabras(af.alfabeto, 8):
            self.assertEqual(acepta(p), bool(re.fullmatch('a+b', p)))

    def test_caso_2_er_exacta(self):
        af = self.ej['Caso 2 del anexo']
        _, r = self.comprobar(af, 8)
        self.assertEqual(r['expresion'], 'x·(x·y*·y)*')
        acepta = reconocedor_afnd(thompson(r['er']))
        for p in palabras(af.alfabeto, 8):
            self.assertEqual(acepta(p), bool(re.fullmatch('x(xy*y)*', p)))

    def test_flujo_afnd_afd_er_caso_2(self):
        self.comprobar(self.ej['Caso 2 del anexo'], 8, True)

    def test_epsilon_ciclo_e_inicial(self):
        af = self.ej['Bonus epsilon']
        self.assertEqual(clausura(['s'], indice(af)), {'s', 'p'})
        self.assertEqual(convertir(af)['inicial'], ('s', 'p'))
        self.comprobar(af, 8)

    def test_epsilon_despues_de_mover(self):
        af = Automata(['s', 'p', 'f'], ['a'], 's', ['f'], [('s', 'a', 'p'), ('p', '', 'f')])
        c = convertir(af)
        self.assertEqual(c['tabla'][1]['conjunto'], ('p', 'f'))
        self.assertIn('D1', c['afd'].finales)
        self.comprobar(af)

    def test_sin_finales(self):
        v, r = self.comprobar(Automata(['s'], ['a'], 's', [], []))
        self.assertEqual(r['er'], VACIO)
        self.assertEqual(v['aceptadas'], [0, 0, 0])

    def test_alfabeto_vacio(self):
        v, r = self.comprobar(Automata(['s'], [], 's', ['s'], []))
        self.assertEqual(v['total'], 1)
        self.assertEqual(v['aceptadas'], [1, 1, 1])
        self.assertEqual(r['er'], LAMBDA)

    def test_inicial_final_y_un_simbolo(self):
        af = Automata(['par', 'impar'], ['a'], 'par', ['par'], [('par', 'a', 'impar'), ('impar', 'a', 'par')])
        v, _ = self.comprobar(af, 8)
        self.assertEqual(v['aceptadas'], [5, 5, 5])

    def test_inalcanzable(self):
        af = self.ej['Caso 1 del anexo']
        af.estados.append('fantasma')
        af.finales.append('fantasma')
        af.transiciones.append(('fantasma', 'b', 'fantasma'))
        self.assertTrue(all('fantasma' not in f['conjunto'] for f in convertir(af)['tabla']))
        self.comprobar(af, 8)

    def test_simbolos_literales_y_unicode(self):
        for s in ('+', '*', '.', '🟢', ','):
            with self.subTest(simbolo=s):
                v, _ = self.comprobar(Automata(['s'], [s], 's', ['s'], [('s', s, 's')]))
                self.assertEqual(v['aceptadas'], [7, 7, 7])

    def test_inicial_no_es_el_primero(self):
        _, r = self.comprobar(Automata(['f', 's'], ['a'], 's', ['f'], [('s', 'a', 'f')]))
        self.assertEqual(r['expresion'], 'a')

    def test_validacion_y_duplicados(self):
        with self.assertRaises(ValueError):
            Automata(['s', 's'], ['a'], 's', [], [])
        with self.assertRaises(ValueError):
            Automata(['s'], ['a'], 'otro', [], [])
        with self.assertRaises(ValueError):
            Automata(['s'], ['ab'], 's', [], [])
        with self.assertRaises(ValueError):
            Automata(['s'], ['a'], 's', [], [('s', 'a', 'no')])
        self.assertEqual(len(Automata(['s'], ['a'], 's', [], [('s', 'a', 's')] * 2).transiciones), 1)

    def test_limites(self):
        af = self.ej['Caso 1 del anexo']
        with self.assertRaises(ValueError):
            convertir(af, limite=1)
        for n in (5, 6.5, 13, True):
            with self.assertRaises(ValueError):
                preparar_verificacion(af, convertir(af)['afd'], LAMBDA, n)
        grande = Automata(['s'], list('abcdefgh'), 's', [], [])
        with self.assertRaises(ValueError):
            preparar_verificacion(grande, convertir(grande)['afd'], VACIO, 8)

    def test_contraejemplos(self):
        af = self.ej['Caso 1 del anexo']
        afd = convertir(af)['afd']
        v = verificar(af, afd, LAMBDA)
        self.assertEqual(v['diferencias'][0], ('', False, False, True))
        self.assertTrue(any(f[0] == 'ab' for f in v['diferencias']))
        afd.finales.clear()
        v = verificar(af, afd, obtener_er(af)['er'])
        self.assertIn(('ab', True, False, True), v['diferencias'])

    def test_identidades_y_traza(self):
        a = literal('a')
        self.assertEqual(union(VACIO, a, a), a)
        self.assertEqual(concatenar(LAMBDA, a), a)
        self.assertEqual(concatenar(VACIO, a), VACIO)
        self.assertEqual(estrella(estrella(a)), estrella(a))
        r = obtener_er(self.ej['Caso 2 del anexo'])
        self.assertTrue(all(p['regla'] and p['detalle'] for p in r['pasos']))
        self.assertTrue(any(p['regla'] == 'Sustitución' for p in r['pasos']))

    def test_100_afnd_reproducibles(self):
        azar = random.Random(20261014)
        for caso in range(100):
            estados = ['u', 'v', 'w']
            af = Automata(estados, ['a', 'b'], estados[caso % 3], [s for s in estados if azar.random() < .45],
                          [(o, s, d) for o in estados for s in ('a', 'b', '') for d in estados if azar.random() < .16])
            with self.subTest(caso=caso):
                self.comprobar(af)

    def test_reglas_bucle_salida_y_final(self):
        casos = [
            (Automata(['s'], ['a'], 's', ['s'], [('s', 'a', 's')]), r'a*'),
            (Automata(['s', 'f'], ['a', 'b'], 's', ['f'],
                      [('s', 'a', 's'), ('s', 'b', 'f')]), r'a*b'),
            (Automata(['s'], ['a'], 's', ['s'], [('s', '', 's')]), r''),
            (Automata(['s'], ['a'], 's', [], [('s', '', 's')]), r'(?!)'),
        ]
        for af, patron in casos:
            with self.subTest(patron=patron):
                _, r = self.comprobar(af)
                acepta = reconocedor_afnd(thompson(r['er']))
                for palabra in palabras(af.alfabeto, 6):
                    self.assertEqual(acepta(palabra), re.fullmatch(patron, palabra) is not None)

    def test_reglas_alternativas_y_concatenacion(self):
        af = Automata(['s', 'p', 'f'], ['a', 'b'], 's', ['f'],
                      [('s', 'a', 'p'), ('s', 'b', 'p'), ('p', 'a', 'f')])
        _, r = self.comprobar(af)
        acepta = reconocedor_afnd(thompson(r['er']))
        for palabra in palabras(af.alfabeto, 6):
            self.assertEqual(acepta(palabra), re.fullmatch(r'(a|b)a', palabra) is not None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
