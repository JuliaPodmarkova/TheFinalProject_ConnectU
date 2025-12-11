document.addEventListener('DOMContentLoaded', () => {

    const api = {

        getHeaders: () => ({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access')}`
        }),


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


        getProfiles: async (filters = {}) => {
            const cleanFilters = Object.fromEntries(
                Object.entries(filters).filter(([_, v]) => v != null && v !== '')
            );
            const query = new URLSearchParams(cleanFilters).toString();
            const response = await fetch(`/api/v1/profiles/next/?${query}`, { headers: api.getHeaders() });

            if (response.status === 401) {
                logout();
                throw new Error('Unauthorized');
            }
            if (!response.ok) throw new Error('Не удалось загрузить анкеты');
            return response.json();
        },

        sendReaction: async (to_user_id, reaction) => {
            const response = await fetch('/api/v1/reactions/', {
                method: 'POST',
                headers: api.getHeaders(),
                body: JSON.stringify({ to_user_id, reaction })
            });
            if (!response.ok) throw new Error('Не удалось отправить реакцию');
            return response.json();
        },

        getMyProfile: async () => {
            const response = await fetch('/api/v1/profiles/me/', { headers: api.getHeaders() });
            if (!response.ok) throw new Error('Не удалось загрузить профиль');
            return response.json();
        }
    };

    async function renderNav() {
        const navRight = document.getElementById('nav-right');
        if (!navRight) return;

        navRight.innerHTML = '';

        if (localStorage.getItem('access')) {

            try {
                const profile = await api.getMyProfile();
                const userNavTemplate = document.getElementById('user-nav-template');
                const userNode = userNavTemplate.content.cloneNode(true);

                const avatarUrl = profile.main_photo?.image || `https://ui-avatars.com/api/?name=${encodeURIComponent(profile.full_name)}&background=4A96FF&color=fff&font-size=0.5`;
                userNode.querySelector('.user-avatar').src = avatarUrl;

                userNode.getElementById('logout-btn').addEventListener('click', logout);
                userNode.getElementById('search-btn').addEventListener('click', openFilterModal);

                navRight.appendChild(userNode);
            } catch (error) {
                console.error("Ошибка при отрисовке навигации:", error);
                logout();
            }
        } else {
            const guestNavTemplate = document.getElementById('guest-nav-template');
            const guestNode = guestNavTemplate.content.cloneNode(true);
            navRight.appendChild(guestNode);
        }
    }

     function logout(e) {
        if (e) e.preventDefault();
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        window.location.href = '/login/'; // Перенаправляем на страницу входа
    }

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
                window.location.href = '/';
            } catch (error) {
                errorMessage.textContent = error.message;
            }
        });
    }

    function initFeedPage() {
        const cardContainer = document.getElementById('profile-card-container');
        if (!cardContainer) return;

        console.log("Страница ленты инициализирована!");
        // loadProfiles(); // Раскомментируй, когда будет готова функция
    }

    function openFilterModal() {
        const filterModal = document.getElementById('filter-modal');
        if (filterModal) filterModal.classList.add('visible');
    }

    function initFilterModal() {
        const filterModal = document.getElementById('filter-modal');
        const closeModalBtn = document.querySelector('.modal-close-btn');

        if (!filterModal || !closeModalBtn) return;

        closeModalBtn.addEventListener('click', () => filterModal.classList.remove('visible'));
        filterModal.addEventListener('click', (e) => {
            if (e.target === filterModal) filterModal.classList.remove('visible');
        });

    }

    function main() {
        renderNav();
        initLoginPage();
        initFeedPage();
        initFilterModal();
    }

    main();

});