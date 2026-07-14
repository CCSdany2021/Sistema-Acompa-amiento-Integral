SELECT
  au.first_name || ' ' || au.last_name as nombre,
  au.email,
  ea.is_active,
  ea.fines_educativos
FROM acompanamiento_educador ea
JOIN auth_user au ON ea.user_id = au.id
ORDER BY au.first_name;
