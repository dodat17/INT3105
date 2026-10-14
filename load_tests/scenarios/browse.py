import random

from locust import HttpUser, between, task

from load_tests.scenarios.common import load_data


class BrowseUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self) -> None:
        self.data = load_data()

    @task(3)
    def movies(self) -> None:
        self.client.get("/movies")

    @task(2)
    def showtimes(self) -> None:
        self.client.get("/showtimes")

    @task
    def seats(self) -> None:
        if self.data["showtime_ids"]:
            showtime_id = random.choice(self.data["showtime_ids"])
            self.client.get(f"/showtimes/{showtime_id}/seats")
