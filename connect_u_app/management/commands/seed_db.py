import random
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
from tqdm import tqdm
from connect_u_app.models import User, UserProfile, Photo, Like, Dislike, Match, Interest

class Command(BaseCommand):
    help = 'Seeds the database with mock data for the ConnectU application'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='The number of users to create', default=100)

    @transaction.atomic
    def handle(self, *args, **options):
        count = options['count']
        fake = Faker('ru_RU')

        self.stdout.write(self.style.WARNING('--- Clearing old data... ---'))
        Match.objects.all().delete()
        Like.objects.all().delete()
        Dislike.objects.all().delete()
        Photo.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Interest.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('--- Creating interests... ---'))
        interests_list = [
            'Путешествия', 'Кино', 'Музыка', 'Спорт', 'Чтение', 'Кулинария',
            'Фотография', 'Игры', 'Программирование', 'Искусство', 'Танцы',
            'Йога', 'Животные', 'Волонтерство', 'Наука'
        ]
        interests = [Interest.objects.create(name=name) for name in interests_list]

        self.stdout.write(self.style.SUCCESS(f'--- Creating {count} users... ---'))
        users_to_create = []
        for _ in tqdm(range(count)):
            user = User(
                email=fake.unique.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password='password123',
                gender=random.choice(['M', 'F']),
                birth_date=fake.date_of_birth(minimum_age=18, maximum_age=65)
            )
            user.set_password(user.password)
            users_to_create.append(user)
        User.objects.bulk_create(users_to_create)

        users = list(User.objects.filter(is_superuser=False).order_by('-date_joined')[:count])

        self.stdout.write(self.style.SUCCESS('--- Creating user profiles... ---'))
        profiles_to_create = []
        for user in tqdm(users):
            profile = UserProfile(
                user=user,
                full_name=f"{user.first_name} {user.last_name}",
                city=fake.city(),
                status=random.choice(['searching', 'in_relationship', 'not_specified']),
            )
            profiles_to_create.append(profile)
        UserProfile.objects.bulk_create(profiles_to_create)

        self.stdout.write(self.style.SUCCESS('--- Assigning interests to profiles... ---'))
        profiles = UserProfile.objects.filter(user__in=users)
        ThroughModel = UserProfile.interests.through
        relations_to_create = []
        for profile in tqdm(profiles):
            profile_interests = random.sample(interests, k=random.randint(1, 5))
            for interest in profile_interests:
                relations_to_create.append(
                    ThroughModel(userprofile_id=profile.id, interest_id=interest.id)
                )
        ThroughModel.objects.bulk_create(relations_to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS('--- Generating likes and dislikes... ---'))
        likes_to_create = []
        dislikes_to_create = []
        all_likes_set = set()

        for user in tqdm(users):
            num_reactions = random.randint(10, 50)
            potential_targets = random.sample([u for u in users if u != user], k=min(num_reactions, len(users) - 1))
            for target_user in potential_targets:
                if random.random() < 0.7:  # 70% chance of liking
                    likes_to_create.append(Like(from_user=user, to_user=target_user))
                    all_likes_set.add((user.id, target_user.id))
                else:
                    dislikes_to_create.append(Dislike(from_user=user, to_user=target_user))

        Like.objects.bulk_create(likes_to_create, ignore_conflicts=True)
        Dislike.objects.bulk_create(dislikes_to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS('--- Creating matches from mutual likes... ---'))
        matches_to_create = []
        processed_pairs = set()
        for from_user_id, to_user_id in tqdm(all_likes_set):
            if (to_user_id, from_user_id) in all_likes_set:
                pair = tuple(sorted((from_user_id, to_user_id)))
                if pair not in processed_pairs:
                    user1_id, user2_id = pair
                    matches_to_create.append(Match(user1_id=user1_id, user2_id=user2_id))
                    processed_pairs.add(pair)
        Match.objects.bulk_create(matches_to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'--- Database has been seeded with {count} users and {len(matches_to_create)} matches! ---'))