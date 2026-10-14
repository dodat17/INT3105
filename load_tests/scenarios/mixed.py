import random

from locust import HttpUser, between, task

from load_tests.scenarios.common import choose_user, load_data


class MixedUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self) -> None:
        self.data = load_data()
        self.user_data = choose_user(self.data)
        self.headers = {"Authorization": f"Bearer {self.user_data['token']}"}
        self.booking_ids: list[str] = []

    @task(60)
    def browse(self) -> None:
        self.client.get(random.choice(["/movies", "/showtimes"]))

    @task(20)
    def my_bookings(self) -> None:
        self.client.get("/bookings", headers=self.headers)

    @task(15)
    def book(self) -> None:
        if not self.data["showtime_ids"]:
            return
        showtime_id = random.choice(self.data["showtime_ids"])
        seats = self.client.get(f"/showtimes/{showtime_id}/seats").json().get("seats", [])
        available = [seat for seat in seats if seat["status"] == "AVAILABLE"]
        if not available:
            return
        response = self.client.post(
            "/bookings",
            headers=self.headers,
            json={"showtime_id": showtime_id, "seat_ids": [random.choice(available)["id"]]},
        )
        if response.status_code == 201:
            self.booking_ids.append(response.json()["id"])

    @task(5)
    def cancel(self) -> None:
        if self.booking_ids:
            booking_id = self.booking_ids.pop()
            self.client.delete(f"/bookings/{booking_id}", headers=self.headers)
