from typing import List


class ErrorMessages:
    INT_IDENTIFIER_TYPE = 'Don\'t know how to convert from class java.lang.Integer to class org.openmrs.PatientIdentifierType'
    EMPTY_IDENTIFIER_TYPE = 'Cannot invoke "org.openmrs.PatientIdentifierType.getUuid()" because "identifierType" is null'

    INT_LOCATION = 'Don\'t know how to convert from class java.lang.Integer to class org.openmrs.Location'
    EMPTY_LOCATION = 'Cannot invoke "org.openmrs.Location.getUuid()" because "location" is null'

    INT_IDENTIFIER = 'identifiers on class org.openmrs.Patient => identifier on class org.openmrs.PatientIdentifier => Don\'t know how to convert from class java.lang.Integer to class java.lang.String'

    INVALID_SUBMISSION = 'Invalid Submission'

    USER_IS_NOT_LOGGED_IN = "User is not logged in [Privileges required: Get People]"

    @staticmethod
    def privileges_required(privileges: List[str]):
        return f'User is logged in but doesn\'t have the relevant privilege [Privileges required: {",".join(privileges)}]'
