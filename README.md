# Simulador de autómatas - Grupo 8

**FABER ENRIQUE UNI GOMEZ · JAIR DANIEL ROSADO RIASCOS · JUAN FELIPE TORREZ**

Aplicación de escritorio en **Python + Tkinter** para convertir AFND a AFD, obtener expresiones regulares por ecuaciones y comparar los tres reconocedores. Funciona localmente con la biblioteca estándar, sin paquetes de pip, servidor ni internet.

## Abrir en Visual Studio Code

1. Clonar el repositorio o extraer el ZIP del código; no ejecutar desde la vista del archivo comprimido.
2. Abrir `Grupo_8.code-workspace` con Visual Studio Code. Si aparece la confianza del espacio de trabajo, revisar y confiar en esta carpeta para habilitar sus tareas.
3. Pulsar **Ctrl+Mayús+B**: abre el simulador. También se puede usar **F5** con la extensión Python y su depurador.
4. Para las pruebas: **Terminal → Ejecutar tarea → Comprobar algoritmos**.

Se requiere **Python 3.10 o posterior con Tkinter**. En Windows, el instalador oficial de Python suele incluir Tcl/Tk. `python -m tkinter` permite comprobarlo. Si `python` no está disponible, configurar Python en PATH; para F5, seleccionar el intérprete instalado con **Python: Select Interpreter**.

También se puede abrir una terminal en esta carpeta:

```powershell
python app.py
python -B -m unittest -v
```

El espacio de trabajo usa rutas relativas y no depende de la ubicación de este equipo. No hace falta crear un entorno virtual ni instalar dependencias.

## Archivos

```text
Simulador_Python_Grupo_8/
  Grupo_8.code-workspace   Acceso a ejecución, depuración y pruebas
  app.py                  Interfaz Tkinter
  automatas.py            Algoritmos y modelo de datos
  test_automatas.py        Pruebas automáticas
  README.md               Ejecución, uso y comprobaciones
  SPEC.md                 Requisitos, arquitectura y casos límite
  .gitignore              Exclusiones de archivos temporales
```

Esta carpeta contiene el código para GitHub, las pruebas y su documentación técnica. La bitácora PDF, su fuente editable y el video se entregan por separado en la carpeta hermana **Documentos_y_video_Grupo_8**. No son necesarios para ejecutar ni probar el simulador.

## Uso de la aplicación

1. Cargar **Caso 1 del anexo**, **Caso 2 del anexo** o **Bonus epsilon**, o editar estados, alfabeto, inicial, finales y transiciones.
2. Escribir una transición por línea: `q0 a q1`. Repetir origen y símbolo en otra línea para varios destinos. Para epsilon: `q0 ε q1`.
3. Pulsar **Convertir a AFD**. Revisar los grafos, la tabla y cada paso conjunto/símbolo. `∅` es el pozo; `★` marca finales y `→` el inicial. Los botones permiten recorrer los pasos.
4. En **Autómata → ER**, elegir **AFD convertido** para el flujo completo o **Autómata original**. Obtener la ER y recorrer las ecuaciones, reglas, sustituciones y simplificaciones.
5. En **Verificador**, elegir n de 6 a 12 y ejecutar. Se enumeran todas las cadenas de longitud 0 a n, incluida λ. Se muestran total, aceptadas por motor y todas las diferencias, si existen. Se puede cancelar.

Editar la entrada descarta los resultados anteriores. Los datos se conservan mientras la ventana está abierta; los ejemplos están incorporados en el código.

Los estados se separan por comas y no contienen espacios ni comas. El alfabeto admite `a,b` o una lista JSON como `["a", ","]`; cada símbolo tiene un carácter. ε y λ están reservados para la cadena vacía. La notación ER es `+` unión, `·` concatenación, `*` estrella, `λ` cadena vacía y `∅` lenguaje vacío. Los símbolos que parecen operadores se muestran entre comillas.

## Resultados comprobados

**19 pruebas automáticas correctas**: anexos, tabla exacta, flujo AFND → AFD → ER, reglas básicas, inicial final, ciclos epsilon, inalcanzables, pozo, ausencia de finales, alfabetos vacío y de un símbolo, Unicode, validación, límites y contraejemplos. Incluyen 100 AFND con semilla 20261014, comprobados hasta n=6: 12.700 palabras en total. En los anexos también se compara con patrones esperados independientes hasta n=8.

La revisión de integración comprobó nueve aspectos de la ventana: carga, grafos completos, ambos anexos, navegación, epsilon, invalidación, cancelación, tamaño mínimo y ejecución con conexiones de red bloqueadas en el proceso. La bitácora contiene las capturas reales y el detalle de los dos errores corregidos.

| Ejemplo | Resultado esperado | Comprobación |
| --- | --- | --- |
| Caso 1 | `{q0}`, `{q0,q1}`, `∅`, `{q2}`; D0 inicial, D2 pozo, D3 final; ER `a·a*·b` | n=6: 127 cadenas, 5 aceptadas por cada motor, 0 diferencias |
| Caso 2 | Desde el original: `x·(x·y*·y)*` | n=8: 511 cadenas, 21 aceptadas por cada motor, 0 diferencias |
| Bonus epsilon | Clausura inicial `{s,p}`; lenguaje `a*·b` | Clausura inicial y posterior al movimiento comprobadas |

En el caso 1 se aceptan `ab`, `aab` y `aaab`; se rechazan λ, `a`, `b` y `abb`. En el caso 2 se aceptan `x`, `xxy` y `xxyy`; se rechazan λ, `xx` y `xy`. Desde el AFD pueden aparecer ER escritas de otra forma que describen el mismo lenguaje. La enumeración acotada no demuestra equivalencia para longitudes mayores.

## Diseño y límites

`automatas.py` no depende de Tkinter. Construye subconjuntos alcanzables con una cola y clausura epsilon; un subconjunto es final si contiene algún final original. El pozo se añade cuando es alcanzable.

Para la ER forma `Xi = suma(Aij·Xj) + bi`. Un final aporta λ y conserva sus transiciones. Elimina variables mediante sustitución y Arden; resuelve al final la variable inicial. Se calcula la solución mínima de lenguajes de caminos finitos; la unicidad de Arden requiere que el coeficiente del bucle no contenga λ.

La ER es un árbol inmutable. Thompson construye otro AFND a partir de ella. El verificador usa tres recorridos: conjuntos para el AFND original, un estado para el AFD y Thompson para la ER. La interfaz verifica en lotes de 128 palabras con `after` para permitir cancelar.

Límites: 12 estados originales, 8 símbolos, 256 subconjuntos, 18 estados para ER, n de 6 a 12 y hasta 350.000 palabras. La traza de ER también tiene límites de tamaño. Con un AFD grande, elegir el original como fuente de ER. Los grafos grandes tienen desplazamiento.

## Correspondencia con la guía

| Requisito | Ubicación |
| --- | --- |
| Fases 0 y 1: especificación, arquitectura y modelo | `SPEC.md` |
| Fase 2: algoritmos puros y pruebas del Anexo A | `automatas.py` y `test_automatas.py` |
| Fases 3 y 4: interfaz, grafos y explicación | `app.py`; demostración en la entrega externa |
| Fase 5: dos bugs con síntoma, causa, corrección y regresión | Bitácora de la entrega externa |
| Fase 6: revisión, refactor e instrucciones | Este README, código y pruebas |
| Verificador obligatorio y bonus epsilon | Pestaña Verificador, ejemplo Bonus epsilon y pruebas |
| Código, bitácora PDF y video menor de tres minutos | Repositorio y carpeta externa de documentos/video |

La carpeta externa contiene `Bitacora.pdf`, `Bitacora.md` y `Demo.webm`. El video dura 2 minutos y 45 segundos y tiene narración sintética en español. El repositorio del código excluye estos entregables mediante `.gitignore`.

## Preparación de la sustentación

Cada integrante debe poder repetir este recorrido y explicar su razonamiento:

1. **Minuto 0-1:** editar el caso 1 y explicar estados, símbolos, inicial y finales.
2. **Minuto 1-2:** recorrer un subconjunto y explicar clausura, destino y pozo.
3. **Minuto 2-3:** resolver el caso 2: `Q2=y*·y·Q1`, `Q1=(x·y*·y)*`, `Q0=x·Q1`.
4. **Minuto 3-4:** verificar hasta n=6 y explicar por qué son 127 cadenas y qué sería un contraejemplo.
5. **Minuto 4-5:** cargar un autómata nuevo y hacer un cambio pequeño, por ejemplo el texto del título en `app.py`, comprendiendo el código que se modifica.

La sustentación individual es una actividad que los integrantes deben realizar; no queda sustituida por el video ni por las pruebas automáticas.
