from accounts.tests import BaseUserTestCase
from accounts.models import User
from specialist.models import Specialist


class SpecialistTestCase(BaseUserTestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.register_user('admin@gmail.com', '123', 'admin', is_superuser=True, is_staff=True)
        self.jwt_admin = self.get_jwt(self.admin)

    def block_specialist(self, specialist, jwt, status=200, message='success'):
        response = self.client.post('/specialist/block/',
                                    data={'id': specialist.id},
                                    headers={'Authorization': jwt})
        self.assertResponse(response, status, message)

    def unblock_specialist(self, specialist, jwt, status=200, message='success'):
        response = self.client.post('/specialist/unblock/',
                                    data={'id': specialist.id},
                                    headers={'Authorization': jwt})
        self.assertResponse(response, status, message)

    def test_specialist_list(self):
        specialist = self.register_specialist()
        user = self.register_user('testuser@gmail.com', '123', 'test_user')

        response = self.client.get('/specialist/', headers={'Authorization': f'{self.get_jwt(self.admin)}'})
        self.assertResponse(response, 200, "success")

        for u in [specialist, user]:
            response = self.client.get('/specialist/', headers={'Authorization': f'{self.get_jwt(u)}'})
            self.assertResponse(response, 403, "error")

    def test_specialist_detail(self):
        specialist = self.register_specialist()

        response = self.client.get(f'/specialist/{specialist.id}/', headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")

        response = self.client.get(f'/specialist/{specialist.id}/',
                                   headers={'Authorization': f'{self.get_jwt(specialist)}'})
        self.assertResponse(response, 403, "error")

    def test_block_unblock_specialist(self):
        specialist = self.register_specialist()

        response = self.client.get(f'/specialist/{specialist.id}/', headers={'Authorization': self.jwt_admin})
        self.assertEqual(response.data.get("data").get('is_active'), True)

        self.block_specialist(specialist, self.jwt_admin)
        response = self.client.get(f'/specialist/{specialist.id}/', headers={'Authorization': self.jwt_admin})
        self.assertEqual(response.data.get("data").get('is_active'), False)

        self.unblock_specialist(specialist, self.jwt_admin)
        response = self.client.get(f'/specialist/{specialist.id}/', headers={'Authorization': self.jwt_admin})
        self.assertEqual(response.data.get("data").get('is_active'), True)

    def test_specialist_filter(self):
        for i in range(5):
            self.register_specialist(email=f'testspecialist{i}@gmail.com', username=f'test_specialist_{i}')

        response = self.client.get('/specialist/', {'user__username': 'test_specialist_1'},
                                   headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data['data']['count'], 1)

        response = self.client.get('/specialist/', {'is_active': 'True'}, headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data['data']['count'], 5)

        specialist = User.objects.get(username="test_specialist_1")
        self.block_specialist(specialist, self.jwt_admin)

        response = self.client.get('/specialist/', {'is_active': 'True'}, headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data['data']['count'], 4)

    def test_specialist_update(self):
        specialist = self.register_specialist()

        response = self.client.patch(f'/specialist/{specialist.id}/',
                                     {'description': 'Test description 1'},
                                     content_type='application/json',
                                     headers={'Authorization': self.get_jwt(specialist)})
        self.assertResponse(response, 200, "success")

        specialist = Specialist.objects.get(user=specialist)
        self.assertEqual(specialist.description, 'Test description 1')


class CandidatesTestCase(BaseUserTestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.register_user('admin@gmail.com', '123', 'admin', is_superuser=True, is_staff=True)
        self.jwt_admin = self.get_jwt(self.admin)

    def create_candidate(self, email='testcandidates@gmail.com', username='test_candidates'):
        user = self.register_user(email=email, password='123', username=username)
        self.client.post('/candidates/', {'description': 'Test Candidate'},
                         headers={'Authorization': self.get_jwt(user)})
        return user

    def accept_candidate(self, candidate, jwt, status=200, message='success'):
        response = self.client.post('/candidates/accept/', data={'id': candidate.id}, headers={'Authorization': jwt})
        self.assertResponse(response, status, message)

    def cancel_candidate(self, candidate, rejection_text, jwt, status=200, message='success'):
        response = self.client.post('/candidates/cancel/', data={'id': candidate.id, 'rejection_text': rejection_text},
                                    headers={'Authorization': jwt})
        self.assertResponse(response, status, message)

    def test_candidates_list(self):
        user = self.register_user('testuser@gmail.com', '123', 'test_user')

        response = self.client.get('/candidates/', headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")

        response = self.client.get('/candidates/', headers={'Authorization': self.get_jwt(user)})
        self.assertResponse(response, 403, "error")

    def test_candidates_register(self):
        user = self.register_user('testuser@gmail.com', '123', 'test_user')

        response = self.client.post('/candidates/', {'description': 'Test Candidate'},
                                    headers={'Authorization': self.get_jwt(user)})
        self.assertResponse(response, 201, "success")

    def test_accept_candidate(self):
        candidate = self.create_candidate()

        response = self.client.get(f'/candidates/{candidate.id}/status/',
                                   headers={'Authorization': self.get_jwt(candidate)})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data.get("data").get("status"), "In processing")

        self.accept_candidate(candidate, self.jwt_admin)

        response = self.client.get(f'/candidates/{candidate.id}/status/',
                                   headers={'Authorization': self.get_jwt(candidate)})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data.get("data").get("status"), "Successfully")

    def test_cancel_candidate(self):
        candidate = self.create_candidate()

        self.cancel_candidate(candidate, "Test cancel", self.jwt_admin)

        response = self.client.get(f'/candidates/{candidate.id}/status/',
                                   headers={'Authorization': self.get_jwt(candidate)})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data.get("data").get("status"), "Cancelled")

    def test_invalid_accept_and_cancel(self):
        candidate = self.create_candidate()
        user = self.register_user('testuser@gmail.com', '123', 'test_user')
        jwt_user = self.get_jwt(user)

        # Попытка принять/отменить не с правами администратора
        self.accept_candidate(candidate, jwt_user, status=403, message='error')
        self.cancel_candidate(candidate, "Test cancel", jwt_user, status=403, message='error')

        # Попытка принять повторно или отменить снова после изменения статуса
        self.accept_candidate(candidate, self.jwt_admin)
        self.accept_candidate(candidate, self.jwt_admin, status=400, message='error')

    def test_candidates_reapplication(self):
        candidate = self.create_candidate()
        self.cancel_candidate(candidate, "Test cancel", self.jwt_admin)
        response = self.client.post('/candidates/reapplication/',
                                    data={'description': 'Test Candidate'},
                                    headers={'Authorization': self.get_jwt(candidate)})

        self.assertResponse(response, 200, "success")

    def test_candidates_check_status(self):
        candidate = self.create_candidate()
        user = self.register_user('testuser@gmail.com', '123', 'test_user')
        jwt_user = self.get_jwt(user)

        response = self.client.get(f'/candidates/{candidate.id}/status/', headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")

        response = self.client.get(f'/candidates/{candidate.id}/status/', headers={'Authorization': jwt_user})
        self.assertResponse(response, 403, "error")

    def test_candidates_filter(self):
        for i in range(5):
            self.create_candidate(email=f'testCandidates{i}@gmail.com', username=f'test_candidates_{i}')

        response = self.client.get('/candidates/',
                                   {'user__username': 'test_candidates_1'},
                                   headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data['data']['count'], 1)

        response = self.client.get('/candidates/',
                                   {'status': 'In processing'},
                                   headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data['data']['count'], 5)

        candidate = User.objects.get(username="test_candidates_1")
        self.accept_candidate(candidate, self.jwt_admin)

        response = self.client.get('/candidates/',
                                   {'status': 'In processing'},
                                   headers={'Authorization': self.jwt_admin})
        self.assertResponse(response, 200, "success")
        self.assertEqual(response.data['data']['count'], 4)
