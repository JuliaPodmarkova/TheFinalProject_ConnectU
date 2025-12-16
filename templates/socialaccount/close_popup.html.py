<!DOCTYPE html>
<html>
<head>
    <title>Аутентификация...</title>
    <script>
        try {
            // Перезагружаем родительское окно. `true` заставляет перезагрузить с сервера, а не из кэша.
            window.opener.location.reload(true);
        } catch (e) {
            // Если родительское окно было закрыто, может возникнуть ошибка. Игнорируем.
            console.error(e);
        }
        // Закрываем текущее всплывающее окно
        window.close();
    </script>
</head>
<body>
    <p>Вход выполнен. Это окно сейчас закроется...</p>
</body>
</html>