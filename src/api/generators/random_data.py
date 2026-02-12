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
    def get_uuid():
        return faker.uuid4()