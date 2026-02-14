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

    @staticmethod
    def get_bad_iso_utc_string() -> str:
        return f"{faker.date(pattern='%Y-%m-%d')}T99:99:99Z"

    @staticmethod
    def get_impossible_iso_utc() -> str:
        return "2026-13-40T25:61:61.000Z"