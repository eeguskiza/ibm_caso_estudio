# Sistema IBM "Caso de Estudio" — Resolucion de ejercicios de memoria virtual

Herramienta interactiva para resolver paso a paso ejercicios de memoria virtual
del sistema IBM System/370 (caso de estudio). Descompone direcciones virtuales,
analiza PTEs, ejecuta el algoritmo LRU de 2a oportunidad, calcula EPAs en disco
DASD y genera informes HTML visuales con todos los calculos intermedios.

## Requisitos

- Python 3.10+ (sin dependencias externas)

## Como ejecutar

```bash
python main.py
```

## Modos de uso

1. **Ejercicios precargados** — Selecciona un ejercicio del PDF o de los apuntes
   y el programa lo resuelve completo mostrando cada paso.

2. **Modo interactivo** — Introduce tus propios datos paso a paso (disco, RSIZE,
   direccion virtual, PTE, colas LRU...) y obtiene la solucion guiada.

3. **Calculadora rapida** — Operaciones sueltas: descomponer dV, analizar PTE,
   calcular EPA, construir BI(0)/BI(1), etc.

Al finalizar cada ejercicio se puede generar un **informe HTML** con los
resultados formateados, colores y tablas, listo para imprimir o entregar.

## Estructura del proyecto

```
ibm_caso_estudio/
├── main.py          Punto de entrada, menus y flujo interactivo
├── solver.py        Logica de calculo pura (funciones sin prints)
├── display.py       Impresion formateada por terminal (cajas Unicode)
├── exercises.py     Ejercicios precargados del PDF y apuntes
├── report.py        Generacion de informe HTML standalone
└── README.md        Este archivo
```

## Contexto

Asignatura de **Sistemas Operativos** — Universidad de Deusto.
Caso de estudio: traduccion de direcciones virtuales con DAT, reemplazamiento
de paginas mediante LRU de 2a oportunidad y gestion de almacenamiento en disco
DASD (modelos 3330, 3340, 3350).

## Autor

Erik Eguskiza Aranda
