Perfecto, te hago un resumen completo de todo lo que tenemos hasta ahora:

---

**🏗️ Estructura actual del proyecto**

```
soc_api/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── dependencies.py
│   ├── models/
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── session.py
│   │   └── audit_log.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   └── role.py
│   ├── routers/
│   │   ├── auth.py
│   │   └── users.py
│   └── services/
│       ├── auth_service.py
│       └── user_service.py
├── .env
└── requirements.txt
```

---

**📌 Endpoints disponibles actualmente**

```
POST   /auth/login        → login
POST   /auth/logout       → logout

GET    /users/            → listar usuarios   (solo admin)
GET    /users/{id}        → ver usuario       (solo admin)
POST   /users/            → crear usuario     (solo admin)
PUT    /users/{id}        → editar usuario    (solo admin)
DELETE /users/{id}        → desactivar        (solo admin)
```

---

**🔐 Lo que devuelve el LOGIN**

```json
POST /auth/login
{
  "username": "admin",
  "password": "Admin123!"
}
```

Respuesta:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "admin",
  "role": "admin"
}
```

---

**¿Cómo usarlo en el frontend?**

El flujo es este:

```
1. Usuario llena el form de login
2. Frontend hace POST /auth/login con username y password
3. API devuelve el token + datos del usuario
4. Frontend guarda el token (localStorage o memoria)
5. En cada request siguiente envía el token en el header así:

   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6...

6. Si el token expira o es inválido → API responde 401
7. Frontend redirige al login
```

En código (fetch):

```javascript
// LOGIN
const response = await fetch("http://localhost:8000/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ username: "admin", password: "Admin123!" }),
});
const data = await response.json();
// data.access_token → guárdalo

// USAR EL TOKEN EN REQUESTS PROTEGIDOS
const users = await fetch("http://localhost:8000/users/", {
  headers: {
    Authorization: `Bearer ${data.access_token}`,
  },
});
```

En código (axios):

```javascript
// guardar token después del login
axios.defaults.headers.common["Authorization"] = `Bearer ${data.access_token}`;

// luego todos los requests lo envían automáticamente
axios.get("http://localhost:8000/users/");
```

---

**⚠️ Errores posibles que debes manejar en el front**

| Código | Significado                                    |
| ------ | ---------------------------------------------- |
| `401`  | Token inválido o expirado → redirigir al login |
| `403`  | Sin permisos (no es admin)                     |
| `404`  | Recurso no encontrado                          |
| `400`  | Datos incorrectos (ej: username duplicado)     |

---

¿Quedó claro? ¿Seguimos con el CRUD de roles?
