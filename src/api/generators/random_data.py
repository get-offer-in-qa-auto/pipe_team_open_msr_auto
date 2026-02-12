from typing import Union

from faker import Faker

faker = Faker()


class RandomData:
    @staticmethod
    def get_int(min_val, max_val) -> int:
        return faker.pyint(min_value=min_val, max_value=max_val)

    @staticmethod
    def get_word() -> str:
        return faker.word()

    @staticmethod
    def get_string(length: int) -> str:
        return faker.lexify(text="?" * length)

    @staticmethod
    def get_uuid() -> str:
        return faker.uuid4()

    @staticmethod
    def get_number(digits: int, fix_len: bool) -> int:
        return faker.random_number(digits, fix_len)

    @staticmethod
    def get_bad_dt():
        return f"{faker.date(pattern='%Y/%m/%d')} {faker.time(pattern='%H:%M:%S')}"