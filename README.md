# App de Traducción Orquestada con Docker Compose y Swarm

📜 **Descripción general**

Construcción de una aplicación de traducción de texto que usa un modelo generativo (Gen-AI), registra cada interacción con MLflow Tracking, y se define y ejecuta usando Docker Compose para el desarrollo local. Posteriormente, se despliega como un stack orquestado en Docker Swarm para demostrar escalabilidad y gestión de servicios.

🎯 **Requisitos obligatorios**

- ✅ Interfaz web con Gradio (ingreso de texto, selección de idioma, resultado)
- ✅ Registro de cada interacción en MLflow (texto original, idioma, traducción, timestamp)
- ✅ Entorno de desarrollo local con docker-compose.yml
- ✅ Despliegue en Docker Swarm con docker-stack.yml
- ✅ Imagen publicada en Docker Hub

🏛️ **Estructura del trabajo**

### Parte A — App de traducción (Desarrollo local)
- Interfaz Gradio con campo texto, selector idioma, botón traducir, área de resultado
- Integración con SDK de Gen-AI para obtener traducciones
- Configuración de URI de MLflow desde variable de entorno
- Pruebas locales sin Docker

### Parte B — Integración con MLflow Tracking
- Creación automática de runs en MLflow por cada traducción
- Registro de parámetros (idioma, modelo), métricas (latencia, longitud) y artefactos
- Configuración de conexión remota a servidor MLflow

### Parte C — Orquestación local con Docker Compose
- Dockerfile para la aplicación con Python 3.11
- docker-compose.yml con dos servicios: app-traductor y mlflow-server
- Volúmenes persistentes para base de datos y artefactos
- Red común para comunicación entre servicios

### Parte D — Despliegue en Producción con Docker Swarm
- docker-stack.yml adaptado para Swarm con imagen de Docker Hub
- Configuración de réplicas y políticas de reinicio
- Red overlay para comunicación multi-nodo
- Escalabilidad dinámica del servicio

📁 **Estructura del proyecto**

```
directorio/
├── chatbotgradio.py          # Aplicación principal con Gradio
├── Dockerfile               # Imagen Docker para la app
├── docker-compose.yml       # Orquestación local
├── docker-stack.yml         # Orquestación Swarm
├── requirements.txt         # Dependencias Python
└── .env                    # Variables de entorno (API_KEY)
```

� **Instalación y ejecución**

### Desarrollo local
```bash
# 1. Configurar variables de entorno
export OPEN_ROUTER_API_KEY=tu_api_key

# 2. Levantar stack local
docker-compose up --build

# 3. Acceder a las aplicaciones
# Gradio: http://localhost:7860
# MLflow: http://localhost:5000
```

### Producción con Swarm
```bash
# 1. Inicializar Swarm
docker swarm init

# 2. Publicar imagen en Docker Hub
docker tag app-traductor usuario/traductor-genai:1.0.0
docker push usuario/traductor-genai:1.0.0

# 3. Desplegar stack
docker stack deploy -c docker-stack.yml traductor_stack

# 4. Escalar servicio
docker service scale traductor_stack_app-traductor=3
```

🔧 **Componentes técnicos**

### Servicios Docker
- **app-traductor**: Aplicación Gradio con lógica de traducción integrada (puerto 7860)
- **mlflow-server**: Servidor MLflow para tracking de experimentos (puerto 5000)

### Arquitectura General
El proyecto utiliza una arquitectura basada en microservicios ejecutados en contenedores Docker. Los servicios principales son:
- **app-traductor**: Aplicación Gradio que incluye la interfaz web y la lógica de traducción (expuesto en puerto 7860)
- **mlflow-server**: Servidor MLflow para registro y monitoreo de experimentos (expuesto en puerto 5000)

En Docker Compose, los servicios comparten una red bridge y usan volúmenes locales. En Swarm, los servicios se ejecutan como réplicas dentro de una red overlay distribuida.

### Diferencias entre docker-compose.yml y docker-stack.yml
- **Compose**: Permite build directo desde Dockerfile, orientado a desarrollo local
- **Swarm**: Requiere imagen ya publicada (directiva `image` en lugar de `build`)
- **Deploy**: Swarm utiliza sección `deploy` para configurar réplicas, reinicios y restricciones
- **Redes**: Compose usa `bridge`, Swarm usa `overlay` para comunicación multi-nodo
- **Volúmenes**: En Swarm deben manejarse mediante drivers distribuidos o declaración externa

### Comandos Principales
```bash
# Desarrollo local
docker-compose up -d                    # Levanta servicios locales
docker-compose build                   # Construye imágenes de desarrollo

# Producción Swarm
docker swarm init                      # Inicializa cluster Swarm
docker stack deploy -c docker-stack.yml traductor_stack  # Despliega aplicación
docker service ls                       # Lista servicios en ejecución
docker service scale traductor_stack_app-traductor=3   # Escala réplicas
docker push usuario/traductor-genai:1.0.0   # Publica imagen en Docker Hub
docker pull usuario/traductor-genai:1.0.0   # Descarga imagen desde Docker Hub
```

### Observaciones sobre Rendimiento
La latencia del servicio depende de la carga del cluster y del modelo de traducción utilizado:
- **Entorno local (Compose)**: Latencia baja sin red distribuida
- **Entorno Swarm**: Latencia ligeramente mayor debido al enrutamiento interno entre nodos
- **Calidad de traducción**: Resultados consistentes para textos cortos y medianos
- **Escalabilidad**: Desempeño estable al escalar réplicas del servicio

### Modelos de IA disponibles
- Google: gemma-3-27b-it, gemini-2.0-flash-exp
- Qwen: qwen3-14b, qwen-2.5-72b-instruct
- DeepSeek: deepseek-r1-distill-llama-70b, deepseek-r1-0528-qwen3-8b

### Idiomas soportados
Español, Inglés, Francés, Alemán, Italiano, Portugués, Chino, Japonés

📊 **Monitoreo con MLflow**

Cada traducción registra:
- **Parámetros**: idioma_origen, idioma_destino, modelo, proveedor, input_length
- **Métricas**: latencia_ms, output_length, length_ratio
- **Artefactos**: JSON con timestamp, textos, y métricas completas

🐳 **Configuración Docker**

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY chatbotgradio.py .
EXPOSE 7860
CMD ["sh", "-c", "sleep 10 && python chatbotgradio.py"]
```

### Volúmenes persistentes
- `mlflow-db-data`: Base de datos de experimentos
- `mlflow-artifacts-data`: Artefactos y logs

🔍 **Verificación del despliegue**

```bash
# Ver servicios del stack
docker stack services traductor_stack

# Ver réplicas activas
docker service ls

# Ver logs de servicios
docker service logs traductor_stack_app-traductor
```

� **Notas importantes**

- La aplicación espera 10 segundos antes de iniciar para asegurar que MLflow esté disponible
- Los modelos gratuitos de OpenRouter tienen límites de uso
- Los volúmenes aseguran persistencia de datos entre reinicios
- Swarm utiliza routing mesh para balanceo de carga automático