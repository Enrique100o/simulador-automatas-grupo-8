"""Algoritmos de autómatas. Solo librería estándar; sin interfaz ni red."""
from dataclasses import dataclass, field
from itertools import product


@dataclass
class Automata:
    estados: list[str]
    alfabeto: list[str]
    inicial: str
    finales: list[str]
    transiciones: list[tuple[str, str, str]]
    etiquetas: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.estados or len(set(self.estados)) != len(self.estados):
            raise ValueError('Se necesitan estados únicos, sin repetir.')
        if any(not isinstance(s, str) or not s or any(c.isspace() or c == ',' for c in s) for s in self.estados):
            raise ValueError('Los nombres de estados no pueden tener espacios ni comas.')
        if len(set(self.alfabeto)) != len(self.alfabeto):
            raise ValueError('Hay símbolos repetidos en el alfabeto.')
        if any(len(s) != 1 or s in ('ε', 'λ') or s.isspace() for s in self.alfabeto):
            raise ValueError('Cada símbolo debe tener un carácter; ε y λ no pertenecen al alfabeto.')
        if self.inicial not in self.estados or any(s not in self.estados for s in self.finales):
            raise ValueError('El inicial y los finales deben pertenecer a los estados.')
        normalizadas, vistas = [], set()
        for origen, simbolo, destino in self.transiciones:
            simbolo = '' if simbolo in ('', 'ε', 'λ', 'epsilon') else simbolo
            if origen not in self.estados or destino not in self.estados:
                raise ValueError(f'Transición con estado inexistente: {origen} → {destino}.')
            if simbolo and simbolo not in self.alfabeto:
                raise ValueError(f'El símbolo {simbolo!r} no pertenece al alfabeto.')
            t = (origen, simbolo, destino)
            if t not in vistas:
                vistas.add(t)
                normalizadas.append(t)
        self.transiciones = normalizadas
        self.finales = list(dict.fromkeys(self.finales))


def indice(af):
    resultado = {s: {} for s in af.estados}
    for origen, simbolo, destino in af.transiciones:
        resultado[origen].setdefault(simbolo, set()).add(destino)
    return resultado


def clausura(estados, transiciones):
    """Todos los alcanzables por cero o más pasos epsilon, incluso con ciclos."""
    vistos, pendientes = set(estados), list(estados)
    while pendientes:
        for destino in transiciones[pendientes.pop()].get('', ()):
            if destino not in vistos:
                vistos.add(destino)
                pendientes.append(destino)
    return vistos


def mover(estados, simbolo, transiciones):
    return {d for s in estados for d in transiciones[s].get(simbolo, ())}


def conjunto(estados):
    return '{' + ','.join(estados) + '}' if estados else '∅'


def convertir(af, limite=256):
    """Subconjuntos alcanzables. Devuelve AFD, tabla y pasos explicados."""
    ix = indice(af)
    ordenar = lambda ss: tuple(s for s in af.estados if s in ss)
    listas = [ordenar(clausura([af.inicial], ix))]
    ids = {listas[0]: 'D0'}
    transiciones, tabla, pasos, finales = [], [], [], []
    i = 0
    while i < len(listas):
        origen, activos = f'D{i}', listas[i]
        es_final = bool(set(activos).intersection(af.finales))
        if es_final:
            finales.append(origen)
        fila = {'id': origen, 'conjunto': activos, 'final': es_final, 'destinos': {}}
        for simbolo in af.alfabeto:
            mov = ordenar(mover(activos, simbolo, ix))
            destino = ordenar(clausura(mov, ix))
            nuevo = destino not in ids
            if nuevo:
                if len(listas) >= limite:
                    raise ValueError(f'La conversión supera {limite} subconjuntos; reduce el autómata.')
                ids[destino] = f'D{len(listas)}'
                listas.append(destino)
            destino_id = ids[destino]
            transiciones.append((origen, simbolo, destino_id))
            fila['destinos'][simbolo] = destino_id
            pasos.append({'origen': origen, 'activos': activos, 'simbolo': simbolo,
                          'destino': destino_id, 'detalle':
                          f'Procesar {conjunto(activos)} con {simbolo}: '
                          f'mover = {conjunto(mov)}; clausura-ε = {conjunto(destino)}. '
                          + ('Conjunto nuevo: se agrega a la cola. ' if nuevo else 'Conjunto ya registrado. ')
                          + ('Es final porque contiene un final original.' if set(destino).intersection(af.finales) else '')})
        tabla.append(fila)
        i += 1
    afd = Automata(list(ids.values()), af.alfabeto[:], 'D0', finales, transiciones,
                   {ids[ss]: conjunto(ss) for ss in listas})
    return {'afd': afd, 'tabla': tabla, 'pasos': pasos, 'inicial': listas[0]}


def reconocedor_afnd(af):
    ix, finales = indice(af), set(af.finales)

    def acepta(palabra):
        activos = clausura([af.inicial], ix)
        for simbolo in palabra:
            if simbolo not in af.alfabeto:
                return False
            activos = clausura(mover(activos, simbolo, ix), ix)
        return bool(activos.intersection(finales))
    return acepta


def reconocedor_afd(af):
    ix = indice(af)
    if any('' in fila or any(len(ds) != 1 for ds in fila.values()) for fila in ix.values()):
        raise ValueError('El segundo reconocedor requiere un AFD sin epsilon.')

    def acepta(palabra):
        estado = af.inicial
        for simbolo in palabra:
            destinos = ix[estado].get(simbolo)
            if not destinos:
                return False
            estado = next(iter(destinos))
        return estado in af.finales
    return acepta


@dataclass(frozen=True)
class ER:
    tipo: str
    hijos: tuple = ()
    simbolo: str = ''


VACIO, LAMBDA = ER('vacio'), ER('lambda')


def literal(simbolo):
    return ER('literal', simbolo=simbolo) if simbolo else LAMBDA


def union(*expresiones):
    partes = []
    for r in expresiones:
        for p in r.hijos if r.tipo == 'union' else (r,):
            if p != VACIO and p not in partes:
                partes.append(p)
    return VACIO if not partes else partes[0] if len(partes) == 1 else ER('union', tuple(partes))


def concatenar(*expresiones):
    partes = []
    for r in expresiones:
        if r == VACIO:
            return VACIO
        if r != LAMBDA:
            partes.extend(r.hijos if r.tipo == 'concat' else (r,))
    return LAMBDA if not partes else partes[0] if len(partes) == 1 else ER('concat', tuple(partes))


def estrella(r):
    return LAMBDA if r in (VACIO, LAMBDA) else r if r.tipo == 'estrella' else ER('estrella', (r,))


def mostrar(r, nivel=0):
    if r == VACIO:
        return '∅'
    if r == LAMBDA:
        return 'λ'
    if r.tipo == 'literal':
        return r.simbolo if r.simbolo.isalnum() else repr(r.simbolo)
    precedencia = {'union': 1, 'concat': 2, 'estrella': 3}[r.tipo]
    if r.tipo == 'estrella':
        texto = mostrar(r.hijos[0], 3) + '*'
    else:
        texto = (' + ' if r.tipo == 'union' else '·').join(mostrar(p, precedencia) for p in r.hijos)
    return '(' + texto + ')' if precedencia < nivel else texto


def obtener_er(af):
    """Resuelve Xi = suma(Aij Xj) + bi por eliminación y lema de Arden."""
    if len(af.estados) > 18:
        raise ValueError('Para la ER usa hasta 18 estados; puedes seleccionar el autómata original.')
    n = len(af.estados)
    posiciones = {s: i for i, s in enumerate(af.estados)}
    coef = [[VACIO for _ in range(n)] for _ in range(n)]
    constantes = [LAMBDA if s in af.finales else VACIO for s in af.estados]
    activos, pasos = list(range(n)), []
    nombre = lambda i: f'X[{af.estados[i]}]'

    def registrar(regla, detalle, antes='', despues=''):
        if len(pasos) >= 12000 or len(antes) + len(despues) > 80000:
            raise ValueError('La expresión o la explicación es demasiado grande; reduce el autómata.')
        pasos.append({'regla': regla, 'detalle': detalle, 'antes': antes, 'despues': despues})

    def operacion(tipo, *rs):
        funciones = {'union': union, 'concat': concatenar, 'estrella': estrella}
        r = funciones[tipo](*rs)
        antes = ((' + ' if tipo == 'union' else '·').join(f'({mostrar(x)})' for x in rs)
                 if tipo != 'estrella' else f'({mostrar(rs[0])})*')
        registrar('Simplificación algebraica',
                  'Identidades: ∅ + R = R; R + R = R; λ·R = R·λ = R; ∅·R = R·∅ = ∅; ∅* = λ; λ* = λ; asociatividad y precedencia.', antes, mostrar(r))
        return r

    for origen, simbolo, destino in af.transiciones:
        i, j = posiciones[origen], posiciones[destino]
        coef[i][j] = union(coef[i][j], literal(simbolo))

    def ecuacion(i):
        terminos = [f'{mostrar(coef[i][j], 2)}·{nombre(j)}' for j in activos if coef[i][j] != VACIO]
        if constantes[i] != VACIO:
            terminos.append(mostrar(constantes[i]))
        return nombre(i) + ' = ' + (' + '.join(terminos) or '∅')

    ecuaciones = [ecuacion(i) for i in activos]
    for i in activos:
        cantidad = sum(t[0] == af.estados[i] for t in af.transiciones)
        registrar('Unión de transiciones' if cantidad > 1 else 'Transición simple',
                  'Cada transición aporta su etiqueta por el lenguaje del destino; las alternativas se unen con +.', despues=ecuacion(i))
        if af.estados[i] in af.finales:
            registrar('Estado final: p = λ', 'Se añade λ para aceptar terminar aquí, conservando las salidas.', despues=ecuacion(i))
    inicial = posiciones[af.inicial]
    for k in [i for i in reversed(activos) if i != inicial]:
        antes, bucle = ecuacion(k), coef[k][k]
        cierre = operacion('estrella', bucle)
        salidas = {j: operacion('concat', cierre, coef[k][j]) for j in activos if j != k and coef[k][j] != VACIO}
        constante = operacion('concat', cierre, constantes[k])
        terminos = [f'{mostrar(r, 2)}·{nombre(j)}' for j, r in salidas.items()]
        if constante != VACIO:
            terminos.append(mostrar(constante))
        resuelta = nombre(k) + ' = ' + (' + '.join(terminos) or '∅')
        registrar('Sin bucle' if bucle == VACIO else 'Bucle más salida: Arden' if salidas else 'Bucle: Arden',
                  'X = A·X + B → X = A*·B. Se toma la solución mínima de lenguajes de caminos finitos; es única si λ no pertenece a A.', antes, resuelta)
        for i in activos:
            if i == k or coef[i][k] == VACIO:
                continue
            previa, factor = ecuacion(i), coef[i][k]
            for j, r in salidas.items():
                coef[i][j] = operacion('union', coef[i][j], operacion('concat', factor, r))
            constantes[i] = operacion('union', constantes[i], operacion('concat', factor, constante))
            coef[i][k] = VACIO
            registrar('Sustitución', f'Se reemplaza {nombre(k)} en {nombre(i)}.', previa, ecuacion(i))
        activos.remove(k)
    previa = ecuacion(inicial)
    resultado = operacion('concat', operacion('estrella', coef[inicial][inicial]), constantes[inicial])
    registrar('Arden en el estado inicial', 'El lenguaje del autómata es el de su estado inicial.', previa, mostrar(resultado))
    return {'er': resultado, 'expresion': mostrar(resultado), 'ecuaciones': ecuaciones, 'pasos': pasos}


def thompson(er):
    """AFND independiente a partir del árbol de expresión regular."""
    estados, transiciones, alfabeto = [], [], []

    def construir(r):
        inicio, fin = f'T{len(estados)}', f'T{len(estados) + 1}'
        estados.extend((inicio, fin))
        agregar = lambda a, s, b: transiciones.append((a, s, b))
        if r == LAMBDA:
            agregar(inicio, '', fin)
        elif r.tipo == 'literal':
            agregar(inicio, r.simbolo, fin)
            if r.simbolo not in alfabeto:
                alfabeto.append(r.simbolo)
        elif r.tipo == 'union':
            for hijo in r.hijos:
                a, b = construir(hijo)
                agregar(inicio, '', a)
                agregar(b, '', fin)
        elif r.tipo == 'concat':
            previo = inicio
            for hijo in r.hijos:
                a, b = construir(hijo)
                agregar(previo, '', a)
                previo = b
            agregar(previo, '', fin)
        elif r.tipo == 'estrella':
            a, b = construir(r.hijos[0])
            for origen, destino in [(inicio, fin), (inicio, a), (b, a), (b, fin)]:
                agregar(origen, '', destino)
        return inicio, fin

    inicio, fin = construir(er)
    return Automata(estados, alfabeto, inicio, [fin], transiciones)


def palabras(alfabeto, n):
    for longitud in range(n + 1):
        for letras in product(alfabeto, repeat=longitud):
            yield ''.join(letras)


def preparar_verificacion(afnd, afd, er, n):
    if type(n) is not int or not 6 <= n <= 12:
        raise ValueError('n debe ser un entero entre 6 y 12.')
    total = sum(len(afnd.alfabeto) ** i for i in range(n + 1))
    if total > 350000:
        raise ValueError(f'Se generarían {total:,} palabras; el límite es 350.000. Reduce n o el alfabeto.')
    return total, palabras(afnd.alfabeto, n), (reconocedor_afnd(afnd), reconocedor_afd(afd), reconocedor_afnd(thompson(er)))


def verificar(afnd, afd, er, n=6):
    total, cadenas, motores = preparar_verificacion(afnd, afd, er, n)
    aceptadas, diferencias = [0, 0, 0], []
    for palabra in cadenas:
        valores = [f(palabra) for f in motores]
        aceptadas = [cantidad + valor for cantidad, valor in zip(aceptadas, valores)]
        if len(set(valores)) > 1:
            diferencias.append((palabra, *valores))
    return {'n': n, 'total': total, 'aceptadas': aceptadas, 'diferencias': diferencias}


def ejemplos():
    return {
        'Caso 1 del anexo': Automata(['q0', 'q1', 'q2'], ['a', 'b'], 'q0', ['q2'], [('q0', 'a', 'q0'), ('q0', 'a', 'q1'), ('q1', 'b', 'q2')]),
        'Caso 2 del anexo': Automata(['q0', 'q1', 'q2'], ['x', 'y'], 'q0', ['q1'], [('q0', 'x', 'q1'), ('q1', 'x', 'q2'), ('q2', 'y', 'q2'), ('q2', 'y', 'q1')]),
        'Bonus epsilon': Automata(['s', 'p', 'f'], ['a', 'b'], 's', ['f'], [('s', '', 'p'), ('p', '', 's'), ('p', 'a', 'p'), ('p', 'b', 'f')])}
