"""Simulador local de autómatas - Grupo 8. Ejecutar: python app.py."""
import json
import math
import re
import tkinter as tk
from tkinter import ttk

from automatas import Automata, conjunto, convertir, ejemplos, obtener_er, preparar_verificacion

VERDE = '#17624f'
FONDO = '#f3f6f2'
TINTA = '#203b32'


def lista(texto):
    if texto.strip().startswith('['):
        valores = json.loads(texto)
        if not isinstance(valores, list) or any(not isinstance(x, str) for x in valores):
            raise ValueError('Una lista JSON debe contener solo texto.')
        return valores
    return [x for x in re.split(r'[,\s]+', texto.strip()) if x]


def escribir_texto(widget, texto):
    widget.configure(state='normal')
    widget.delete('1.0', 'end')
    widget.insert('1.0', texto)
    widget.configure(state='disabled')


def dibujar(canvas, af, activos=(), paso=None):
    """Dibuja sin Graphviz ni imágenes externas; mantiene la notación de clase."""
    canvas.delete('all')
    if af is None:
        return
    columnas = 2 if len(af.estados) == 4 else min(4, len(af.estados))
    filas = math.ceil(len(af.estados) / columnas)
    ancho = max(canvas.winfo_width() - 6, columnas * 155 + 30)
    alto = max(canvas.winfo_height() - 6, filas * 145 + 20)
    posiciones = {}
    for i, s in enumerate(af.estados):
        fila, col = divmod(i, columnas)
        cantidad = min(columnas, len(af.estados) - fila * columnas)
        posiciones[s] = ((ancho - cantidad * 155) / 2 + 77 + col * 155, 95 + fila * 145)
    grupos = {}
    for origen, simbolo, destino in af.transiciones:
        grupos.setdefault((origen, destino), []).append(simbolo or 'ε')
    for (origen, destino), simbolos in grupos.items():
        x, y = posiciones[origen]
        xx, yy = posiciones[destino]
        color = '#bd782c' if paso and (origen, destino) == (paso['origen'], paso['destino']) and paso['simbolo'] in simbolos else '#718b7b'
        if origen == destino:
            puntos = (x - 18, y - 21, x - 40, y - 79, x + 40, y - 79, x + 18, y - 21)
            tx, ty = x, y - 62
        else:
            dx, dy = xx - x, yy - y
            d = math.hypot(dx, dy)
            ux, uy = dx / d, dy / d
            curva = 35 if (destino, origen) in grupos else -42 if abs(dx) > 180 else 0
            cx, cy = (x + xx) / 2 - uy * curva, (y + yy) / 2 + ux * curva
            da, db = math.hypot(cx - x, cy - y), math.hypot(xx - cx, yy - cy)
            puntos = (x + (cx - x) / da * 43, y + (cy - y) / da * 26, cx, cy,
                      xx - (xx - cx) / db * 46, yy - (yy - cy) / db * 28)
            tx, ty = (puntos[0] + 2 * cx + puntos[4]) / 4, (puntos[1] + 2 * cy + puntos[5]) / 4 - 9
        canvas.create_line(*puntos, smooth=True, arrow=tk.LAST, fill=color, width=1.8, arrowshape=(9, 11, 4))
        etiqueta = ', '.join(dict.fromkeys(simbolos))
        w = max(17, len(etiqueta) * 6)
        canvas.create_rectangle(tx - w / 2 - 3, ty - 8, tx + w / 2 + 3, ty + 8, fill='white', outline='')
        canvas.create_text(tx, ty, text=etiqueta, fill=TINTA, font=('Segoe UI', 9))
    x, y = posiciones[af.inicial]
    canvas.create_line(x - 70, y, x - 44, y, arrow=tk.LAST, fill=VERDE, width=2)
    for s, (x, y) in posiciones.items():
        final, iluminado = s in af.finales, s in activos
        color = '#bd782c' if iluminado else VERDE
        canvas.create_oval(x - 43, y - 26, x + 43, y + 26, fill='#fff0d7' if iluminado else '#edf5ec', outline=color, width=2)
        if final:
            canvas.create_oval(x - 37, y - 21, x + 37, y + 21, outline=color, width=1.5)
        etiqueta = af.etiquetas.get(s, s)
        canvas.create_text(x, y, text=etiqueta if len(etiqueta) <= 13 else s, fill=TINTA, font=('Segoe UI', 9, 'bold'))
        if len(etiqueta) > 13:
            canvas.create_text(x, y + 37, text=etiqueta[:35] + ('…' if len(etiqueta) > 35 else ''), fill=TINTA, font=('Segoe UI', 8))
    if len(af.estados) <= 8:
        # Los casos pequeños caben completos; los grandes conservan desplazamiento.
        caja = canvas.bbox('all')
        vista_w, vista_h = canvas.winfo_width(), canvas.winfo_height()
        if caja and vista_w > 40 and vista_h > 40:
            factor = min(1, (vista_w - 32) / (caja[2] - caja[0]), (vista_h - 32) / (caja[3] - caja[1]))
            canvas.scale('all', caja[0], caja[1], factor, factor)
            caja = canvas.bbox('all')
            canvas.move('all', (vista_w - (caja[2] - caja[0])) / 2 - caja[0],
                        (vista_h - (caja[3] - caja[1])) / 2 - caja[1])
            ancho, alto = vista_w, vista_h
    canvas.configure(scrollregion=(0, 0, ancho, alto))


class Aplicacion(ttk.Frame):
    def __init__(self, root):
        super().__init__(root, padding=16)
        self.root = root
        root.title('Autómatas · Python y Tkinter · Grupo 8')
        root.geometry('1280x880')
        root.minsize(1020, 760)
        self.pack(fill='both', expand=True)
        self.afnd = self.conversion = self.er = None
        self.trabajo = None
        self.cargando = False
        self.paso_c = self.paso_r = 0
        estilo = ttk.Style()
        estilo.theme_use('clam')
        estilo.configure('.', font=('Segoe UI', 10), background=FONDO, foreground=TINTA)
        estilo.configure('TFrame', background=FONDO)
        estilo.configure('TLabelframe', bordercolor='#d5e0d5', background=FONDO)
        estilo.configure('TLabelframe.Label', foreground=VERDE, font=('Segoe UI', 10, 'bold'))
        estilo.configure('Titulo.TLabel', font=('Segoe UI', 22, 'bold'), foreground=VERDE)
        estilo.configure('Primario.TButton', background=VERDE, foreground='white', padding=(10, 7))
        estilo.map('Primario.TButton', background=[('active', '#237e63')])
        estilo.configure('TNotebook.Tab', padding=(13, 9))
        estilo.configure('Treeview', rowheight=26, background='white', fieldbackground='white', font=('Segoe UI', 9))
        estilo.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        cabecera = ttk.Frame(self)
        cabecera.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 14))
        ttk.Label(cabecera, text='Autómatas', style='Titulo.TLabel').pack(side='left')
        ttk.Label(cabecera, text='   AFND → AFD → ER   |   Grupo 8 · Python + Tkinter · Offline').pack(side='left', padx=10)
        self._editor()
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=1, column=1, sticky='nsew', padx=(16, 0))
        self.tab_c, self.tab_r, self.tab_v = (ttk.Frame(self.tabs, padding=12) for _ in range(3))
        for frame, titulo in [(self.tab_c, '01  AFND → AFD'), (self.tab_r, '02  Autómata → ER'), (self.tab_v, '03  Verificador')]:
            self.tabs.add(frame, text=titulo)
        self._conversion()
        self._expresion()
        self._verificador()
        self.estado = tk.StringVar(value='Listo.')
        ttk.Label(self, textvariable=self.estado, wraplength=1200).grid(row=2, column=0, columnspan=2, sticky='ew', pady=(12, 6))
        ttk.Label(self, text='FABER ENRIQUE UNI GOMEZ · JAIR DANIEL ROSADO RIASCOS · JUAN FELIPE TORREZ', font=('Segoe UI', 8)).grid(row=3, column=0, columnspan=2, sticky='w')
        self.cargar_ejemplo()

    def _boton(self, padre, texto, accion, primario=False):
        return ttk.Button(padre, text=texto, command=lambda: self.seguro(accion), style='Primario.TButton' if primario else 'TButton')

    def seguro(self, accion):
        try:
            accion()
        except (ValueError, TypeError, KeyError, RecursionError) as error:
            self.estado.set('Error: ' + str(error))

    def _editor(self):
        marco = ttk.LabelFrame(self, text='Autómata de entrada', padding=14)
        marco.grid(row=1, column=0, sticky='ns')
        marco.columnconfigure(0, weight=1)
        self.seleccion = tk.StringVar(value='Caso 1 del anexo')
        ttk.Combobox(marco, textvariable=self.seleccion, values=list(ejemplos()), state='readonly', width=25).grid(row=0, column=0, sticky='ew')
        self._boton(marco, 'Cargar ejemplo', self.cargar_ejemplo).grid(row=1, column=0, sticky='ew', pady=(5, 15))
        self.campos = {}
        for i, (clave, titulo) in enumerate([('estados', 'Estados (por coma)'), ('alfabeto', 'Alfabeto (por coma)'), ('inicial', 'Estado inicial'), ('finales', 'Finales (por coma)')]):
            ttk.Label(marco, text=titulo).grid(row=2 + i * 2, column=0, sticky='w', pady=(5, 4))
            variable = tk.StringVar()
            ttk.Entry(marco, textvariable=variable, width=27).grid(row=3 + i * 2, column=0, sticky='ew')
            variable.trace_add('write', self.invalidar)
            self.campos[clave] = variable
        ttk.Label(marco, text='Transiciones: origen símbolo destino').grid(row=10, column=0, sticky='w', pady=(18, 5))
        self.transiciones = tk.Text(marco, width=28, height=10, font=('Consolas', 10), undo=True, relief='solid', borderwidth=1)
        self.transiciones.grid(row=11, column=0, sticky='nsew')
        marco.rowconfigure(11, weight=1)
        self.transiciones.bind('<<Modified>>', self._modificado)
        ttk.Label(marco, text='Una fila por destino. Ejemplo: q0 a q1\nUsa ε, λ o epsilon para no consumir símbolo.', font=('Segoe UI', 8), wraplength=250).grid(row=12, column=0, sticky='w', pady=8)
        self._boton(marco, 'Convertir a AFD', self.convertir, True).grid(row=13, column=0, sticky='ew', pady=(2, 6))

    def _conversion(self):
        f = self.tab_c
        f.columnconfigure(0, weight=1)
        f.rowconfigure(1, weight=1)
        self.resumen_c = tk.StringVar()
        ttk.Label(f, textvariable=self.resumen_c).grid(row=0, column=0, sticky='w', pady=(0, 8))
        graficos = ttk.Frame(f)
        graficos.grid(row=1, column=0, sticky='nsew')
        graficos.columnconfigure((0, 1), weight=1)
        graficos.rowconfigure(0, weight=1)
        self.canvases = []
        for col, titulo in enumerate(['AFND original', 'AFD resultante']):
            grupo = ttk.LabelFrame(graficos, text=titulo, padding=4)
            grupo.grid(row=0, column=col, sticky='nsew', padx=(0, 6) if col == 0 else (6, 0))
            grupo.columnconfigure(0, weight=1)
            grupo.rowconfigure(0, weight=1)
            canvas = tk.Canvas(grupo, width=350, height=295, background='white', highlightthickness=0)
            canvas.grid(row=0, column=0, sticky='nsew')
            sx, sy = ttk.Scrollbar(grupo, orient='horizontal', command=canvas.xview), ttk.Scrollbar(grupo, command=canvas.yview)
            sx.grid(row=1, column=0, sticky='ew')
            sy.grid(row=0, column=1, sticky='ns')
            canvas.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
            canvas.bind('<Configure>', lambda _e: self.redibujar())
            self.canvases.append(canvas)
        pasos = ttk.LabelFrame(f, text='Paso a paso', padding=10)
        pasos.grid(row=2, column=0, sticky='ew', pady=10)
        pasos.columnconfigure(1, weight=1)
        self.texto_c = tk.StringVar()
        self.contador_c = tk.StringVar()
        ttk.Label(pasos, textvariable=self.texto_c, wraplength=780).grid(row=0, column=0, columnspan=3, sticky='ew', pady=(0, 8))
        self.prev_c = self._boton(pasos, '← Anterior', lambda: self.paso_conversion(-1))
        self.prev_c.grid(row=1, column=0)
        ttk.Label(pasos, textvariable=self.contador_c, anchor='center').grid(row=1, column=1, sticky='ew')
        self.next_c = self._boton(pasos, 'Siguiente →', lambda: self.paso_conversion(1))
        self.next_c.grid(row=1, column=2)
        grupo = ttk.LabelFrame(f, text='Tabla de conversión · → inicial · ★ final', padding=5)
        grupo.grid(row=3, column=0, sticky='ew')
        grupo.columnconfigure(0, weight=1)
        self.tabla = ttk.Treeview(grupo, show='headings', height=5)
        self.tabla.grid(row=0, column=0, sticky='ew')
        sx = ttk.Scrollbar(grupo, orient='horizontal', command=self.tabla.xview)
        sy = ttk.Scrollbar(grupo, command=self.tabla.yview)
        sx.grid(row=1, column=0, sticky='ew')
        sy.grid(row=0, column=1, sticky='ns')
        self.tabla.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)

    def _expresion(self):
        f = self.tab_r
        f.columnconfigure(0, weight=1)
        f.rowconfigure(6, weight=1)
        barra = ttk.Frame(f)
        barra.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        self.fuente = tk.StringVar(value='AFD convertido')
        selector = ttk.Combobox(barra, textvariable=self.fuente, values=['AFD convertido', 'Autómata original'], state='readonly', width=24)
        selector.pack(side='left')
        selector.bind('<<ComboboxSelected>>', lambda _e: self.limpiar_er())
        self._boton(barra, 'Obtener expresión regular', self.calcular_er, True).pack(side='left', padx=10)
        ttk.Label(f, text='Expresión del lenguaje', foreground=VERDE).grid(row=1, column=0, sticky='w')
        self.resultado_er = tk.Text(f, height=3, wrap='word', font=('Consolas', 16), relief='flat', background='#e7f1e8', state='disabled')
        self.resultado_er.grid(row=2, column=0, sticky='ew', pady=(5, 10))
        ttk.Label(f, text='Sistema de ecuaciones inicial').grid(row=3, column=0, sticky='w')
        self.ecuaciones = tk.Text(f, height=6, font=('Consolas', 10), wrap='word', relief='flat', state='disabled')
        self.ecuaciones.grid(row=4, column=0, sticky='ew', pady=5)
        self.selector_r = ttk.Combobox(f, state='disabled')
        self.selector_r.grid(row=5, column=0, sticky='ew', pady=10)
        self.selector_r.bind('<<ComboboxSelected>>', self.seleccionar_paso_er)
        self.detalle_r = tk.Text(f, wrap='word', font=('Consolas', 10), relief='flat', state='disabled', height=10)
        self.detalle_r.grid(row=6, column=0, sticky='nsew')
        barra = ttk.Frame(f)
        barra.grid(row=7, column=0, sticky='ew', pady=(10, 0))
        barra.columnconfigure(1, weight=1)
        self.prev_r = self._boton(barra, '← Anterior', lambda: self.paso_er(-1))
        self.prev_r.grid(row=0, column=0)
        self.contador_r = tk.StringVar()
        ttk.Label(barra, textvariable=self.contador_r, anchor='center').grid(row=0, column=1, sticky='ew')
        self.next_r = self._boton(barra, 'Siguiente →', lambda: self.paso_er(1))
        self.next_r.grid(row=0, column=2)
        ttk.Label(f, text='λ: cadena vacía · ∅: lenguaje vacío · +: unión · ·: concatenación · *: estrella', font=('Segoe UI', 9)).grid(row=8, column=0, sticky='w', pady=(12, 0))

    def _verificador(self):
        f = self.tab_v
        f.columnconfigure(0, weight=1)
        f.rowconfigure(4, weight=1)
        barra = ttk.Frame(f)
        barra.grid(row=0, column=0, sticky='ew', pady=8)
        ttk.Label(barra, text='Longitud máxima n:').pack(side='left')
        self.n = tk.StringVar(value='6')
        ttk.Spinbox(barra, from_=6, to=12, textvariable=self.n, width=5).pack(side='left', padx=10)
        self.n.trace_add('write', lambda *_a: self.limpiar_verificacion())
        self.b_verificar = self._boton(barra, 'Verificar AFND / AFD / ER', self.iniciar_verificacion, True)
        self.b_verificar.pack(side='left', padx=4)
        self.b_cancelar = self._boton(barra, 'Cancelar', self.cancelar)
        self.b_cancelar.pack(side='left', padx=6)
        self.mensaje_v = tk.StringVar(value='Primero convierte a AFD y calcula la ER.')
        ttk.Label(f, textvariable=self.mensaje_v, wraplength=800, foreground=VERDE, font=('Segoe UI', 12, 'bold')).grid(row=1, column=0, sticky='ew', pady=18)
        self.progreso = ttk.Progressbar(f)
        self.progreso.grid(row=2, column=0, sticky='ew')
        self.metricas = tk.StringVar(value='Sin resultados.')
        ttk.Label(f, textvariable=self.metricas, font=('Segoe UI', 12)).grid(row=3, column=0, sticky='w', pady=20)
        self.diferencias = ttk.Treeview(f, columns=('cadena', 'afnd', 'afd', 'er'), show='headings')
        for clave, titulo in [('cadena', 'Cadena con diferencia'), ('afnd', 'AFND'), ('afd', 'AFD'), ('er', 'ER')]:
            self.diferencias.heading(clave, text=titulo)
            self.diferencias.column(clave, width=180 if clave == 'cadena' else 100, anchor='center')
        self.diferencias.grid(row=4, column=0, sticky='nsew')
        sy = ttk.Scrollbar(f, command=self.diferencias.yview)
        sy.grid(row=4, column=1, sticky='ns')
        self.diferencias.configure(yscrollcommand=sy.set)
        ttk.Label(f, text='Se comprueban λ y todas las cadenas hasta n. Esto no demuestra equivalencia para longitudes mayores.\nMotores: AFND por conjuntos, AFD por un estado y ER por un AFND independiente de Thompson.', wraplength=800).grid(row=5, column=0, sticky='w', pady=15)

    def _modificado(self, _evento):
        if self.transiciones.edit_modified():
            self.transiciones.edit_modified(False)
            self.invalidar()

    def invalidar(self, *_args):
        if self.cargando or not hasattr(self, 'tabs'):
            return
        self.afnd = self.conversion = None
        self.limpiar_er()
        self.tabla.delete(*self.tabla.get_children())
        for canvas in self.canvases:
            canvas.delete('all')
        self.resumen_c.set('Entrada modificada. Pulsa Convertir a AFD.')
        self.texto_c.set('Los resultados anteriores se invalidaron al editar.')
        self.contador_c.set('')
        self.prev_c.configure(state='disabled')
        self.next_c.configure(state='disabled')
        self.estado.set('Entrada modificada; vuelve a convertir.')

    def limpiar_er(self):
        self.er = None
        escribir_texto(self.resultado_er, 'Pendiente de calcular')
        escribir_texto(self.ecuaciones, '')
        escribir_texto(self.detalle_r, '')
        self.selector_r.configure(values=(), state='disabled')
        self.selector_r.set('')
        self.contador_r.set('')
        self.prev_r.configure(state='disabled')
        self.next_r.configure(state='disabled')
        self.limpiar_verificacion()

    def limpiar_verificacion(self):
        self.cancelar()
        self.mensaje_v.set('Listo para verificar los tres reconocedores.' if self.conversion and self.er
                           else 'AFD listo. Calcula la ER para continuar.' if self.conversion
                           else 'Primero convierte a AFD y calcula la ER.')
        self.metricas.set('Sin resultados.')
        self.progreso['value'] = 0
        self.diferencias.delete(*self.diferencias.get_children())

    def leer_editor(self):
        transiciones = []
        for numero, linea in enumerate(self.transiciones.get('1.0', 'end').splitlines(), 1):
            if not linea.strip():
                continue
            partes = linea.split()
            if len(partes) != 3:
                raise ValueError(f'Línea {numero}: usa origen símbolo destino, separados por espacios.')
            transiciones.append(tuple(partes))
        af = Automata(lista(self.campos['estados'].get()), lista(self.campos['alfabeto'].get()),
                      self.campos['inicial'].get().strip(), lista(self.campos['finales'].get()), transiciones)
        if len(af.estados) > 12 or len(af.alfabeto) > 8:
            raise ValueError('El editor admite hasta 12 estados y 8 símbolos.')
        return af

    def cargar_ejemplo(self):
        af = ejemplos()[self.seleccion.get()]
        self.cargando = True
        for campo in ('estados', 'alfabeto', 'inicial', 'finales'):
            valor = getattr(af, campo)
            self.campos[campo].set(valor if isinstance(valor, str) else ','.join(valor))
        self.transiciones.delete('1.0', 'end')
        self.transiciones.insert('1.0', '\n'.join(f'{o} {s or "ε"} {d}' for o, s, d in af.transiciones))
        self.transiciones.edit_modified(False)
        self.cargando = False
        self.convertir()

    def convertir(self):
        af = self.leer_editor()
        conversion = convertir(af)
        self.afnd, self.conversion = af, conversion
        self.limpiar_er()
        self.paso_c = 0
        columnas = ['conjunto'] + [f's{i}' for i in range(len(af.alfabeto))] + ['final']
        self.tabla.configure(columns=columnas)
        for clave, titulo in zip(columnas, ['Estado AFD / subconjunto'] + af.alfabeto + ['Final']):
            self.tabla.heading(clave, text=titulo)
            self.tabla.column(clave, width=240 if clave == 'conjunto' else 145 if clave != 'final' else 60, minwidth=60)
        self.tabla.delete(*self.tabla.get_children())
        afd = conversion['afd']
        for fila in conversion['tabla']:
            inicial = fila['id'] == afd.inicial
            etiqueta = ('→ ' if inicial else '') + ('★ ' if fila['final'] else '') + fila['id'] + ' = ' + conjunto(fila['conjunto'])
            valores = [etiqueta] + [afd.etiquetas[fila['destinos'][s]] for s in af.alfabeto] + ['Sí' if fila['final'] else 'No']
            self.tabla.insert('', 'end', iid=fila['id'], values=valores)
        self.resumen_c.set(f'{len(afd.estados)} conjuntos alcanzables · {len(afd.finales)} finales · ' + ('incluye pozo ∅' if '∅' in afd.etiquetas.values() else 'sin estado pozo'))
        self.mostrar_conversion()
        self.tabs.select(self.tab_c)
        self.estado.set('Conversión lista. Recorre los pasos o continúa al módulo de ER.')

    def redibujar(self):
        if self.conversion:
            paso = self.conversion['pasos'][self.paso_c - 1] if self.paso_c else None
            dibujar(self.canvases[0], self.afnd, paso['activos'] if paso else self.conversion['inicial'])
            dibujar(self.canvases[1], self.conversion['afd'], [paso['origen'] if paso else 'D0'], paso)

    def mostrar_conversion(self):
        c = self.conversion
        if not c:
            return
        total = len(c['pasos'])
        texto = c['pasos'][self.paso_c - 1]['detalle'] if self.paso_c else f'Estado inicial: clausura-ε({self.afnd.inicial}) = {conjunto(c["inicial"])}. Un conjunto es final si contiene un final del AFND.'
        self.texto_c.set(texto)
        self.contador_c.set(f'Paso {self.paso_c} de {total}')
        self.prev_c.configure(state='normal' if self.paso_c > 0 else 'disabled')
        self.next_c.configure(state='normal' if self.paso_c < total else 'disabled')
        self.tabla.selection_set(c['pasos'][self.paso_c - 1]['origen'] if self.paso_c else 'D0')
        self.redibujar()

    def paso_conversion(self, incremento):
        if self.conversion:
            self.paso_c = max(0, min(self.paso_c + incremento, len(self.conversion['pasos'])))
            self.mostrar_conversion()

    def calcular_er(self):
        if not self.conversion:
            raise ValueError('Primero convierte el autómata a AFD.')
        resultado = obtener_er(self.conversion['afd'] if self.fuente.get() == 'AFD convertido' else self.afnd)
        self.limpiar_verificacion()
        self.er, self.paso_r = resultado, 0
        escribir_texto(self.resultado_er, resultado['expresion'])
        escribir_texto(self.ecuaciones, '\n'.join(resultado['ecuaciones']))
        self.selector_r.configure(values=[f'{i + 1}. {p["regla"]}' for i, p in enumerate(resultado['pasos'])], state='readonly')
        self.mostrar_er()
        self.mensaje_v.set('Listo para verificar los tres reconocedores.')
        self.estado.set('ER calculada. Ya puedes verificar los tres reconocedores.')

    def mostrar_er(self):
        if not self.er:
            return
        p = self.er['pasos'][self.paso_r]
        self.selector_r.current(self.paso_r)
        escribir_texto(self.detalle_r, f'REGLA: {p["regla"]}\n\n{p["detalle"]}\n\nANTES\n{p["antes"] or "Construcción del sistema"}\n\nDESPUÉS\n{p["despues"]}')
        self.contador_r.set(f'Paso {self.paso_r + 1} de {len(self.er["pasos"])}')
        self.prev_r.configure(state='normal' if self.paso_r else 'disabled')
        self.next_r.configure(state='normal' if self.paso_r < len(self.er['pasos']) - 1 else 'disabled')

    def paso_er(self, incremento):
        if self.er:
            self.paso_r = max(0, min(self.paso_r + incremento, len(self.er['pasos']) - 1))
            self.mostrar_er()

    def seleccionar_paso_er(self, _evento):
        self.paso_r = self.selector_r.current()
        self.mostrar_er()

    def cancelar(self):
        if self.trabajo is not None:
            self.trabajo = None
            self.mensaje_v.set('Verificación cancelada; no se emite una conclusión.')
        if hasattr(self, 'b_verificar'):
            self.b_verificar.configure(state='normal')
            self.b_cancelar.configure(state='disabled')

    def iniciar_verificacion(self):
        if not self.conversion or not self.er:
            raise ValueError('Convierte a AFD y calcula la ER antes de verificar.')
        try:
            n = int(self.n.get())
        except ValueError:
            raise ValueError('n debe ser un entero entre 6 y 12.') from None
        total, cadenas, motores = preparar_verificacion(self.afnd, self.conversion['afd'], self.er['er'], n)
        self.limpiar_verificacion()
        trabajo = {'n': n, 'total': total, 'cadenas': cadenas, 'motores': motores, 'revisadas': 0, 'aceptadas': [0, 0, 0], 'diferencias': []}
        self.trabajo = trabajo
        self.b_verificar.configure(state='disabled')
        self.b_cancelar.configure(state='normal')
        self.progreso.configure(maximum=total, value=0)
        self._lote(trabajo)

    def _lote(self, trabajo):
        if self.trabajo is not trabajo:
            return
        terminado = False
        for _ in range(128):
            try:
                palabra = next(trabajo['cadenas'])
            except StopIteration:
                terminado = True
                break
            valores = [f(palabra) for f in trabajo['motores']]
            trabajo['revisadas'] += 1
            for i, valor in enumerate(valores):
                trabajo['aceptadas'][i] += valor
            if len(set(valores)) > 1:
                trabajo['diferencias'].append((palabra, *valores))
        self.progreso['value'] = trabajo['revisadas']
        self.metricas.set(f'Comprobadas: {trabajo["revisadas"]:,}    |    Aceptadas AFND: {trabajo["aceptadas"][0]:,}    AFD: {trabajo["aceptadas"][1]:,}    ER: {trabajo["aceptadas"][2]:,}')
        if terminado:
            self.trabajo = None
            self.b_verificar.configure(state='normal')
            self.b_cancelar.configure(state='disabled')
            diferencias = trabajo['diferencias']
            self.mensaje_v.set(f'{len(diferencias)} cadenas con diferencias.' if diferencias else f'Sin diferencias en las {trabajo["total"]:,} cadenas hasta n = {trabajo["n"]}.')
            for palabra, *valores in diferencias:
                self.diferencias.insert('', 'end', values=[palabra or 'λ'] + ['Acepta' if v else 'Rechaza' for v in valores])
        else:
            self.mensaje_v.set(f'Verificando {trabajo["revisadas"]:,} de {trabajo["total"]:,} cadenas…')
            self.root.after(1, lambda: self._lote(trabajo))


def main():
    root = tk.Tk()
    Aplicacion(root)
    root.mainloop()


if __name__ == '__main__':
    main()
