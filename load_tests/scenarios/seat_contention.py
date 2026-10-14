import random

from locust import HttpUser, between, task

from load_tests.scenarios.common import choose_user, load_data


class SeatContentionUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self) -> None:
        self.data = load_data()
        user_data = choose_user(self.data)
        self.headers = {"Authorization": f"Bearer {user_data['token']}"}
        self.showtime_id = self.data["showtime_ids"][0]
        seats = self.client.get(f"/showtimes/{self.showtime_id}/seats").json()["seats"]
        self.seat_ids = [seat["id"] for seat in seats[:10]]

    @task
    def contend(self) -> None:
        with self.client.post(
            "/bookings",
            headers=self.headers,
            json={"showtime_id": self.showtime_id, "seat_ids": [random.choice(self.seat_ids)]},
            catch_response=True,
        ) as response:
            if response.status_code in (201, 409):
                response.success()
