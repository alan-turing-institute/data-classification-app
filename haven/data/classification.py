

class QuestionText:
    PUBLIC_AND_OPEN = (
        'Is the data publicly and openly available for use in research?'
    )

    PUBLISHABLE = (
        'Could the data in principle be published if the research team wanted to?'
    )
    DOES_NOT_DESCRIBE_INDIVIDUALS = (
        'Do you have absolute certainty the data does not or could not ever be '
        'used to describe identifiable individual living humans, taking into '
        'account the possibility of re-identification of anonymised or '
        'pseudonymised data?'
    )
    DISCLOSURE_TERMINATION = (
        'If the data were disclosed, would the collaboration resulting in the '
        'institute having access to the data be terminated?'
    )
    DISCLOSURE_EMBARRASSMENT = (
        'If the data were disclosed, would the research institute be subject '
        'to reputational harm or embarassment?'
    )

    INDIVIDUALS_ARE_ANONYMOUS = (
        'Do you have strong confidence that all information about individuals '
        'in the dataset cannot be connected to identified individuals, taking '
        'into account anonymisation and pseudonymisation? '
        'Consider the possibility of re-identification on the basis of other '
        'confidential datasets in the project being combined with this one.'
    )
    DISCLOSURE_PENALTIES = (
        'If the data were disclosed, would the research institute be subject '
        'to financial or criminal penalties?'
    )

    VALUABLE_TO_ENEMIES = (
        'Is the data likely to be of significant value to criminal gangs or '
        'hostile governments?'
    )
