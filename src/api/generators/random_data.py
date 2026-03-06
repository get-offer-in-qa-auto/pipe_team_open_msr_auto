import allure
from faker import Faker

faker = Faker()


class RandomData:
    @staticmethod
    @allure.step("get_int")
    def get_int(min_val, max_val) -> int:
        return faker.pyint(min_value=min_val, max_value=max_val)

    @staticmethod
    @allure.step("get_word")
    def get_word() -> str:
        return faker.word()

    @staticmethod
    @allure.step("get_string")
    def get_string(length: int) -> str:
        return faker.lexify(text="?" * length)

    @staticmethod
    @allure.step("get_uuid")
    def get_uuid() -> str:
        return faker.uuid4()

    @staticmethod
    @allure.step("get_number")
    def get_number(digits: int, fix_len: bool) -> int:
        return faker.random_number(digits, fix_len)

    @staticmethod
    @allure.step("get_bad_dt")
    def get_bad_dt():
        return f"{faker.date(pattern='%Y/%m/%d')} {faker.time(pattern='%H:%M:%S')}"

    @staticmethod
    @allure.step("get_bad_iso_utc_string")
    def get_bad_iso_utc_string() -> str:
        return f"{faker.date(pattern='%Y-%m-%d')}T99:99:99Z"

    @staticmethod
    @allure.step("get_impossible_iso_utc")
    def get_impossible_iso_utc() -> str:
        return "2026-13-40T25:61:61.000Z"