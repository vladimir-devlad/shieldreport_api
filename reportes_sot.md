Perfecto. Te explico cómo funcionará la lógica completa:

---

**¿Cómo funciona el filtrado por rol?**

```
Admin/Supervisor          Usuario normal
─────────────────         ─────────────────────────────
GET /reportes             GET /reportes
      ↓                         ↓
SELECT * FROM             SELECT r.* FROM sot_reportes r
sot_reportes              INNER JOIN user_razon_social urs
                            ON r.razon_social_id = urs.razon_social_id
                          WHERE urs.user_id = {id_del_usuario_logueado}
      ↓                         ↓
Ve TODO                   Ve SOLO sus razones sociales asignadas
```

---

**¿Qué endpoints haremos?**

```
GET  /reportes/              → lista reportes (filtrado según rol)
GET  /reportes/{id}          → ver un reporte específico
GET  /reportes/filtros       → filtrar por estado, región, fecha, etc.
```

---

**¿Qué filtros tendrá el listado?**

Dado que `sot_reportes` tiene muchas columnas, los filtros más útiles serían:

```
?estado_sot=PENDIENTE
?region=LIMA
?fecha_programada=2024-01-01
?tipo_trabajo=INSTALACION
?distrito=MIRAFLORES
```

Todos opcionales y combinables entre sí.

---

**Reglas de negocio:**

**Admin** → ve todos los reportes sin restricción, puede filtrar por razon_social también.

**Supervisor** → ve todos los reportes sin restricción, igual que admin pero sin gestionar usuarios.

**Usuario** → solo ve reportes cuyo `razon_social_id` esté en su tabla `user_razon_social`. Si no tiene ninguna razon_social asignada, ve una lista vacía.

---

**¿Qué más necesitamos para que esto funcione?**

Antes de los reportes necesitamos un endpoint para **asignar razones sociales a usuarios**, porque sin eso los usuarios nunca verían nada. Sería algo así:

```
POST /users/{id}/razon-social        → asignar razon social a usuario
DELETE /users/{id}/razon-social/{id} → quitar razon social a usuario
GET  /users/{id}/razon-social        → ver razones sociales de un usuario
```

Y también necesitamos el CRUD de `razon_social`:

```
GET    /razon-social/      → listar todas
POST   /razon-social/      → crear nueva
PUT    /razon-social/{id}  → editar
DELETE /razon-social/{id}  → eliminar
```

---

¿Cómo prefieres avanzar?
