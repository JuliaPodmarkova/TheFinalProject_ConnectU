# Используем официальный легковесный образ Nginx
FROM nginx:1.21-alpine

# Удаляем стандартный конфиг, который идет в комплекте с образом
RUN rm /etc/nginx/conf.d/default.conf

# Копируем наш собственный файл default.conf в нужное место внутри контейнера
COPY default.conf /etc/nginx/conf.d/