# /app/connect_u_app/management/commands/seed_db.py

import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.hashers import make_password
from faker import Faker
from tqdm import tqdm  # Импортируем для красивого progress bar

# Убедись, что все нужные модели импортированы
from ...models import User, UserProfile, Photo, Interaction, Match, Interest


class Command(BaseCommand):
    help = 'Seeds the database with mock data for the ConnectU application'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='The number of users to create', default=100)

    @transaction.atomic  # Оборачиваем всё в одну транзакцию для скорости и безопасности
    def handle(self, *args, **options):
        count = options['count']
        fake = Faker('ru_RU')

        self.stdout.write(self.style.WARNING('Clearing old data...'))
        # Очищаем модели в правильном порядке, чтобы не нарушать связи
        Match.objects.all().delete()
        Interaction.objects.all().delete()
        Photo.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Interest.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Creating interests...'))
        interests_list = [
            'Путешествия', 'Кино', 'Музыка', 'Спорт', 'Чтение', 'Кулинария',
            'Фотография', 'Игры', 'Программирование', 'Искусство', 'Танцы',
            'Йога', 'Животные', 'Волонтерство', 'Наука'
        ]
        interests = [Interest.objects.create(name=name) for name in interests_list]

        self.stdout.write(self.style.SUCCESS(f'Creating {count} users...'))

        # --- ВОТ КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ ---
        users_to_create = []
        for i in tqdm(range(count)):
            # Генерируем базовое имя и email
            first_name = fake.first_name()
            last_name = fake.last_name()
            base_username = f"{fake.user_name()}_{i}"  # Добавляем уникальный суффикс
            base_email = f"{base_username}@example.com"  # Гарантируем уникальность email

            user = User(
                username=base_username,
                email=base_email,
                first_name=first_name,
                last_name=last_name,
                password=make_password('password123'),  # Устанавливаем пароль сразу
                gender=random.choice(['M', 'F']),
                birth_date=fake.date_of_birth(minimum_age=18, maximum_age=65)
            )
            users_to_create.append(user)

        # Создаем пользователей одним большим запросом (гораздо быстрее!)
        User.objects.bulk_create(users_to_create)

        # Получаем всех созданных пользователей для дальнейшей работы
        users = list(User.objects.filter(is_superuser=False).order_by('-date_joined')[:count])

        self.stdout.write(self.style.SUCCESS('Creating user profiles...'))
        profiles_to_create = []
        for user in tqdm(users):
            profile = UserProfile(
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                city=fake.city(),
                status=random.choice(['searching', 'in_relationship', 'not_specified']),
                # hobbies можно пропустить, если используем ManyToMany для Interest
            )
            profiles_to_create.append(profile)

        # Создаем профили одним запросом
        profiles = UserProfile.objects.bulk_create(profiles_to_create)

        self.stdout.write(self.style.SUCCESS('Assigning interests to profiles...'))
        # bulk_create не возвращает ID, поэтому получаем профили заново
        profiles = UserProfile.objects.filter(user__in=users)
        ThroughModel = UserProfile.interests.through
        relations_to_create = []
        for profile in tqdm(profiles):
            # Назначаем от 1 до 5 случайных интересов
            profile_interests = random.sample(interests, k=random.randint(1, 5))
            for interest in profile_interests:
                relations_to_create.append(
                    ThroughModel(userprofile_id=profile.id, interest_id=interest.id)
                )

        # Создаем связи ManyToMany одним запросом
        ThroughModel.objects.bulk_create(relations_to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS('Generating interactions (likes/dislikes)...'))
        interactions_to_create = []
        for user in tqdm(users):
            # Каждый пользователь оценивает от 10 до 50 других пользователей
            num_reactions = random.randint(10, 50)
            potential_targets = random.sample([u for u in users if u != user], k=num_reactions)
            for target_user in potential_targets:
                interaction = Interaction(
                    from_user=user,
                    to_user=target_user,
                    reaction=random.choice(['like', 'like', 'dislike'])  # Делаем лайки более частыми
                )
                interactions_to_create.append(interaction)

        Interaction.objects.bulk_create(interactions_to_create,
                                        ignore_conflicts=True)  # Игнорируем, если реакция уже есть

        self.stdout.write(self.style.SUCCESS(f'Database has been seeded successfully with {count} users!'))
