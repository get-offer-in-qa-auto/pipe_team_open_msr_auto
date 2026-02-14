class GeneratorContext:
    reference_provider = None

    @classmethod
    def has_provider(cls) -> bool:
        return cls.reference_provider is not None
