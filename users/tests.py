from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AuthenticationApiTests(APITestCase):
    def test_signup_login_me_and_logout(self):
        signup = self.client.post(reverse("auth-signup"), {
            "first_name": "Jane", "last_name": "Doe", "email": "JANE@example.com", "password": "A-secure-password-917!",
        }, format="json")
        self.assertEqual(signup.status_code, 201)
        self.assertNotIn("password", signup.data)
        token = signup.data["token"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(self.client.get(reverse("auth-me")).data["email"], "jane@example.com")
        self.assertEqual(self.client.post(reverse("auth-logout")).status_code, 204)

        self.client.credentials()
        login = self.client.post(reverse("auth-login"), {"email": "jane@example.com", "password": "A-secure-password-917!"}, format="json")
        self.assertEqual(login.status_code, 200)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        payload = {"email": "jane@example.com", "password": "A-secure-password-917!"}
        self.assertEqual(self.client.post(reverse("auth-signup"), payload, format="json").status_code, 201)
        payload["email"] = "JANE@example.com"
        self.assertEqual(self.client.post(reverse("auth-signup"), payload, format="json").status_code, 400)

    def test_signup_works_during_dashboard_session(self):
        staff = get_user_model().objects.create_user(
            username="dashboard-manager", password="test-password", is_staff=True
        )
        self.client.force_login(staff)
        response = self.client.post(reverse("auth-signup"), {
            "first_name": "Ajina", "last_name": "Santhosh",
            "email": "ajina@example.com", "password": "Secure-account-password-917!",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)

    def test_authenticated_customer_can_manage_address_and_change_password(self):
        signup = self.client.post(reverse("auth-signup"), {
            "email": "customer@example.com", "password": "Original-password-917!", "first_name": "Jane",
        }, format="json")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {signup.data['token']}")
        address = self.client.post(reverse("account-address-list"), {
            "label": "Home", "full_name": "Jane Doe", "address_line_1": "1 Main Street",
            "city": "Dublin", "county": "Dublin", "country_code": "IE", "is_default": True,
        }, format="json")
        self.assertEqual(address.status_code, 201)
        self.assertEqual(self.client.get(reverse("account-address-list")).data["count"], 1)
        changed = self.client.post(reverse("password-change"), {
            "current_password": "Original-password-917!", "new_password": "Changed-password-821!",
        }, format="json")
        self.assertEqual(changed.status_code, 200)
        self.client.credentials()
        login = self.client.post(reverse("auth-login"), {"email": "customer@example.com", "password": "Changed-password-821!"}, format="json")
        self.assertEqual(login.status_code, 200)
