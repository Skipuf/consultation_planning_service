from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from rest_framework.reverse import reverse

from consultations.models import Consultation, Booked
from .models import User
from specialist.models import Specialist


class BaseUserTestCase(TestCase):
    def setUp(self):
        self.user_data = {
            'email': 'testuser@gmail.com',
            'username': 'test_user',
            'password': '123'
        }
        self.create_group_with_permissions('specialist', ['change_consultation', 'delete_consultation'])

    def create_group_with_permissions(self, name, permissions):
        group, _ = Group.objects.get_or_create(name=name)
        group.permissions.add(*Permission.objects.filter(codename__in=permissions))
        return group

    def register_user(self, email=None, password=None, username=None, is_superuser=False, is_staff=False,
                      is_verified=True):
        user_data = {
            'email': email or self.user_data['email'],
            'password': password or self.user_data['password'],
            'username': username or self.user_data['username']
        }
        self.client.post(reverse('signup'), data=user_data)
        user = User.objects.get(email=user_data['email'])
        user.is_verified = is_verified
        user.is_superuser = is_superuser
        user.is_staff = is_staff
        user.save()
        return user

    def register_specialist(self, email='testspecialist@gmail.com', username='test_specialist'):
        user = self.register_user(email=email, password='123', username=username)
        Specialist.objects.create(user=user, description="За 10 лет работы я стал настоящим профессионалом!")
        return user

    def get_jwt(self, user):
        response = self.client.post(reverse('login'), data={'email': user.email, 'password': '123'})
        return f"Bearer {response.data['data']['access']}"

    def assertResponse(self, response, status_code, status_message):
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.data.get("status"), status_message)


class ProfileTestCase(BaseUserTestCase):
    def create_consultation(self, specialist):
        data_consultation = [
            {'datetime': '2025-10-09 16:00'},
            {'datetime': '2025-10-12 16:00'},
            {'datetime': '2025-10-11 16:00'},
        ]
        for data in data_consultation:
            response = self.client.post('/consultation/', data=data, HTTP_AUTHORIZATION=self.get_jwt(specialist))
            self.assertResponse(response, 201, 'success')

    def test_profile_view(self):
        users = [self.register_user(),
                 self.register_user(email='testuser2@gmail.com', username='test_user2', password='123')]
        for user in users:
            response = self.client.get('/accounts/profile/', HTTP_AUTHORIZATION=self.get_jwt(user))
            self.assertResponse(response, 200, 'success')
            self.assertEqual(response.data['data']['email'], user.email)
            self.assertEqual(response.data['data']['username'], user.username)
            self.assertFalse(response.data['data']['specialist'])

    def test_profile_invalid(self):
        self.assertResponse(self.client.get('/accounts/profile/'), 401, 'error')
        self.assertResponse(self.client.get('/accounts/profile/', HTTP_AUTHORIZATION="Bearer 123"), 401, 'error')

    def test_consultations_and_bookeds(self):
        specialist = self.register_specialist()
        user = self.register_user()

        self.create_consultation(specialist)

        response = self.client.get(reverse('consultations'), HTTP_AUTHORIZATION=self.get_jwt(specialist))
        self.assertResponse(response, 200, 'success')
        for consultation, id in zip(response.data['data']['results'], [1, 3, 2]):
            self.assertEqual(consultation['id'], id)

        for consultation in Consultation.objects.all():
            response = self.client.post('/booked/',
                                        data={'consultation': consultation.id, "description": "test description"},
                                        HTTP_AUTHORIZATION=self.get_jwt(user))
            self.assertResponse(response, 201, 'success')

        response = self.client.get(reverse('bookeds'), HTTP_AUTHORIZATION=self.get_jwt(user))
        self.assertResponse(response, 200, 'success')
        for consultation, id in zip(response.data['data']['results'], [1, 3, 2]):
            self.assertEqual(consultation['consultation']['id'], id)

    def test_consultations_invalid(self):
        user = self.register_user()
        self.assertResponse(self.client.get(reverse('consultations'), HTTP_AUTHORIZATION=self.get_jwt(user)), 403,
                            'error')

    def test_profile_block_and_unblock(self):
        user = self.register_user()
        jwt_user = self.get_jwt(user)
        specialist = self.register_specialist()
        jwt_specialist = self.get_jwt(specialist)
        admin = self.register_user('admin@gmail.com', '123', 'admin', is_superuser=True, is_staff=True)
        jwt_admin = self.get_jwt(admin)

        for data_consultation in ["2025-10-08 16:00", "2025-10-12 16:00", "2025-10-11 16:00"]:
            response = self.client.post('/consultation/',
                                        data={'datetime': data_consultation},
                                        HTTP_AUTHORIZATION=jwt_specialist)
            self.client.post('/booked/',
                             data={'consultation': response.data['data']['id'],
                                   "description": "test description"},
                             HTTP_AUTHORIZATION=jwt_user)

        response = self.client.post('/accounts/profile/block/',
                                    data={'id': specialist.id},
                                    HTTP_AUTHORIZATION=jwt_admin)
        self.assertResponse(response, 200, 'success')
        specialist = User.objects.get(pk=specialist.id)
        self.assertFalse(specialist.is_active)

        for consultation in Consultation.objects.filter(user=specialist.id):
            self.assertTrue(consultation.archive)
            for booked in Booked.objects.filter(consultation=consultation.id):
                self.assertTrue(booked.archive)

        response = self.client.post('/accounts/profile/unblock/',
                                    data={'id': specialist.id},
                                    HTTP_AUTHORIZATION=jwt_admin)
        self.assertResponse(response, 200, 'success')
        specialist = User.objects.get(pk=user.id)
        self.assertTrue(specialist.is_active)

    def test_profile_invalid_block_and_unblock(self):
        user = self.register_user()
        jwt_user = self.get_jwt(user)
        specialist = self.register_specialist()
        jwt_specialist = self.get_jwt(specialist)

        for jwt in [jwt_user, jwt_specialist]:
            response = self.client.post('/accounts/profile/block/',
                                        data={'id': specialist.id},
                                        HTTP_AUTHORIZATION=jwt)
            self.assertResponse(response, 403, 'error')
            response = self.client.post('/accounts/profile/unblock/',
                                        data={'id': specialist.id},
                                        HTTP_AUTHORIZATION=jwt)
            self.assertResponse(response, 403, 'error')


class UserRegistrationTestCase(BaseUserTestCase):
    def test_register_user(self):
        response = self.client.post(reverse('signup'), data=self.user_data)
        self.assertResponse(response, 201, "success")
        self.assertEqual(response.data['data']['username'], self.user_data['username'])
        self.assertEqual(response.data['data']['email'], self.user_data['email'])

        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.username, self.user_data['username'])

    def test_register_user_with_invalid_data(self):
        invalid_cases = [
            ('email', 'invalid_email'),
            ('password', None),
            ('username', None),
        ]
        for field, value in invalid_cases:
            invalid_data = self.user_data.copy()
            if value is None:
                del invalid_data[field]
            else:
                invalid_data[field] = value
            self.assertResponse(self.client.post(reverse('signup'), data=invalid_data), 400, "error")

    def test_register_user_with_busy_email(self):
        self.register_user()
        self.assertResponse(self.client.post(reverse('signup'), data=self.user_data), 400, "error")


class UserConfirmEmailTestCase(BaseUserTestCase):
    def setUp(self):
        super().setUp()
        self.user_data2 = {
            'email': 'testuser2@gmail.com',
            'username': 'test_user2',
            'password': '123'
        }

    def test_confirm_email(self):
        user = self.register_user(is_verified=False)
        self.assertFalse(user.is_verified)

        response = self.client.get(f'{reverse("email_verify")}?token={user.token()}')
        self.assertResponse(response, 200, "success")

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

    def test_confirm_email_with_invalid_token(self):
        self.assertResponse(self.client.get(f'{reverse("email_verify")}?token=123456789'), 400, "error")

    def test_confirm_email_with_2_users(self):
        user1 = self.register_user(is_verified=False)
        user2 = self.register_user(email=self.user_data2['email'], password=self.user_data2['password'],
                                   username=self.user_data2['username'], is_verified=False)

        self.client.get(f'{reverse("email_verify")}?token={user1.token()}')

        user1.refresh_from_db()
        user2.refresh_from_db()

        self.assertTrue(user1.is_verified)
        self.assertFalse(user2.is_verified)


class UserLoginTestCase(BaseUserTestCase):
    def test_user_login(self):
        self.register_user()
        self.assertResponse(self.client.post(reverse('login'), data=self.user_data), 200, "success")

    def test_user_login_invalid(self):
        self.register_user()
        invalid_cases = [
            {'email': 'testuser@gmail.com', 'password': '321'},
            {'email': 'testuser1@gmail.com', 'password': '321'},
        ]
        for invalid_data in invalid_cases:
            self.assertResponse(self.client.post(reverse('login'), data=invalid_data), 401, "error")

    def test_user_refresh(self):
        self.register_user()
        response = self.client.post(reverse('login'), data=self.user_data)
        key_refresh = response.data['data']['refresh']

        self.assertResponse(self.client.post(reverse('refresh'), data={'refresh': key_refresh}), 200, "success")

    def test_user_refresh_invalid(self):
        self.assertResponse(self.client.post(reverse('refresh'), data={'refresh': "123456789"}), 401, "error")
