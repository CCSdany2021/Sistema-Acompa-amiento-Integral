# ✅ VALIDACIÓN Y CORRECCIÓN - DESPLEGABLE "QUIÉN ATENDERÁ"

## 🔴 PROBLEMA IDENTIFICADO

**Síntoma:** Al crear un reporte, el desplegable "Quién atenderá" mostraba usuarios pero al guardar parecía hacer "rollback"

**Causa raíz:** Validación insuficiente de los educadores asignados - no se verificaba que:
1. El usuario sea activo (`User.is_active=True`)
2. Tenga un perfil Educador activo (`Educador.is_active=True`)
3. Esté habilitado para crear reportes

---

## ✅ SOLUCIONES IMPLEMENTADAS

### 1. **Validación mejorada en la vista** (estudiantes/views.py:77-142)
```python
# Antes: Asignaba cualquier usuario del formulario sin validar
assigned_to = None
if assigned_to_id:
    assigned_to = get_user_model().objects.filter(pk=assigned_to_id).first()

# Después: Valida que el usuario sea activo y tenga perfil Educador
assigned_to = None
if assigned_to_id:
    try:
        assigned_user = get_user_model().objects.get(pk=assigned_to_id, is_active=True)
        educador = Educador.objects.filter(user=assigned_user, is_active=True).first()
        if educador:
            assigned_to = assigned_user
        else:
            # Si no tiene perfil válido, asigna al usuario actual
            assigned_to = actor_user
    except get_user_model().DoesNotExist:
        assigned_to = actor_user
```

### 2. **Filtrado correcto del desplegable** (estudiantes/views.py:270-295)
```python
# Solo mostrará educadores que cumplan:
# ✅ is_active=True en Educador
# ✅ is_active=True en User
# ✅ Ordenados alfabéticamente
educadores = Educador.objects.filter(is_active=True).select_related('user')
for ed in educadores:
    if ed.user.is_active:  # Validación adicional
        educadores_json.append({...})
```

### 3. **Mensajes de error claros**
Si algo falla, el usuario ve el motivo exacto:
- "El usuario seleccionado no tiene un perfil de Educador activo"
- "El usuario seleccionado no existe o no está activo"

---

## 🔍 CÓMO VERIFICAR QUE TODO ESTÁ BIEN

### Opción 1: Ejecutar el script de validación
```bash
cd Sistema_acompanamiento_integral_nuevo
python scripts/validate_educadores.py
```

**Qué verifica:**
✅ Todos los educadores están activos  
✅ Sus usuarios están activos  
✅ Pueden crear reportes  
✅ Aparecerán en el desplegable  
✅ Tienen fines educativos configurados

### Opción 2: Verificar manualmente en /admin/

1. **Ir a**: http://sai.portalcalasanzsuba.com/admin/acompanamiento/educador/
2. **Para CADA educador, verificar:**
   - ☑️ Checkbox **`is_active`** = ACTIVADO
   - ☑️ Usuario relacionado tiene `is_active=True` en /admin/auth/user/
   - ☑️ Campo **`fines_educativos`** tiene valores (ej: `["ACADEMICO", "CONVIVENCIA"]`)

3. **Ejemplo de configuración CORRECTA:**
   ```
   Usuario: Mireya Rodriguez (mrodriguez@calasanzsuba.edu.co)
   is_active: ✅ ACTIVADO
   rol: ADMIN_GLOBAL
   acceso_global: ✅ ACTIVADO
   fines_educativos: ["ACADEMICO", "CONVIVENCIA", "ESPIRITUAL", "PSICOAFECTIVO"]
   ```

---

## ⚙️ CONFIGURACIÓN OBLIGATORIA POR USUARIO

Para que un educador aparezca en el desplegable "Quién atenderá", debe cumplir:

| Campo | Dónde | Valor requerido |
|-------|-------|-----------------|
| `User.is_active` | /admin/auth/user/ | ✅ ACTIVADO |
| `Educador.is_active` | /admin/acompanamiento/educador/ | ✅ ACTIVADO |
| `Educador.fines_educativos` | /admin/acompanamiento/educador/ | Al menos uno (ej: `["ACADEMICO"]`) |
| Perfil Educador existe | | ✅ DEBE EXISTIR |

---

## 🔐 PERMISOS DE LECTURA/ESCRITURA

### ✅ Cualquier educador ACTIVO puede:
1. ✅ Crear reportes (ser asignado en "Quién atenderá")
2. ✅ Ver reportes asignados a ellos
3. ✅ Crear observaciones en reportes que atienden
4. ✅ Crear recomendaciones en reportes que atienden

### 🔒 SOLO CAP, mrodriguez, dhiguera, pvasquez pueden:
1. 🔒 Ver/editar/cerrar reportes de TODA la institución
2. 🔒 Editar/eliminar observaciones de otros educadores
3. 🔒 Reaabrir casos cerrados
4. 🔒 Ver indicadores globales

---

## 📋 LISTA DE VERIFICACIÓN ANTES DE USAR EN PRODUCCIÓN

- [ ] Ejecuté `python scripts/validate_educadores.py` sin errores
- [ ] En /admin/, todos los educadores tienen `is_active=✅`
- [ ] Todos los usuarios relacionados tienen `is_active=✅` en /admin/auth/user/
- [ ] Al menos 2 educadores tienen fines educativos configurados
- [ ] El desplegable "Quién atenderá" muestra al menos 2 opciones
- [ ] Al crear un reporte, puedo guardar sin rollback
- [ ] Las observaciones y recomendaciones se guardan correctamente
- [ ] Los mensajes de error son claros si algo falla

---

## 🚨 TROUBLESHOOTING

### Problema: El desplegable está vacío
**Solución:**
1. Ve a /admin/acompanamiento/educador/
2. Verifica que al menos UN educador tenga `is_active=✅`
3. Verifica que su User relacionado tenga `is_active=✅` en /admin/auth/user/
4. Ejecuta: `python scripts/validate_educadores.py`

### Problema: Se ve el usuario pero al guardar falla
**Solución:**
1. Ejecuta: `python scripts/validate_educadores.py`
2. Busca problemas reportados
3. Revisa que el usuario tenga fines educativos configurados

### Problema: Solo ves 2 usuarios (cap@calasanzsuba.edu.co y mireya@...)
**Solución:**
1. Ve a /admin/acompanamiento/educador/
2. Para CADA educador que no ves en el desplegable:
   - Marca `is_active=✅`
   - Verifica que su User tenga `is_active=✅`
   - Agrega fines educativos si están vacíos
3. Recarga la página del reporte

---

## 📊 ESTADÍSTICAS ESPERADAS

Si todo está bien configurado, deberías ver:
```
✅ Educadores ACTIVOS: 5+
❌ Educadores INACTIVOS: 0 (o los que intentas desactivar)
Educadores en desplegable: 5+ (solo los ACTIVOS)
```

---

## ✉️ NOTIFICACIONES POR CORREO

Cuando creas un reporte con un educador asignado:
1. ✅ Se envía email al educador asignado
2. ✅ Le notifica que tiene un nuevo caso
3. ✅ Le da el enlace directo al reporte

**Nota:** Los emails se envían si:
- El servidor de correo está configurado
- El usuario tiene email válido
- El reporte se guardó exitosamente

---

## 📞 SOPORTE

Si después de estas validaciones sigue fallando:
1. Revisa el archivo de logs Django
2. Ejecuta `python scripts/validate_educadores.py` completo
3. Verifica manualmente en /admin/ cada educador
4. Contacta al equipo de desarrollo

---

**Última actualización:** 2026-07-10
**Versión del SAI:** 1.0.0
