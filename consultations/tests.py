from accounts.tests import BaseUserTestCase
from consultations.models import Consultation, Booked


class ConsultationTestCase(BaseUserTestCase):
    def setUp(self):
        super().setUp()
        self.specialist = self.register_specialist()
        self.data_consultation = {
            'datetime': "2025-10-08 16:00",
            'time_selection': "2",
            'price': 1000,
            'description': 'test description',
        }

    def test_consultation_list(self):
        user = self.register_user("testuser@gmail.com", "123", username='testuser')
        for test_user in [self.specialist, user]:
            response = self.client.get('/consultation/', HTTP_AUTHORIZATION=self.get_jwt(test_user))
            self.assertResponse(response, 200, 'success')

    def test_consultation_create(self):
        specialist2 = self.register_specialist(email='testspecialist2@gmail.com', username='test_specialist2')
        for test_specialist in [self.specialist, specialist2]:
            response = self.client.post('/consultation/',
                                        data=self.data_consultation,
                                        HTTP_AUTHORIZATION=self.get_jwt(test_specialist))
            self.assertResponse(response, 201, 'success')

    def test_consultation_invalid_create(self):
        jwt_specialist = self.get_jwt(self.specialist)
        user = self.register_user("testuser@gmail.com", "123", username='testuser')

        response = self.client.post('/consultation/',
                                    data=self.data_consultation,
                                    HTTP_AUTHORIZATION=self.get_jwt(user))
        self.assertResponse(response, 403, 'error')

        response = self.client.post('/consultation/',
                                    data=self.data_consultation,
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 201, 'success')

        response = self.client.post('/consultation/',
                                    data=self.data_consultation,
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 400, 'error')

        invalid_data_cases = [
            {'datetime': "2024-10-08 16:00"},
            {'datetime': "2025-10-08 25:00"},
            {'datetime': "2025-13-08 18:00"},
            {'datetime': "2025-10-32 18:00"},
            {'datetime': "2025-10-08 18:61"},
            {'datetime': ""},
            {},
            {'datetime': "2025-10-10 16:00", 'price': -1000},
            {'datetime': "2025-10-10 16:00", 'time_selection': "4"},
        ]

        for invalid_data in invalid_data_cases:
            response = self.client.post('/consultation/',
                                        data=invalid_data,
                                        HTTP_AUTHORIZATION=jwt_specialist)
            self.assertResponse(response, 400, 'error')

    def test_consultation_update(self):
        jwt_specialist = self.get_jwt(self.specialist)
        response = self.client.post('/consultation/',
                                    data=self.data_consultation,
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 201, 'success')
        consultation_id = response.data['data']['id']

        update_cases = [
            {'datetime': '2025-10-08 17:00'},
            {'time_selection': "3"},
            {'datetime': "2025-10-08 23:00", 'time_selection': "3"},
            {'price': 900},
            {'description': 'test description update'}
        ]
        expected_cases = [
            {'start': '2025-10-08 17:00', 'end': '2025-10-08 19:00',
             'price': 1000, 'description': 'test description'},
            {'start': '2025-10-08 17:00', 'end': '2025-10-08 20:00',
             'price': 1000, 'description': 'test description'},
            {'start': '2025-10-08 23:00', 'end': '2025-10-09 02:00',
             'price': 1000, 'description': 'test description'},
            {'start': "2025-10-08 23:00", 'end': '2025-10-09 02:00',
             'price': 900, 'description': 'test description'},
            {'start': '2025-10-08 23:00', 'end': '2025-10-09 02:00',
             'price': 900, 'description': "test description update"}
        ]

        for update, expected in zip(update_cases, expected_cases):
            response = self.client.patch(f'/consultation/{consultation_id}/',
                                         data=update,
                                         content_type='application/json',
                                         HTTP_AUTHORIZATION=jwt_specialist)
            self.assertResponse(response, 200, 'success')
            self.assertEqual(response.data['data']['datetime']['start'], expected['start'])
            self.assertEqual(response.data['data']['datetime']['end'], expected['end'])
            self.assertEqual(response.data['data']['price'], expected['price'])
            self.assertEqual(response.data['data']['description'], expected['description'])

    def test_consultation_invalid_update(self):
        jwt_specialist = self.get_jwt(self.specialist)
        user = self.register_user('testuser@gmail.com', '123', username='testuser')
        specialist2 = self.register_specialist('testspecialist2@gmail.com', 'testspecialist2')

        response = self.client.post('/consultation/',
                                    data=self.data_consultation,
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 201, 'success')
        consultation_id = response.data['data']['id']

        response = self.client.patch(f'/consultation/{consultation_id}/',
                                     data={'price': 100},
                                     content_type='application/json',
                                     HTTP_AUTHORIZATION=self.get_jwt(user))
        self.assertResponse(response, 403, 'error')

        response = self.client.patch(f'/consultation/{consultation_id}/',
                                     data={'price': 100},
                                     content_type='application/json',
                                     HTTP_AUTHORIZATION=self.get_jwt(specialist2))
        self.assertResponse(response, 403, 'error')

        invalid_data_cases = [
            {'datetime': "2024-10-08 16:00"},
            {'datetime': "2025-10-08 25:00"},
            {'datetime': "2025-13-08 18:00"},
            {'datetime': "2025-10-32 18:00"},
            {'datetime': "2025-10-08 18:61"},
            {'datetime': ""},
            {},
            {'price': -1000},
            {'time_selection': "4"},
            {'time_selection': ""},
        ]

        for invalid_data in invalid_data_cases:
            response = self.client.patch(f'/consultation/{consultation_id}/',
                                         data=invalid_data,
                                         content_type='application/json',
                                         HTTP_AUTHORIZATION=jwt_specialist)
            self.assertResponse(response, 400, 'error')

    def test_consultation_cancellation(self):
        jwt_specialist = self.get_jwt(self.specialist)

        response = self.client.post('/consultation/',
                                    data=self.data_consultation,
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 201, 'success')

        id_consultation = response.data['data']['id']

        response = self.client.post('/consultation/cancellation/',
                                    data={
                                        'id': id_consultation,
                                        'rejection_text': 'test rejection text',
                                    },
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 200, 'success')
        consultation = Consultation.objects.get(id=id_consultation)
        self.assertEqual(consultation.archive, True)

    def test_consultation_invalid_cancellation(self):
        jwt_specialist = self.get_jwt(self.specialist)
        specialist_2 = self.register_specialist(email='testspecialist2@gmail.com', username='test_specialist2')
        jwt_specialist_2 = self.get_jwt(specialist_2)

        response = self.client.post('/consultation/',
                                    data=self.data_consultation,
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 201, 'success')

        id_consultation = response.data['data']['id']

        response = self.client.post('/consultation/cancellation/',
                                    data={
                                        'id': id_consultation,
                                        'rejection_text': 'test rejection text',
                                    },
                                    HTTP_AUTHORIZATION=jwt_specialist_2)
        self.assertResponse(response, 403, 'error')

        response = self.client.post('/consultation/cancellation/',
                                    data={
                                        'id': id_consultation,
                                    },
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 400, 'error')

        response = self.client.post('/consultation/cancellation/',
                                    data={
                                        'rejection_text': 'test rejection text',
                                    },
                                    HTTP_AUTHORIZATION=jwt_specialist)
        self.assertResponse(response, 404, 'error')


class BookedTestCase(BaseUserTestCase):
    def create_consultation(self, data_consultation) -> str:
        response = self.client.post('/consultation/',
                                    data=data_consultation,
                                    HTTP_AUTHORIZATION=self.jwt_specialist)
        self.assertResponse(response, 201, 'success')
        return response.data['data']['id']

    def create_booked(self, jwt_user: str, status_code=201, status_message='success'):
        response = self.client.post('/booked/',
                                    data={'consultation': self.id_consultation,
                                          "description": "test description"},
                                    HTTP_AUTHORIZATION=jwt_user or self.jwt_user)
        self.assertResponse(response, status_code, status_message)
        if response.status_code == 201:
            return response.data['data']['id']

    def update_booked(self, jwt_user: str, id_booked: str, data, status_code=200, status_message='success'):
        response = self.client.patch(f'/booked/{id_booked}/',
                                     data=data,
                                     HTTP_AUTHORIZATION=jwt_user or self.jwt_user,
                                     content_type='application/json')
        self.assertResponse(response, status_code, status_message)
        return response

    def accept_booked(self, jwt_user: str, data, status_code=200, status_message='success'):
        response = self.client.post('/booked/accept/',
                                    data=data,
                                    HTTP_AUTHORIZATION=jwt_user or self.jwt_user)
        self.assertResponse(response, status_code, status_message)
        return response

    def cancellation_booked(self, jwt_user: str, data, status_code=200, status_message='success'):
        response = self.client.post('/booked/cancellation/',
                                    data=data,
                                    HTTP_AUTHORIZATION=jwt_user or self.jwt_user)
        self.assertResponse(response, status_code, status_message)
        return response

    def setUp(self):
        super().setUp()

        self.user = self.register_user()
        self.jwt_user = self.get_jwt(self.user)

        self.specialist = self.register_specialist()

        self.jwt_specialist = self.get_jwt(self.specialist)

        self.id_consultation = self.create_consultation({'datetime': "2025-10-08 16:00",
                                                         'time_selection': "1",
                                                         'price': 0,
                                                         'description': 'test description 1'})

        self.user_2 = self.register_user(email='testuser2@gmail.com', username='testuser2', password='123')
        self.jwt_user_2 = self.get_jwt(self.user_2)
        self.id_booked = self.create_booked(jwt_user=self.jwt_user)

    def test_booked_list(self):
        for user in [self.specialist, self.user]:
            response = self.client.get('/booked/', HTTP_AUTHORIZATION=self.get_jwt(user))
            self.assertResponse(response, 200, 'success')

    def test_booked_create(self):
        id_booked = self.create_booked(jwt_user=self.jwt_user_2)
        booked = Booked.objects.get(id=id_booked)
        self.assertEqual(booked.consultation.id, self.id_consultation)
        self.assertEqual(booked.description, "test description")
        self.assertEqual(booked.status, "In processing")

        consultation = Consultation.objects.get(id=self.id_consultation)
        self.assertEqual(consultation.booking, False)

    def test_booked_invalid_create(self):
        self.create_booked(jwt_user=self.jwt_specialist,
                           status_code=400,
                           status_message='error')

        self.accept_booked(jwt_user=self.jwt_specialist, data={'id': self.id_booked})

        self.create_booked(jwt_user=self.jwt_user,
                           status_code=400,
                           status_message='error')

        self.create_booked(jwt_user=self.jwt_user_2,
                           status_code=400,
                           status_message='error')

        response = self.client.post('/booked/')
        self.assertResponse(response, 401, 'error')

    def test_booked_update(self):
        data_update = [
            {'description': 'test description 1'},
            {'description': 'test description 2'},
            {'description': 'test description 3'},
        ]
        for data in data_update:
            response = self.update_booked(jwt_user=self.jwt_user,
                                          id_booked=self.id_booked,
                                          data=data)
            self.assertEqual(response.data['data']['description'], data['description'])

    def test_booled_invalid_update(self):
        data_update = [
            {'id': 100},
            {'consultation': 123},
            {'archive': True},
            {'status': "Booked"},
            {'user': self.user_2.id},
        ]

        self.update_booked(jwt_user=self.jwt_user_2,
                           id_booked=self.id_booked,
                           data={'description': 'test description 1'},
                           status_code=403,
                           status_message='error')

        self.update_booked(jwt_user=self.jwt_specialist,
                           id_booked=self.id_booked,
                           data={'description': 'test description 1'},
                           status_code=403,
                           status_message='error')

        for data in data_update:
            self.update_booked(jwt_user=self.jwt_user,
                               id_booked=self.id_booked,
                               data=data,
                               status_code=400,
                               status_message='error')

    def test_booked_accept(self):
        id_booked_2 = self.create_booked(jwt_user=self.jwt_user_2)

        self.accept_booked(jwt_user=self.jwt_specialist, data={'id': self.id_booked})

        booked_1 = Booked.objects.get(id=self.id_booked)
        booked_2 = Booked.objects.get(id=id_booked_2)
        consultation = Consultation.objects.get(id=self.id_consultation)

        self.assertEqual(consultation.booking, True)
        self.assertEqual(booked_1.status, 'Booked')
        self.assertEqual(booked_2.status, 'Cancelled')

    def test_booked_invalid_accept(self):
        self.accept_booked(jwt_user=self.jwt_user,
                           data={'id': self.id_booked},
                           status_code=403,
                           status_message='error')

        self.accept_booked(jwt_user=self.jwt_user_2,
                           data={'id': self.id_booked},
                           status_code=403,
                           status_message='error')

        self.accept_booked(jwt_user=self.jwt_specialist,
                           data={},
                           status_code=404,
                           status_message='error')

        self.accept_booked(jwt_user=self.jwt_specialist,
                           data={'id': 1234},
                           status_code=404,
                           status_message='error')

    def test_booked_cancellation(self):
        id_booked_2 = self.create_booked(jwt_user=self.jwt_user_2)

        self.cancellation_booked(jwt_user=self.jwt_specialist,
                                 data={'id': self.id_booked,
                                       'rejection_text': 'test rejection text'})

        self.cancellation_booked(jwt_user=self.jwt_specialist,
                                 data={'id': id_booked_2,
                                       'rejection_text': 'test rejection text'})

        booked_1 = Booked.objects.get(id=self.id_booked)
        booked_2 = Booked.objects.get(id=id_booked_2)

        self.assertEqual(booked_1.status, 'Cancelled')
        self.assertEqual(booked_2.status, 'Cancelled')

        self.assertEqual(booked_1.rejection_text, 'test rejection text')
        self.assertEqual(booked_2.rejection_text, 'test rejection text')

        id_booked_1 = self.create_booked(jwt_user=self.jwt_user)

        id_booked_2 = self.create_booked(jwt_user=self.jwt_user_2)

        self.cancellation_booked(jwt_user=self.jwt_user,
                                 data={'id': id_booked_1,
                                       'rejection_text': 'test rejection text'})

        self.cancellation_booked(jwt_user=self.jwt_user_2,
                                 data={'id': id_booked_2,
                                       'rejection_text': 'test rejection text'})

    def atest_booked_invalid_cancellation(self):
        id_booked_2 = self.create_booked(jwt_user=self.jwt_user_2)

        self.cancellation_booked(jwt_user=self.jwt_user_2,
                                 data={'id': self.id_booked,
                                       'rejection_text': 'test rejection text'},
                                 status_code=403,
                                 status_message='error')

        self.cancellation_booked(jwt_user=self.jwt_user,
                                 data={'id': id_booked_2,
                                       'rejection_text': 'test rejection text'},
                                 status_code=403,
                                 status_message='error')

        self.cancellation_booked(jwt_user=self.jwt_user,
                                 data={'id': self.id_booked},
                                 status_code=400,
                                 status_message='error')

        self.cancellation_booked(jwt_user=self.jwt_user,
                                 data={},
                                 status_code=404,
                                 status_message='error')
