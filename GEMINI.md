# Project Overview

This project is a multi-tenant backend system built with Django and Django REST Framework. It provides a comprehensive user management system with role-based access control (RBAC), multi-tenancy support, and a variety of features including a CMS, customer management, and order processing. The system is designed to be extensible, with a modular architecture that allows for the easy addition of new applications.

**Key Technologies:**

*   **Backend:** Django, Django REST Framework
*   **Database:** MySQL (using `pymysql`)
*   **Authentication:** JWT (JSON Web Tokens)
*   **API Documentation:** `drf-spectacular` for OpenAPI 3.0 schema generation, with Swagger UI and ReDoc.
*   **Environment Variables:** `python-dotenv` for managing configuration.
*   **CORS:** `django-cors-headers` for handling Cross-Origin Resource Sharing.

**Architecture:**

The project follows a standard Django architecture, with a `core` project directory and multiple applications, each representing a specific feature or domain. The key architectural features include:

*   **Multi-tenancy:** The system is designed to support multiple tenants, with data isolation between them. The `TenantMiddleware` is responsible for identifying the current tenant based on the request.
*   **Role-Based Access Control (RBAC):** The `rbac` application provides a flexible permission system that allows for fine-grained control over user access to resources.
*   **Modular Applications:** The project is divided into several applications, including:
    *   `users`: Manages user authentication, registration, and profiles.
    *   `tenants`: Manages tenant information.
    *   `rbac`: Implements the RBAC system.
    *   `cms`: A Content Management System.
    *   `customers`: Manages customer data.
    *   `orders`: Handles order processing.
    *   `charts`: Provides data for charts and dashboards.
*   **API Versioning:** The API is versioned, with the current version being `v1`.
*   **Custom Middleware:** The project uses several custom middleware for handling API authentication, tenant identification, logging, and response formatting.

# Building and Running

**1. Prerequisites:**

*   Python 3.x
*   MySQL
*   A virtual environment (recommended)

**2. Installation:**

```bash
# Clone the repository
git clone <repository-url>
cd lipeaks_backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# The requirements.txt file appears to be binary or corrupted.
# You will need to manually inspect the project's dependencies
# and install them using pip. Based on the settings.py file,
# the following dependencies are required:
pip install django djangorestframework pymysql python-dotenv djangorestframework-simplejwt drf-spectacular drf-spectacular-sidecar django-cors-headers

# It is likely that there are other dependencies.
# You may need to consult the project's documentation or
# developers to get a complete list.
```

**3. Configuration:**

*   Create a `.env` file in the project root, based on the `.env.example` file.
*   Update the `.env` file with your database credentials, secret key, and other settings.

**4. Database Setup:**

```bash
# Run the database migrations
python manage.py migrate
```

**5. Running the Development Server:**

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000`.

**6. Running Tests:**

```bash
# TODO: Add instructions for running tests.
# The testing framework and commands are not immediately apparent
# from the file analysis.
```

# Development Conventions

*   **Coding Style:** The project appears to follow the standard Python PEP 8 style guide.
*   **API Design:** The API is designed to be RESTful, with a clear and consistent URL structure.
*   **Authentication:** All API endpoints require JWT authentication, unless explicitly excluded. The `Authorization` header should be used to pass the JWT token.
*   **Multi-tenancy:** For endpoints that require tenant authentication, a custom header (e.g., `X-Tenant-ID`) is likely used to specify the tenant.
*   **API Documentation:** The API is documented using `drf-spectacular`. The documentation is available at the following endpoints:
    *   **Swagger UI:** `/api/v1/docs/`
    *   **ReDoc:** `/api/v1/redoc/`
    *   **OpenAPI Schema:** `/api/v1/schema/`


# AI助手核心规则

## 三阶段工作流

### 阶段一：分析问题

**声明格式**：`【分析问题】`

**目的**
因为可能存在多个可选方案，要做出正确的决策，需要足够的依据。

**必须做的事**：
- 理解我的意图，如果有歧义请问我
- 搜索所有相关代码
- 识别问题根因

**主动发现问题**
- 发现重复代码
- 识别不合理的命名
- 发现多余的代码、类
- 发现可能过时的设计
- 发现过于复杂的设计、调用
- 发现不一致的类型定义
- 进一步搜索代码，看是否更大范围内有类似问题

做完以上事项，就可以向我提问了。

**绝对禁止**：
- ❌ 修改任何代码
- ❌ 急于给出解决方案
- ❌ 跳过搜索和理解步骤
- ❌ 不分析就推荐方案
- ❌ 命令里面使用&&符号，因为这是windows的命令，而不是linux的命令

**阶段转换规则**
本阶段你要向我提问。
如果存在多个你无法抉择的方案，要问我，作为提问的一部分。
如果没有需要问我的，则直接进入下一阶段。

### 阶段二：制定方案
**声明格式**：`【制定方案】`

**前置条件**：
- 我明确回答了关键技术决策。

**必须做的事**：
- 列出变更（新增、修改、删除）的文件，简要描述每个文件的变化
- 消除重复逻辑：如果发现重复代码，必须通过复用或抽象来消除
- 确保修改后的代码符合DRY原则和良好的架构设计

如果新发现了向我收集的关键决策，在这个阶段你还可以继续问我，直到没有不明确的问题之后，本阶段结束。
本阶段不允许自动切换到下一阶段。

在做任何任务之前，先创建任务清单(To-Dos)，哪怕只有一个也需要创建；执行任务清单时，中途不要停止，直到所有任务执行完成。

### 阶段三：执行方案
**声明格式**：`【执行方案】`

**必须做的事**：
- 严格按照选定方案实现
- 修改后运行类型检查

**绝对禁止**：
- ❌ 提交代码（除非用户明确要求）
- 启动开发服务器

如果在这个阶段发现了拿不准的问题，请向我提问。

收到用户消息时，一般从【分析问题】阶段开始，除非用户明确指定阶段的名字。

