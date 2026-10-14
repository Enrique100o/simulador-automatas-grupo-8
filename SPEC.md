# Especificación y arquitectura - Grupo 8

FABER ENRIQUE UNI GOMEZ · JAIR DANIEL ROSADO RIASCOS · JUAN FELIPE TORREZ

## Alcance y criterios de aceptación

Aplicación local en Python 3.10+ y Tkinter. Una sola tecnología de interfaz, biblioteca estándar y ejecución `python app.py`. No usa red, backend, API, CDN ni paquetes externos.

| ID | Entrada / operación | Salida y criterio |
| --- | --- | --- |
| R01 | Estados, alfabeto, inicial, finales, transiciones | Editor validado; errores comprensibles; resultados previos descartados al editar |
| R02 | AFND con o sin epsilon | AFD por subconjuntos alcanzables; cola de pendientes; inicial por clausura; finales por intersección |
| R03 | Subconjunto y símbolo | Tabla completa y paso que explica movimiento, clausura y destino; ∅ absorbente cuando sea alcanzable |
| R04 | AFND y AFD | Dos grafos: óvalos, flechas con símbolo, flecha de entrada y doble contorno en finales |
| R05 | Original o AFD del módulo 1 | Sistema inicial de ecuaciones, reglas, sustituciones, simplificaciones y ER final navegables |
| R06 | AFND, AFD, ER y n configurable | Enumerar λ y todas las palabras hasta n, mínimo 6; comparar tres reconocedores y mostrar diferencias concretas |
| R07 | Ambos casos del Anexo A | Caso 1 con cuatro subconjuntos y lenguaje de una o más a seguido de b; caso 2 equivalente a x·(x·y*·y)* |
| R08 | Transiciones epsilon | Clausura inicial y después de cada movimiento, incluidos ciclos |
| R09 | Edición, verificación larga o datos inválidos | Invalidación, cancelación sin resultado global falso y límites claros |

## Modelo y estructura

`Automata(estados, alfabeto, inicial, finales, transiciones, etiquetas)` usa listas y transiciones `(origen, simbolo, destino)`. Epsilon se normaliza a `""`. Los subconjuntos usan tuplas en el orden original y se identifican como D0, D1, etc. Las etiquetas conservan el conjunto para dibujar y explicar.

Las ER son árboles inmutables con tipos vacío, lambda, literal, unión, concatenación y estrella. Las funciones de construcción aplican identidades algebraicas. No se evalúa una cadena de Python ni una ER textual introducida por el usuario.

| Archivo | Responsabilidad |
| --- | --- |
| `automatas.py` | Validación, índices, clausura, subconjuntos, ecuaciones, Arden, árboles ER, Thompson y comparación |
| `app.py` | Editor Tkinter, Canvas, tabla, navegación y verificación por lotes |
| `test_automatas.py` | Pruebas unittest con anexos, patrones conocidos y casos límite |
| `README.md` | Apertura en VS Code, uso, pruebas y sustentación |
| `Grupo_8.code-workspace` | Tareas y depuración con rutas relativas |

La bitácora PDF, su fuente editable y el video se entregan en la carpeta hermana `Documentos_y_video_Grupo_8`, fuera del repositorio del código. La aplicación no depende de esos archivos.

La interfaz depende del núcleo; el núcleo no importa Tkinter. La verificación reconoce el AFND por conjuntos, el AFD por un estado y la ER mediante una construcción Thompson independiente. AFND y Thompson comparten el recorrido de transiciones epsilon. Los patrones conocidos de los anexos añaden una referencia independiente en las pruebas.

## Orden de construcción y reglas

1. Validar entradas y crear el índice de transiciones.
2. Calcular la clausura inicial; recorrer la cola de subconjuntos. Por cada símbolo, mover y volver a cerrar. Crear el pozo si aparece ∅.
3. Formar ecuaciones de lenguajes derechos `Xi = suma(Aij·Xj) + bi`; `bi=λ` en finales y `bi=∅` en los demás.
4. Eliminar variables no iniciales: resolver su bucle por Arden y sustituir en todas las ecuaciones que las usan. Resolver la inicial al final.
5. Aplicar unión de alternativas, concatenación de caminos, estrella en bucles e identidades de λ y ∅. Un final conserva sus salidas.
6. Construir Thompson y comparar todos los resultados entre longitudes 0 y n.
7. Conectar la interfaz, registrar pasos y comprobar los dos anexos, capturas y cancelación.

Arden resuelve `X=A·X+B` como `A*·B`. Si λ no pertenece a A, la solución es única; con bucles epsilon se toma la solución mínima, que corresponde a caminos finitos. La traza explica esta diferencia. Enumerar hasta n aporta evidencia acotada, no una demostración universal de equivalencia.

## Entradas y límites

Los nombres de estados son únicos y no contienen espacios ni comas. Los símbolos del alfabeto son únicos, de un carácter y distintos de ε, λ y espacios. Las transiciones admiten epsilon y sus extremos deben existir; las repetidas se eliminan.

La interfaz admite hasta 12 estados originales y 8 símbolos. El conversor permite hasta 256 subconjuntos. La ER admite hasta 18 estados, 12.000 pasos y 80.000 caracteres por instantánea de la traza. El verificador exige un entero de 6 a 12 y un máximo de 350.000 palabras; al exceder un límite se informa el motivo. El alfabeto vacío enumera únicamente λ.

## Casos de aceptación

- **Anexo 1:** D0={q0}, D1={q0,q1}, D2=∅, D3={q2}; ocho transiciones. D0 inicial, D3 final, D2 pozo. ER `a·a*·b`. n=6: 127 cadenas, cinco aceptadas.
- **Anexo 2:** `Q0=x·Q1`, `Q1=x·Q2+λ`, `Q2=y·Q2+y·Q1`; ER desde el original `x·(x·y*·y)*`. n=8: 511 cadenas, 21 aceptadas.
- **Casos límite:** inicial final, ningún final, alfabeto vacío, un símbolo, inalcanzables, transiciones faltantes, ciclos epsilon, clausura después de mover y símbolos Unicode u operadores literales.
- **Control de errores:** rechazar datos inválidos y límites excedidos; detectar un AFD o una ER alterados mediante contraejemplos.
- **Interfaz:** ambos grafos completos en los anexos, pasos navegables, mensaje del verificador sincronizado, edición que invalida y cancelación sin afirmar equivalencia.

La bitácora externa reúne las decisiones técnicas y evidencias del desarrollo asistido. P01-P08 reconstruyen las fases; P09 registra la solicitud real de ampliar el video con voz y P10 la separación entre código y entregables. La revisión y sustentación personal corresponden a los integrantes.
