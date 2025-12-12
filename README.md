```markdown
# 🧩 Servidor MCP-Odoo

Este proyecto implementa un **servidor MCP (Model Context Protocol)** que permite conectar **Odoo** con agentes de IA (como ChatGPT o sistemas basados en MCP), exponiendo datos y operaciones del ERP mediante herramientas seguras y modulares.

El objetivo es habilitar consultas y automatizaciones inteligentes sobre **proyectos, tareas y usuarios de Odoo**, sin exponer la base de datos directamente.

---

## 🚀 Características principales

- 🌐 Conexión segura con **Odoo XML-RPC**
- 🧱 Arquitectura modular con herramientas desacopladas (`tools/`)
- 🤖 Compatible con **ChatGPT Connectors** y **Deep Research**
- ⚙️ Soporte para Odoo 14 a 17
- ☁️ Despliegue rápido en **AWS App Runner** o local vía Docker

---

## 🗂️ Estructura del proyecto

```

mcp-odoo/
│
├── Dockerfile
├── Makefile
├── pyproject.toml
├── build.sh
├── README.md
│
├── odoo_client.py        # Cliente XML-RPC base para Odoo
├── server.py             # Servidor FastMCP con registro automático de tools
│
└── tools/
├── projects.py       # Herramientas para proyectos (project.project)
├── tasks.py          # Herramientas para tareas (project.task)
└── users.py          # Herramientas para usuarios (res.users)

````

---

## ⚙️ Instalación local

### 1️⃣ Crear entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
````

### 2️⃣ Instalar dependencias

```bash
pip install -U "mcp[server]" uvicorn pydantic xmlrpc-client
```

### 3️⃣ Configurar variables de entorno

```bash
export ODOO_URL=https://<tu_odoo>.odoo.com
export ODOO_DB=<nombre_de_base>
export ODOO_USER=<usuario@dominio.com>
export ODOO_PASS=<contraseña>
```

### 4️⃣ Ejecutar el servidor

```bash
uvicorn server:mcp_app --reload --port 8000
```

### 5️⃣ Probar el health check

```bash
curl http://localhost:8000/health
```

---

## ☁️ Despliegue en AWS App Runner

### 1️⃣ Construir y subir la imagen Docker

```bash
bash build.sh
```

El script:

* Inicia sesión en ECR
* Construye la imagen Docker
* La etiqueta y publica en tu repositorio ECR

### 2️⃣ Crear servicio App Runner

1. Ir a **AWS Console → App Runner → Create Service**
2. Fuente: `Container image (ECR)`
3. Puerto: `8000`
4. Ruta de health check: `/health`
5. Variables de entorno:

   ```bash
   ODOO_URL=https://<tu_odoo>.odoo.com
   ODOO_DB=<nombre_de_base>
   ODOO_USER=<usuario@dominio.com>
   ODOO_PASS=<contraseña>
   ```

App Runner desplegará automáticamente tu servidor MCP en una URL como:

```
https://xxxxx.us-east-1.awsapprunner.com
```

---

## 🧠 Herramientas MCP disponibles

### 🌍 Ambientes: Producción vs Desarrollo

Este servidor MCP soporta **dos ambientes diferentes**:

#### **PRODUCCIÓN** (Solo Lectura)
- **Herramientas**: `list_projects`, `list_tasks`, `get_task`, `list_users`, `list_sales`, `get_sale`, `search`, `fetch`
- **Propósito**: Consultar datos reales sin modificarlos
- **Variables**: `ODOO_URL`, `ODOO_DB`, `ODOO_LOGIN`, `ODOO_API_KEY`

#### **DESARROLLO** (Lectura y Escritura) 🆕
- **URL**: https://pegasuscontrol-dev18-25468489.dev.odoo.com
- **Herramientas**: `dev_create_sale`, `dev_create_sale_line`, `dev_update_sale`, `dev_read_sale`
- **Propósito**: Crear y modificar órdenes de venta de prueba
- **Variables**: `DEV_ODOO_URL`, `DEV_ODOO_DB`, `DEV_ODOO_LOGIN`, `DEV_ODOO_API_KEY`

> 📖 **Ver ejemplos completos en**: [EJEMPLOS_SALES.md](EJEMPLOS_SALES.md)

---

### 📚 Herramientas de PRODUCCIÓN (Solo Lectura)

### 🔹 `list_projects`

Lista proyectos desde Odoo con filtros opcionales.

**Argumentos:**

* `q`: texto parcial (ilike)
* `active`: True/False/None
* `limit`: límite de resultados

**Ejemplo:**

```json
{
  "tool": "list_projects",
  "arguments": { "q": "demo", "limit": 10 }
}
```

---

### 🔹 `list_tasks`

Lista tareas filtradas por proyecto, usuario o nombre de usuario.

**Argumentos:**

* `project_id`: id del proyecto
* `assigned_to`: id del usuario asignado
* `assigned_to_name`: nombre del usuario (busca automáticamente su ID)
* `q`: texto parcial (ilike)
* `limit`: límite de resultados

**Ejemplo:**

```json
{
  "tool": "list_tasks",
  "arguments": { "assigned_to_name": "Julio", "limit": 5 }
}
```

---

### 🔹 `list_sales` 🆕

Lista órdenes de venta desde Odoo con filtros opcionales.

**Argumentos:**

* `partner_id`: id del cliente (res.partner)
* `user_id`: id del vendedor (res.users)
* `state`: estado de la orden ('draft', 'sent', 'sale', 'done', 'cancel')
* `q`: texto parcial para búsqueda por nombre/referencia
* `limit`: límite de resultados

**Ejemplo:**

```json
{
  "tool": "list_sales",
  "arguments": { "state": "sale", "limit": 10 }
}
```

---

### 🔹 `get_sale` 🆕

Obtiene detalles completos de una orden de venta por ID.

**Argumentos:**

* `sale_id`: id de la orden de venta
* `include_lines`: True/False para incluir líneas de la orden

**Ejemplo:**

```json
{
  "tool": "get_sale",
  "arguments": { "sale_id": 123, "include_lines": true }
}
```

---

### 🔹 `find_users`

Busca usuarios de Odoo por nombre.

**Argumentos:**

* `q`: texto parcial
* `active`: True/False/None
* `limit`: límite de resultados

**Ejemplo:**

```json
{
  "tool": "find_users",
  "arguments": { "q": "Rodriguez" }
}
```

---

### 🔹 `search`

Herramienta genérica compatible con ChatGPT Connectors.
Detecta si el query se refiere a **proyectos** o **tareas** y llama internamente a las herramientas correspondientes.

**Ejemplo:**

```json
{
  "tool": "search",
  "arguments": { "query": "tareas del proyecto CRM" }
}
```

---

### 🔹 `fetch`

Devuelve el contenido completo de un documento (`project:<id>` o `task:<id>`).

**Ejemplo:**

```json
{
  "tool": "fetch",
  "arguments": { "doc_id": "task:123" }
}
```

---

### 🛠️ Herramientas de DESARROLLO (Lectura y Escritura) 🆕

Estas herramientas permiten **crear y modificar** órdenes de venta en el ambiente de desarrollo.

### 🔸 `dev_create_sale`

Crea una nueva orden de venta en el ambiente de desarrollo.

**Argumentos:**
* `partner_id` (int, requerido): ID del cliente (res.partner)
* `user_id` (int, opcional): ID del vendedor
* `date_order` (string, opcional): Fecha de la orden
* `payment_term_id` (int, opcional): Términos de pago
* `note` (string, opcional): Notas u observaciones

**Ejemplo:**
```json
{
  "tool": "dev_create_sale",
  "arguments": {
    "partner_id": 23,
    "user_id": 5,
    "note": "[TEST-DEV] Orden de prueba"
  }
}
```

---

### 🔸 `dev_create_sale_line`

Agrega una línea de producto a una orden de venta.

**Argumentos:**
* `order_id` (int, requerido): ID de la orden
* `product_id` (int, requerido): ID del producto
* `product_uom_qty` (float, opcional): Cantidad (default: 1.0)
* `price_unit` (float, opcional): Precio unitario
* `name` (string, opcional): Descripción del producto

**Ejemplo:**
```json
{
  "tool": "dev_create_sale_line",
  "arguments": {
    "order_id": 145,
    "product_id": 12,
    "product_uom_qty": 10.0,
    "price_unit": 500.00
  }
}
```

---

### 🔸 `dev_update_sale`

Actualiza una orden de venta existente en desarrollo.

**Argumentos:**
* `sale_id` (int, requerido): ID de la orden
* `values` (dict, requerido): Campos a actualizar

**Ejemplo:**
```json
{
  "tool": "dev_update_sale",
  "arguments": {
    "sale_id": 145,
    "values": {"note": "Orden actualizada"}
  }
}
```

---

### 🔸 `dev_read_sale`

Lee una orden de venta del ambiente de desarrollo.

**Argumentos:**
* `sale_id` (int, requerido): ID de la orden
* `fields` (list, opcional): Campos a leer

**Ejemplo:**
```json
{
  "tool": "dev_read_sale",
  "arguments": {
    "sale_id": 145,
    "fields": ["name", "partner_id", "amount_total"]
  }
}
```

---

## 🔧 Variables de entorno
      "phone": "+34 912345678"
    }
  }
}
```

---

### 🔸 `dev_update_record`

Actualiza un registro existente en desarrollo.

**Argumentos:**
* `model` (string, requerido): Nombre del modelo
* `record_id` (int, requerido): ID del registro
* `values` (dict, requerido): Campos a actualizar

**Ejemplo:**
```json
{
  "tool": "dev_update_record",
  "arguments": {
    "model": "project.task",
    "record_id": 456,
    "values": {"priority": "1"}
  }
}
```

---

### 🔸 `dev_read_record`

Lee un registro del ambiente de desarrollo.

**Argumentos:**
* `model` (string, requerido): Nombre del modelo
* `record_id` (int, requerido): ID del registro
* `fields` (list, opcional): Campos a leer

**Ejemplo:**
```json
{
  "tool": "dev_read_record",
  "arguments": {
    "model": "project.task",
    "record_id": 456,
    "fields": ["name", "priority", "user_id"]
  }
}
```

---

## 🔧 Variables de entorno

### Ambiente de Producción (Solo Lectura)

| Variable       | Descripción                      |
| -------------- | -------------------------------- |
| `ODOO_URL`     | URL base de Odoo (producción)    |
| `ODOO_DB`      | Nombre de la base de datos       |
| `ODOO_LOGIN`   | Usuario con permisos de lectura  |
| `ODOO_API_KEY` | API Key del usuario              |
| `PORT`         | Puerto del servidor (default: 8000) |

### Ambiente de Desarrollo (Lectura y Escritura) 🆕

| Variable          | Descripción                           | Valor por defecto |
| ----------------- | ------------------------------------- | ----------------- |
| `DEV_ODOO_URL`    | URL de Odoo desarrollo                | https://pegasuscontrol-dev18-25468489.dev.odoo.com |
| `DEV_ODOO_DB`     | Base de datos de desarrollo           | pegasuscontrol-dev18-25468489 |
| `DEV_ODOO_LOGIN`  | Usuario del ambiente de desarrollo    | (requerido)       |
| `DEV_ODOO_API_KEY`| API Key para desarrollo               | (requerido)       |

**Ejemplo de archivo `.env`:**

```bash
# PRODUCCIÓN (Solo lectura)
ODOO_URL=https://pegasuscontrols.odoo.sh
ODOO_DB=pegasuscontrols-9900001
ODOO_LOGIN=usuario@empresa.com
ODOO_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx

# DESARROLLO (Lectura y escritura)
DEV_ODOO_URL=https://pegasuscontrol-dev18-25468489.dev.odoo.com
DEV_ODOO_DB=pegasuscontrol-dev18-25468489
DEV_ODOO_LOGIN=dev_usuario@empresa.com
DEV_ODOO_API_KEY=yyyyyyyyyyyyyyyyyyyyyyyy

# Servidor
PORT=8000
```

---

## 💬 Integración con ChatGPT / Deep Research

En ChatGPT (Connectors o Deep Research):

* URL del servidor:
  `https://<tu-app-runner>.awsapprunner.com`
* Protocolo: `text/event-stream`
* Herramientas esperadas: `search`, `fetch`

Estas herramientas exponen la información de Odoo en el formato MCP estándar.

---

## 🧱 Cómo agregar nuevas herramientas

Cada módulo en `tools/` se carga automáticamente desde `server.py`:

```python
for module_name in ["projects", "tasks", "users"]:
    mod = importlib.import_module(f"tools.{module_name}")
    mod.register(mcp, {"odoo": odoo})
```

Para crear una nueva herramienta:

1. Agrega un archivo nuevo en `tools/` (por ejemplo, `tools/invoices.py`).
2. Implementa una función `register(mcp, deps)` y registra tus métodos.
3. Reinicia el servidor: se cargará automáticamente.

---

## 🧩 Compatibilidad técnica

| Componente     | Versión recomendada                   |
| -------------- | ------------------------------------- |
| Python         | 3.10+                                 |
| Odoo           | 14 – 17                               |
| FastMCP        | Última versión estable                |
| AWS App Runner | Cualquier región soportada            |
| ChatGPT        | Conectores / Deep Research habilitado |

---

## 🧑‍💻 Autor

**Julio Rodríguez**
Pegasus Control — Arquitectura y Automatización IA
📧 [arodriguezpc@corporativosade.com.mx](mailto:arodriguezpc@corporativosade.com.mx)

----------------------

## Ejemplo de uso y despliegue local

# ✅ SERVIDOR MCP-ODOO - LISTO PARA USO CON LLM

## 🎯 ESTADO ACTUAL: SERVIDOR CORRIENDO Y FUNCIONAL

```
✅ Servidor activo en: http://127.0.0.1:8000
✅ Endpoint MCP: http://127.0.0.1:8000/mcp
✅ Health check: http://127.0.0.1:8000/health → {"ok": true}
✅ 6 herramientas registradas y funcionando
```

---

## 🚀 INICIO RÁPIDO

### Para iniciar el servidor:
```bash
cd /home/devsoft/Documentos/mcp-odoo
.venv/bin/uvicorn server:app --port 8000 --host 0.0.0.0 --reload
```

### Para detener el servidor:
```bash
pkill -f "uvicorn server:app"
```

---

## 📋 HERRAMIENTAS DISPONIBLES PARA EL LLM

| # | Tool | Descripción | Parámetros |
|---|------|-------------|------------|
| 1 | `list_projects` | Lista proyectos de Odoo | limit (opcional) |
| 2 | `list_tasks` | Lista tareas con filtros | limit, assigned_to (opcional) |
| 3 | `get_task` | Obtiene detalle de una tarea | task_id (requerido) |
| 4 | `list_users` | Lista usuarios | limit (opcional) |
| 5 | `search` | Busca en proyectos y tareas | query, limit |
| 6 | `fetch` | Obtiene documento completo | doc_id (ej: "project:123") |

---

## 🤖 CONFIGURACIÓN VS CODE (mcp.json)

Tu archivo `.vscode/mcp.json` está configurado:

```json
{
  "servers": {
    "mcp-odoo": {
      "url": "http://127.0.0.1:8000/mcp",
      "type": "http"
    }
  },
  "inputs": []
}
```

---

## 🧪 PRUEBAS RÁPIDAS

### Test 1: Verificar herramientas disponibles
```bash
cd /home/devsoft/Documentos/mcp-odoo
.venv/bin/python test_mcp_client.py
```

### Test 2: Probar endpoint de salud
```bash
curl http://127.0.0.1:8000/health
```

### Test 3: Ver logs en tiempo real
```bash
tail -f /tmp/mcp-odoo.log
```

---

## 💻 EJEMPLO DE USO CON PYTHON

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def consultar_odoo():
    URL = "http://127.0.0.1:8000/mcp"
    
    async with streamablehttp_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Listar proyectos
            result = await session.call_tool("list_projects", {"limit": 5})
            print(result.content[0].text)
            
            # Listar tareas
            result = await session.call_tool("list_tasks", {"limit": 10})
            print(result.content[0].text)
            
            # Buscar
            result = await session.call_tool("search", {
                "query": "almacen",
                "limit": 5
            })
            print(result.content[0].text)

asyncio.run(consultar_odoo())
```

---

## 🔑 VARIABLES DE ENTORNO

El archivo `.env` contiene las credenciales de Odoo:

```bash
ODOO_URL=https://pegasuscontrols.odoo.sh  # ✅ Configurado
ODOO_DB=pegasuscontrols-9900001           # ✅ Configurado
ODOO_LOGIN=victor.lopez@pegasuscontrols.com # ✅ Configurado
ODOO_API_KEY=*****************************  # ✅ Configurado
PORT=8000                                   # ✅ Configurado
```

---

## 📊 MONITOREO Y LOGS

### Ver estado del servidor
```bash
lsof -i :8000
ps aux | grep uvicorn
```

### Ver logs
```bash
tail -f /tmp/mcp-odoo.log
```

### Ver últimas 50 líneas de logs
```bash
tail -50 /tmp/mcp-odoo.log
```

## 🎯 PETICIONES DESDE LLM

Cuando uses un LLM (ChatGPT, Claude, etc.) con este servidor:

1. **URL del servidor**: `http://127.0.0.1:8000/mcp`
2. **Tipo**: HTTP/SSE
3. **Autenticación**: No requerida (ya configurada en .env)

El LLM podrá:
- ✅ Listar proyectos de Odoo
- ✅ Buscar tareas
- ✅ Filtrar por usuario asignado
- ✅ Obtener detalles de tareas específicas
- ✅ Buscar en proyectos y tareas simultáneamente
- ✅ Listar usuarios del sistema

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [x] Servidor corriendo en puerto 8000
- [x] Variables de entorno cargadas (.env)
- [x] FastMCP configurado con streamable_http
- [x] 6 herramientas registradas
- [x] Conexión con Odoo exitosa
- [x] Endpoint /health respondiendo
- [x] Endpoint /mcp activo
- [x] mcp.json configurado
- [x] Tests funcionando

---

## 🎉 ¡LISTO PARA USAR!

Tu servidor MCP-Odoo está completamente configurado y listo para recibir peticiones de LLM.

**Siguiente paso**: Conecta tu LLM favorito usando la URL `http://127.0.0.1:8000/mcp`

---

## 📚 ARCHIVOS DE REFERENCIA

- `server.py` - Servidor principal
- `odoo_client.py` - Cliente de Odoo
- `tools/` - Herramientas modulares
- `test_mcp_client.py` - Test de conexión
- `GUIA_USO_LLM.md` - Guía detallada
- `.env` - Variables de entorno
- `/tmp/mcp-odoo.log` - Logs del servidor

**Última actualización**: 9 de diciembre de 2025

------------------------------------------