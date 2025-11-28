// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {

    // --- ОБЪЕКТ ДЛЯ РАБОТЫ С API ---
    // Соберем все наши запросы к бэкенду в одном месте.
    const api = {
        /**
         * Получает заголовки для авторизованного запроса.
         */
        getHeaders: () => ({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access')}`
        }),

        /**
         * Запрос на вход в систему.
         * @param {string} email - Email пользователя.
         * @param {string} password - Пароль пользователя.
         */
        login: async (email, password) => {
            const response = await fetch('/api/v1/auth/jwt/create/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (!response.ok) {
                throw new Error('Неверный email или пароль.');
            }
            return response.json();
        },

        /**
         * Загружает профили для ленты с учетом фильтров.
         * @param {object} filters - Объект с фильтрами.
         */
        getProfiles: async (filters = {}) => {
            // Удаляем пустые значения из фильтров
            const cleanFilters = Object.fromEntries(
                Object.entries(filters).filter(([_, v]) => v != null && v !== '')
            );
            const query = new URLSearchParams(cleanFilters).toString();
            // Обрати внимание: URL теперь /profiles/next/
            const response = await fetch(`/api/v1/profiles/next/?${query}`, { headers: api.getHeaders() });

            if (response.status === 401) {
                // Если токен протух, перенаправляем на логин
                logout();
                throw new Error('Unauthorized');
            }
            if (!response.ok) throw new Error('Не удалось загрузить анкеты');
            return response.json();
        },

        /**
         * Отправляет реакцию (лайк/дизлайк) на профиль.
         * @param {number} to_user_id - ID пользователя, которому ставим реакцию.
         * @param {string} reaction - 'like' или 'dislike'.
         */
        sendReaction: async (to_user_id, reaction) => {
            const response = await fetch('/api/v1/reactions/', {
                method: 'POST',
                headers: api.getHeaders(),
                body: JSON.stringify({ to_user_id, reaction })
            });
            if (!response.ok) throw new Error('Не удалось отправить реакцию');
            return response.json();
        },

        /**
         * Загружает данные своего профиля.
         */
        getMyProfile: async () => {
            // Обрати внимание: URL теперь /profiles/me/
            const response = await fetch('/api/v1/profiles/me/', { headers: api.getHeaders() });
            if (!response.ok) throw new Error('Не удалось загрузить профиль');
            return response.json();
        }
    };

    // --- УПРАВЛЕНИЕ UI И СОСТОЯНИЕМ АВТОРИЗАЦИИ ---

    /**
     * Главная функция для отрисовки шапки (nav-бара).
     * Она решает, что показать: кнопки для гостя или меню для пользователя.
     */
    async function renderNav() {
        const navRight = document.getElementById('nav-right');
        if (!navRight) return; // Если на странице нет шапки, ничего не делаем

        navRight.innerHTML = ''; // Очищаем контейнер

        if (localStorage.getItem('access')) {
            // Пользователь авторизован
            try {
                const profile = await api.getMyProfile();
                const userNavTemplate = document.getElementById('user-nav-template');
                const userNode = userNavTemplate.content.cloneNode(true);

                // Устанавливаем аватар (или заглушку, если фото нет)
                const avatarUrl = profile.main_photo?.image || `https://ui-avatars.com/api/?name=${encodeURIComponent(profile.full_name)}&background=4A96FF&color=fff&font-size=0.5`;
                userNode.querySelector('.user-avatar').src = avatarUrl;

                // Навешиваем обработчики событий на кнопки ВНУТРИ шаблона
                userNode.getElementById('logout-btn').addEventListener('click', logout);
                userNode.getElementById('search-btn').addEventListener('click', openFilterModal);

                navRight.appendChild(userNode);
            } catch (error) {
                console.error("Ошибка при отрисовке навигации:", error);
                logout(); // Если не удалось загрузить профиль, разлогиниваем
            }
        } else {
            // Пользователь - гость
            const guestNavTemplate = document.getElementById('guest-nav-template');
            const guestNode = guestNavTemplate.content.cloneNode(true);
            navRight.appendChild(guestNode);
        }
    }

    /**
     * Функция выхода из системы.
     */
    function logout(e) {
        if (e) e.preventDefault();
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        window.location.href = '/login/'; // Перенаправляем на страницу входа
    }

    // --- ЛОГИКА ДЛЯ КОНКРЕТНЫХ СТРАНИЦ ---

    /**
     * Инициализация страницы входа (/login/).
     */
    function initLoginPage() {
        const loginForm = document.getElementById('login-form');
        const errorMessage = document.getElementById('error-message');
        if (!loginForm) return;

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorMessage.textContent = '';
            const email = loginForm.elements.email.value;
            const password = loginForm.elements.password.value;

            try {
                const data = await api.login(email, password);
                localStorage.setItem('access', data.access);
                localStorage.setItem('refresh', data.refresh);
                window.location.href = '/'; // Перенаправляем на главную после успеха
            } catch (error) {
                errorMessage.textContent = error.message;
            }
        });
    }

    /**
     * Инициализация страницы с лентой (/).
     */
    function initFeedPage() {
        const cardContainer = document.getElementById('profile-card-container');
        if (!cardContainer) return; // Если мы не на странице ленты, выходим

        // Код для ленты, который у тебя уже был, можно разместить здесь.
        // Например, вызов loadProfiles().
        console.log("Страница ленты инициализирована!");
        // loadProfiles(); // Раскомментируй, когда будет готова функция
    }

    /**
     * Открывает модальное окно с фильтрами.
     */
    function openFilterModal() {
        const filterModal = document.getElementById('filter-modal');
        if (filterModal) filterModal.classList.add('visible');
    }

    /**
     * Инициализация модального окна фильтров (должно быть на странице ленты).
     */
    function initFilterModal() {
        const filterModal = document.getElementById('filter-modal');
        const closeModalBtn = document.querySelector('.modal-close-btn');
        // const filterForm = document.getElementById('filter-form');

        if (!filterModal || !closeModalBtn) return;

        closeModalBtn.addEventListener('click', () => filterModal.classList.remove('visible'));
        filterModal.addEventListener('click', (e) => {
            if (e.target === filterModal) filterModal.classList.remove('visible');
        });

        // Сюда добавишь логику отправки формы фильтров
    }

    // --- ГЛАВНАЯ ФУНКЦИЯ ИНИЦИАЛИЗАЦИИ ---
    // Эта функция запускается один раз при загрузке любой страницы.
    function main() {
        renderNav(); // Первым делом отрисовываем шапку

        // Затем запускаем логику для конкретной страницы, на которой находимся
        initLoginPage();
        initFeedPage();
        initFilterModal();
    }

    // Запускаем всё!
    main();

});