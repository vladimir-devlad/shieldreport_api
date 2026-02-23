Entendido, ahora el modelo de negocio está más claro. Reformulemos:

---

**Reglas de negocio corregidas:**

```
ADMIN:
  - Crea usuarios con cualquier rol
  - Asigna cualquier razon_social a cualquier usuario
  - Asigna supervisores a usuarios
  - Ve todo sin restricciones

SUPERVISOR:
  - NO crea usuarios
  - Busca usuarios sin supervisor para agregarlos a su grupo
  - Solo puede asignar a esos usuarios sus propias razon_social
  - Ve solo su grupo de usuarios

USUARIO:
  - Solo ve su propia info y sus razon_social
```

---

**Endpoints reformulados:**

**AUTH**
| Endpoint | Admin | Supervisor | Usuario |
|----------|-------|------------|---------|
| POST /auth/login | ✅ | ✅ | ✅ |
| POST /auth/logout | ✅ | ✅ | ✅ |

**USERS**
| Endpoint | Admin | Supervisor | Usuario | Descripción |
|----------|-------|------------|---------|-------------|
| GET /users/ | ✅ todos | ✅ solo su grupo | ❌ | Lista usuarios |
| GET /users/me | ✅ | ✅ | ✅ | Mi perfil |
| GET /users/{id} | ✅ | ✅ solo su grupo | ❌ | Detalle usuario |
| GET /users/sin-supervisor | ✅ | ✅ | ❌ | Usuarios sin supervisor para que el supervisor los jale |
| POST /users/ | ✅ | ❌ | ❌ | Solo admin crea |
| PUT /users/{id} | ✅ | ❌ | ❌ | Solo admin edita |
| PUT /users/me/password | ✅ | ✅ | ✅ | Cambiar contraseña |
| DELETE /users/{id} | ✅ | ❌ | ❌ | Solo admin desactiva |

**ROLES**
| Endpoint | Admin | Supervisor | Usuario |
|----------|-------|------------|---------|
| GET /roles/ | ✅ | ❌ | ❌ |
| GET /roles/{id} | ✅ | ❌ | ❌ |
| POST /roles/ | ✅ | ❌ | ❌ |
| PUT /roles/{id} | ✅ | ❌ | ❌ |
| DELETE /roles/{id} | ✅ | ❌ | ❌ |

**RAZON SOCIAL**
| Endpoint | Admin | Supervisor | Usuario | Descripción |
|----------|-------|------------|---------|-------------|
| GET /razon-social/ | ✅ todas | ✅ solo las suyas | ✅ solo las suyas | Listar |
| GET /razon-social/user/{id} | ✅ | ✅ solo su grupo | ❌ | RS de un usuario |
| POST /razon-social/ | ✅ | ❌ | ❌ | Crear |
| PUT /razon-social/{id} | ✅ | ❌ | ❌ | Editar |
| DELETE /razon-social/{id} | ✅ | ❌ | ❌ | Eliminar |
| POST /razon-social/assign | ✅ a cualquiera | ✅ solo a su grupo con sus RS | ❌ | Asignar |
| DELETE /razon-social/assign/{user_id}/{rs_id} | ✅ | ✅ solo su grupo | ❌ | Quitar |

**SUPERVISOR — gestión de su grupo**
| Endpoint | Admin | Supervisor | Usuario | Descripción |
|----------|-------|------------|---------|-------------|
| GET /supervisor/usuarios-disponibles | ✅ | ✅ | ❌ | Usuarios sin supervisor |
| POST /supervisor/agregar-usuario | ✅ | ✅ | ❌ | Jalar usuario a su grupo |
| DELETE /supervisor/remover-usuario/{user_id} | ✅ | ✅ solo su grupo | ❌ | Sacar usuario del grupo |

---

**Lo que cambia respecto a antes:**

`POST /users/` — solo admin, supervisor ya no crea usuarios, los jala de los disponibles.

`GET /users/sin-supervisor` — nuevo, lista usuarios con rol `usuario` que no tienen supervisor asignado.

`POST /supervisor/agregar-usuario` — nuevo, el supervisor selecciona un usuario disponible y lo agrega a su grupo.

`DELETE /supervisor/remover-usuario/{id}` — nuevo, el supervisor puede soltar un usuario de su grupo.

**Flujo de pruebas completo en Swagger:**

```
Como admin:
1. POST /razon-social/          → crear Empresa A, B, C
2. POST /users/                 → crear supervisor sin supervisor_id
3. POST /users/                 → crear usuario sin supervisor_id
4. GET  /users/sin-supervisor   → debe aparecer el usuario recién creado
5. POST /supervisor/agregar-usuario → asignar usuario al supervisor
6. POST /razon-social/assign    → asignar Empresa A y B al supervisor
7. POST /razon-social/assign    → asignar Empresa A al usuario
8. GET  /users/                 → ver todo completo

Como supervisor:
9.  GET  /users/sin-supervisor      → ve usuarios disponibles
10. POST /supervisor/agregar-usuario → jala un usuario a su grupo
11. POST /razon-social/assign        → asigna sus razones sociales al usuario
12. POST /razon-social/assign        → intenta asignar Empresa C → 403
13. POST /supervisor/agregar-usuario → intenta agregar a otro supervisor → 403

Como usuario:
14. GET /users/me              → ve su propio perfil
15. GET /razon-social/         → ve solo sus razones sociales
16. PUT /users/me/password     → cambia su contraseña
17. GET /users/                → debe dar 403
```
