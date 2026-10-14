from locust import HttpUser, between, task

from load_tests.scenarios.common import choose_user, load_data


class LoginUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        self.user_data = choose_user(load_data())

    @task
    def login(self) -> None:
        self.client.post(
            "/auth/login",
            json={"email": self.user_data["email"], "password": self.user_data["password"]},
        )
