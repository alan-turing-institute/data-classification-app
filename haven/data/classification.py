from data.tiers import Tier


def insert_question(model_cls, **kwargs):
    q = model_cls(**kwargs)
    q.full_clean()
    q.save()
    return q


def insert_initial_questions(model_cls):
    # This method should only be called on an empty database (i.e. on first
    # migration or during tests). If you make changes, they will not be
    # reflected in the actual database unless you make a related migration.
    assert not model_cls.objects.exists()
    q13 = insert_question(
        model_cls,
        name='sophisticated_attack',
        question=('Do likely attackers include sophisticated, '
                  'well-resourced and determined threats, such as highly '
                  'capable serious organised crime groups and state '
                  'actors?'),
        yes_tier=Tier.FOUR,
        no_tier=Tier.THREE,
    )
    q12 = insert_question(
        model_cls,
        name='no_reidentify_strong',
        question=('Is your confidence that it is not possible to '
                  're-identify individuals from the data strong?'),
        yes_tier=Tier.TWO,
        no_tier=Tier.THREE,
    )
    q11 = insert_question(
        model_cls,
        name='financial_low',
        question=('Are the legal or financial consequences of disclosure '
                  'low?'),
        yes_tier=Tier.TWO,
        no_question=q13,
    )
    q9 = insert_question(
        model_cls,
        name='include_commercial',
        question=('Will you be working with commercial-in-confidence '
                  'information or third-party intellectual property?'),
        yes_question=q11,
        no_tier=Tier.ONE,
    )
    q10 = insert_question(
        model_cls,
        name='no_reidentify_absolute',
        question=('Is your confidence that it is not possible to '
                  're-identify individuals from the data absolute?'),
        yes_question=q9,
        no_question=q12
    )
    q8 = insert_question(
        model_cls,
        name='open_publication',
        question=('Will you be working in an open, continuously published '
                  'manner?'),
        yes_tier=Tier.ZERO,
        no_tier=Tier.ONE
    )
    q7 = insert_question(
        model_cls,
        name='substantial_threat',
        question=('Would disclosure pose a substantial threat to the '
                  'personal safety, health or security of the data '
                  'subjects?'),
        yes_tier=Tier.FOUR,
        no_tier=Tier.THREE,
    )
    q6 = insert_question(
        model_cls,
        name='closed_identify_living',
        question='Does the data identify living individuals?',
        yes_question=q7,
        no_question=q10,
    )
    q5 = insert_question(
        model_cls,
        name='closed_personal',
        question=('Will you be working with data related to living '
                  'individuals, or derived from such data? (e.g. '
                  'pseudonymised or synthetic data)'),
        yes_question=q6,
        no_question=q9,
    )
    q4 = insert_question(
        model_cls,
        name='publishable',
        question=('Could all the data handled or generated be published, '
                  'albeit at the loss of research competitiveness?'),
        yes_question=q8,
        no_question=q5,
    )
    q3 = insert_question(
        model_cls,
        name='open_generate_new',
        question=('Will you be generating (including by selecting or '
                  'sorting) new personal information about individuals?'),
        yes_question=q7,
        no_question=q8,
    )
    q2 = insert_question(
        model_cls,
        name='open_identify_living',
        question=('Does the data identify living individuals? (e.g. '
                  'social media data)'),
        yes_question=q3,
        no_question=q8,
    )
    insert_question(
        model_cls,
        name='public_and_open',
        question=('Are all input datasets to the project publicly and '
                  'openly available for use in research?'),
        yes_question=q2,
        no_question=q4,
    )
