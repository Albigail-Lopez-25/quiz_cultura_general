#Título del programa: juego_gui_completo
#Autor:Guadalupe Albigail Huerta López 
#Fecha: 26/06/2026
#Descripción:

import json
import os
import sqlite3
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox

#aqui estan las clases que se hicieron en la unidad 2 pero no se utilizaron todas
#clase que representa al estudiante que juefa la partida y que aguarda sus datos
class Jugador: 
    def __init__(self, nombre: str):
        self.__nombre = nombre
        self.__puntaje = 0
        self.__vidas = 3

#es un decorador property para permitir la lectura del nombre pero impedir la modificacion
    @property
    def nombre(self):
        return self.__nombre

#metodo get publico para obtener el valor del puntaje privado    
    def get_puntaje(self):
        return self.__puntaje
    
    def get_vidas(self):
        return self.__vidas

#aumenta el puntaje acumulado si el valor de puntos es positivo 
    def aumentar_puntaje(self, puntos: int):
        if puntos > 0:
            self.__puntaje += puntos

    def restar_vida(self):
        self.__vidas -= 1

class ElementoJuego:
#esta es la clase base para definir la estructura general de los componetes del juego
    def mostrar(self):
        print(f"Mostrando elemento basico de juego")

    def correctos(self, respuesta):
        return False

#clase hija especializada en reactivos de opcion multiple con 4 opciones   
class PreguntaMultiple(ElementoJuego):
    def __init__(self, texto: str, opciones: list, indice_correcto: int):
        self.texto = texto
        self.opciones = opciones
        self.indice_correcto = indice_correcto

#sobrescrito el metodo del padre para validar por numero o texto exacto
    def correctos(self, respuesta: str):
        texto_correcto = self.opciones[self.indice_correcto]
        numero_correcto = str(self.indice_correcto + 1)
        usuario = respuesta.strip().lower()
#la estructura de desicion logica que retorna true si concide con alguna de las dos opciones validas
        return usuario == numero_correcto or usuario == texto_correcto.strip().lower()
    
#aqui se esta utilizando la unidad 2 y 3 lo cual es la persistencia y la conexion a base de datos 
#maneja la creacion de la bsae de datos local y las operaciones crud de puntuaciones 
class Ranking:
    def __init__(self):
        carpeta_actual = os.path.dirname(os.path.abspath(__file__))  #el os.path.dirname se utiliza para extraer la ruta de la carpeta 
        ruta_db = os.path.join(carpeta_actual, "ranking.db")

#establece lo que es a conexion con sqlite
        self.conexion = sqlite3.connect(ruta_db)
        self.cursor = self.conexion.cursor()

#es la estructura estricta sql para crear la tabla si no existe previamente
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS puntuaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jugador TEXT,
                puntaje INTEGER,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)    
        self.conexion.commit()

#se inserte un nuevo registro en la tabla de base de datos 
    def guardar(self, nombre: str, puntaje: int):
        self.cursor.execute ("""
            INSERT INTO puntuaciones (jugador, puntaje)
            VALUES (?, ?)
            """, (nombre, puntaje))
        self.conexion.commit()

#se ejecuta una consulta ordenada descendentemente limitando los datos al top 5
    def obtener_top5(self):
        self.cursor.execute("""
            SELECT jugador, puntaje FROM puntuaciones
            ORDER BY puntaje DESC
            LIMIT 5
        """)
#retorna una lista de tuplas para recorrer en la GUI
        return self.cursor.fetchall() #para recuperar todas la filas o registros

#se cierra el flujo de conexion con la base de datos de manera segura
    def cerrar(self):
        self.conexion.close()

#aqui empieza lo de la unidad 3 que es la interfaz gui y las estructuras de control principales 
#esta clase es la que controla principal la interfaz visual con tkinter
class JuegoGUI:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title(f"Quiz Game")
        self.ventana.geometry("560x440")
        self.ventana.config(bg="white")
        
#es la inicialización de variables de control de flujo
        self.jugador = None
        self.banco_preguntas = []
        self.preguntas_partida = []
        self.indice_actual = 0
        self.ranking_db = Ranking() #aqui es la instancia de la conexión a Base de Datos
        
#es la estructura de control que lee el archivo JSON dinámicamente
        self.preguntas_iniciales()

#la creación de la barra de menú superior interactiva
        self.menu_superior()

#es el frame contenedor dinámico (actúa como switch de pantallas borrando y redibujando widgets)
        self.pantalla_activa = tk.Frame(self.ventana, bg="white")
        self.pantalla_activa.pack(fill="both", expand=True)

# es la que cargar por defecto la primera sección que es el inicio
        self.vista_inicio()

#es el que lee el archivo JSON de preguntas utilizando validación y manejo de excepciones.
    def preguntas_iniciales(self):
        self.banco_preguntas = []
        carpeta = os.path.dirname(os.path.abspath(__file__))
        ruta_json = os.path.join(carpeta, "preguntas.json")
        
# Estructura condicional (Unidad 3) para verificar si el archivo físico existe
        if os.path.exists(ruta_json):
            try:
                with open(ruta_json, 'r', encoding='utf-8') as archivo:
                    datos = json.load(archivo)
                
# Bucle 'for' para instanciar dinámicamente los objetos correctos 
                for item in datos:
                    texto_p = item.get("pregunta") or item.get("texto")
                    opciones = item.get("opciones") 
                    indice_c = item.get("correcta") 

                    if texto_p and opciones and isinstance(indice_c, int):
                        self.banco_preguntas.append(PreguntaMultiple(texto_p, opciones, indice_c))

            except Exception:
                self.banco_preguntas = []
        else:
            self.banco_preguntas = []

#la estructura iterativa 'for' que destruye los widgets previos para redibujar la pantalla.
    def limpiar_pantalla(self):
        for widget in self.pantalla_activa.winfo_children():
            widget.destroy()

#se configura el elemento superior de navegación (Widget Menu)
    def menu_superior(self):
        barra_menu = tk.Menu(self.ventana)
        
        submenu = tk.Menu(barra_menu, tearoff=0)
        submenu.add_command(label=f"Pantalla de Inicio", command=self.vista_inicio)
        submenu.add_command(label=f"Jugar Nueva Ronda", command=self.inicializar_partida)
        submenu.add_command(label=f"Ver Tabla de Puntuaciones", command=self.mostrar_vista_ranking)
        submenu.add_separator()
        submenu.add_command(label=f"Salir del quiz", command=self.cerrar_juego_completo)
        
        barra_menu.add_cascade(label="Opciones del Sistema", menu=submenu)
        self.ventana.config(menu=barra_menu)

#vistas principales 
# Genera el formulario de bienvenida y captura el nombre del estudiante
    def vista_inicio(self):
        self.limpiar_pantalla()

        label_bienvenida = tk.Label(
            self.pantalla_activa, text=f"JUEGO QUIZ GAME", 
            font=("Times New Roman", 16, "bold"), background="white", foreground="black"
        )
        label_bienvenida.pack(pady=40)

        label_ayuda_nombre = tk.Label(
            self.pantalla_activa, text=f"Por favor ingresa tu nombre: ", 
            font=("Times New Roman", 11), background="white", foreground="black"
        )
        label_ayuda_nombre.pack(pady=5)

        self.entry_nombre = tk.Entry(self.pantalla_activa, font=("Times New Roman", 12), width=25, justify="center")
        self.entry_nombre.pack(pady=10)
        self.entry_nombre.insert(0, "")

# Botón de arranque de juego
        button_iniciar = tk.Button(
            self.pantalla_activa, text=f"Comenzar", font=("Times New Roman", 11, "bold"),
            background="white", foreground="black", padx=20, pady=8, bd=0, cursor="hand2", #padx y pady utilizan tkinter para añadir espacios de separacion
            command=self.inicializar_partida
        )
        button_iniciar.pack(pady=35)

#Estructura que valida datos obligatorios y selecciona las preguntas al azar.
    def inicializar_partida(self):
        nombre_ingresado = ""
        if hasattr(self, 'entry_nombre') and self.entry_nombre.winfo_exists():
            nombre_ingresado = self.entry_nombre.get().strip() #hasattr es una función que se utiliza para verificar si un objeto tiene un atributo o un método específico.
        else:
            nombre_ingresado = ""
        
#Validación de campo vacío (Unidad 3)
        if not nombre_ingresado:
            messagebox.showwarning(f"Atención", "El nombre del jugador es obligatorio para registrar la puntuación.")
            return
        
#si no hay menos de 5 preguntas lanza error y no inicia
        if len(self.banco_preguntas) < 5:
            messagebox.showerror(f"Error", "El archivo de preguntas contiene menos de 5 reactivos. No se puede iniciar.")
            return

#Instanciación del objeto Jugador con los datos validados (Unidad 2)
        self.jugador = Jugador(nombre_ingresado)

#se selecciona 5 preguntas al alzar
        self.preguntas_partida = random.sample(self.banco_preguntas, k=5)
        self.indice_actual = 0

#inica el tiempo
        self.tiempo_inicio = time.time()

        self.renderizar_pregunta_actual()

#Bucle visual controlado condicionalmente para pintar reactivos múltiples o binarios.
    def renderizar_pregunta_actual(self):
        self.limpiar_pantalla()

#Estructura de Control Condicional: Si ya se contestaron todas las preguntas elegidas
        if self.indice_actual >= len(self.preguntas_partida) or self.jugador.get_vidas() <=0:
            self.tiempo_total = round(time.time() - self.tiempo_inicio, 2)
            self.finalizar_partida()
            return

        pregunta = self.preguntas_partida[self.indice_actual]

#Estado del Jugador (Uso de métodos get y properties de la Unidad 2)
        label_info_top = tk.Label(
            self.pantalla_activa,
            text=f"Jugador: {self.jugador.nombre} Puntaje: {self.jugador.get_puntaje()} pts Vidas: {self.jugador.get_vidas()} Pregunta {self.indice_actual + 1} de {len(self.preguntas_partida)}",
            font=("Times New Roman", 10, "bold"), background="white", foreground="black", anchor="w", padx=10
        )
        label_info_top.pack(fill="x", pady=(0, 20))

#Enunciado del reactivo
        label_enunciado = tk.Label(
           self.pantalla_activa, text=pregunta.texto,
            font=("Times New Roman", 12, "bold"), background="white", foreground="blue", wraplength=500, justify="center"
        )
        label_enunciado.pack(pady=20)

#Variable de Tkinter ligada a la selección de opciones
        self.variable_opcion = tk.StringVar()

#CONTROL DE POLIMORFISMO para pintar componentes dinámicos según el tipo de objeto
        frame_contenedor_rb = tk.Frame(self.pantalla_activa, bg="white")
        frame_contenedor_rb.pack(pady=5)

#Estructura iterativa 'for' para dibujar las 4 opciones de la lista
        for i, opcion in enumerate(pregunta.opciones):
            rb = tk.Radiobutton(
                frame_contenedor_rb, text=f"{i + 1}. {opcion}", variable=self.variable_opcion,
                value=str(i + 1), font=("Times New Roman", 11), background="white", anchor="w", width=35
            )
            rb.pack(pady=3)

#Botón único para enviar respuestas de tipo múltiple
        button_enviar_multiple = tk.Button(
            self.pantalla_activa, text="Validar Respuesta", font=("Times New Roman", 10, "bold"),
            background="orange", foreground="white", padx=15, pady=6, bd=0, cursor="hand2",
            command=self.validar_seleccion_multiple
        )
        button_enviar_multiple.pack(pady=20)

#Valida que el Radiobutton no esté vacío antes de enviarlo al evaluador.
    def validar_seleccion_multiple(self):
        seleccion = self.variable_opcion.get()
        if not seleccion:
            messagebox.showwarning(f"Falta Selección", "Debes seleccionar una opción antes de continuar.")
            return
        self.avanzar_juego(seleccion)

#Llama a las validaciones lógicas propias de tus clases agregando puntajes correspondientes.
    def avanzar_juego(self, respuesta_alumno):
        pregunta_actual = self.preguntas_partida[self.indice_actual]

# Llamada polimórfica a tus métodos de validación personalizados
        if hasattr(pregunta_actual, 'correctos') and pregunta_actual.correctos(respuesta_alumno):
            messagebox.showinfo(f"Resultado Correcto", "Excelente respuesta (+10 pts)")
            self.jugador.aumentar_puntaje(10)
        else:
            self.jugador.restar_vida()
            messagebox.showerror("Resultado Incorrecto", f"La respuesta es incorrecta, te quedan {self.jugador.get_vidas()} vidas. (-1 vida)")

# Control de flujo incremental (Unidad 3) para avanzar al siguiente elemento de la lista
        self.indice_actual += 1
        self.renderizar_pregunta_actual()

#Inserta automáticamente la puntuación final en SQLite y pinta los resultados
    def finalizar_partida(self):
        self.limpiar_pantalla()

# Ejecución del método guardar de la clase Ranking (Inserción SQL)
        self.ranking_db.guardar(self.jugador.nombre, self.jugador.get_puntaje())

        motivo_fin = "Perdiste " if self.jugador.get_vidas() <= 0 else "Quiz terminado"

        label_terminado = tk.Label(
            self.pantalla_activa, text="Cuestionario Concluido", 
            font=("Times New Roman", 16, "bold"), background="white", foreground="Black"
        )
        label_terminado.pack(pady=25)

        label_score_final = tk.Label(
            self.pantalla_activa, 
            text=f"Felicidades , {self.jugador.nombre}.\n\nPuntaje: {self.jugador.get_puntaje()} Puntos\nTiempo total: {self.tiempo_total} segundos",
            font=("Times New Roman", 13, "bold"), background="white", foreground="black"
        )
        label_score_final.pack(pady=15)

        messagebox.showinfo(f"Resultados", f"Quiz terminado.\nPuntaje total: {self.jugador.get_puntaje()} pts\nTiempo total: {self.tiempo_total}s")

        button_ver_posiciones = tk.Button(
            self.pantalla_activa, text=f"Consultar Tabla de Clasificación", font=("Times New Roman", 10, "bold"),
            background="blue", foreground="white", padx=12, pady=6, bd=0, cursor="hand2",
            command=self.mostrar_vista_ranking
        )
        button_ver_posiciones.pack(pady=20)

#Recupera los datos de SQLite y los dibuja ordenadamente usando un Treeview tabular.
    def mostrar_vista_ranking(self):
        self.limpiar_pantalla()

        label_title_tabla = tk.Label(
            self.pantalla_activa, text="TOP 5 ", 
            font=("Times New Roman", 14, "bold"), background="white", foreground="black"
        )
        label_title_tabla.pack(pady=15)

# Configuración del componente Treeview (Tabla estructurada de Tkinter)
        columnas_tabla = ("pos", "jugador", "puntos")
        tabla_grafica = ttk.Treeview(self.pantalla_activa, columns=columnas_tabla, show="headings", height=5)
        tabla_grafica.pack(pady=10, padx=25, fill="x")

# Configurar encabezados visuales
        tabla_grafica.heading("pos", text="Posición")
        tabla_grafica.heading("jugador", text="Nombre del jugador")
        tabla_grafica.heading("puntos", text="Puntaje Total")

# Formato de dimensiones de columnas
        tabla_grafica.column("pos", width=75, anchor="center")
        tabla_grafica.column("jugador", width=250, anchor="w")
        tabla_grafica.column("puntos", width=120, anchor="center")

# Estructura secuencial de lectura desde SQLite
        mejores_marcas = self.ranking_db.obtener_top5()
        
# Bucle iterativo 'for' de la Unidad 3 para insertar las tuplas de la DB en las filas del componente gráfico
        for posicion_indice, fila_tupla in enumerate(mejores_marcas):
            tabla_grafica.insert("", "end", values=(f"{posicion_indice + 1}°", fila_tupla[0], f"{fila_tupla[1]} pts"))

        button_regresar_menu = tk.Button(
            self.pantalla_activa, text="Regresar a inicio", font=("Times New Roman", 10, "bold"),
            background="white", foreground="blue", padx=12, pady=5, bd=0, cursor="hand2",
            command=self.vista_inicio
        )
        button_regresar_menu.pack(pady=20)

#Elimina de forma controlada la ventana y finaliza los hilos de memoria de SQLite.
    def cerrar_juego_completo(self):
        self.ranking_db.cerrar()
        self.ventana.destroy()

if __name__ == "__main__":
# Inicializa el motor raíz de ventanas de Tkinter
    ventana_raiz = tk.Tk()
# Pasa el elemento raíz a nuestra clase constructora
    aplicacion_juego = JuegoGUI(ventana_raiz)
# Abre el bucle persistente de refresco gráfico de la aplicación
    ventana_raiz.mainloop()
