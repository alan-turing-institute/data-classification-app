from django.core.exceptions import ObjectDoesNotExist
from simple_history.manager import HistoryManager
from simple_history.models import HistoricalRecords

from data.tiers import Tier


CLOSED_PERSONAL = 'Will any project input be personal data?'
FINANCIAL_LOW = (
    'Do you have high confidence that the commercial, legal, '
    'reputational or political consequences of unauthorised '
    'disclosure of this data will be low?')
FINANCIAL_LOW_PERSONAL = (
    'Do you have high confidence that the commercial, legal, '
    'reputational or political consequences of unauthorised '
    'disclosure of this data will be low?')
INCLUDE_COMMERCIAL = (
    'Will you be working with commercial-in-confidence '
    'information or private third-party intellectual property, '
    'or legally or politically sensitive data?')
INCLUDE_COMMERCIAL_PERSONAL = (
    'Will you also be working with commercial-in-confidence '
    'information or private third-party intellectual property, '
    'or legally or politically sensitive data?')
NO_REIDENTIFY = 'Is that personal data pseudonymized?'
NO_REIDENTIFY_ABSOLUTE = (
    'Do you have absolute confidence that it is not possible '
    'to identify individuals from the data, either at the '
    'point of entry or as a result of any analysis that may '
    'be carried out?')
NO_REIDENTIFY_STRONG = (
    'Do you have strong confidence that it is not possible to '
    'identify individuals from the data, either at the point of '
    'entry or as a result of any analysis that may be carried '
    'out?')
OPEN_GENERATE_NEW = (
    'Will the research generate (including by selecting, or '
    'sorting or combining) any personal data?')
OPEN_PUBLICATION = (
    'Will releasing any of the datasets or results impact on '
    'the competitive advantage of the research team?')
PUBLIC_AND_OPEN = (
    'Is that personal data legally accessible by the general '
    'public with no restrictions on use?')
PUBLISHABLE = (
    'Do you have high confidence that the commercial, legal, '
    'reputational or political consequences of unauthorised '
    'disclosure of this data will be so low as to be trivial?')
SOPHISTICATED_ATTACK = (
    'Do likely attackers include sophisticated, '
    'well-resourced and determined threats, such as highly '
    'capable serious organised crime groups and state '
    'actors?')
SUBSTANTIAL_THREAT = (
    'Would disclosure pose a substantial threat to the '
    'personal safety, health or security of the data '
    'subjects?')


def initial_questions():
    questions = [
        {
            'name': 'sophisticated_attack',
            'question': SOPHISTICATED_ATTACK,
            'yes_tier': Tier.FOUR,
            'no_tier': Tier.THREE,
        },
        {
            'name': 'financial_low_personal',
            'question': FINANCIAL_LOW_PERSONAL,
            'yes_tier': Tier.TWO,
            'no_question': 'sophisticated_attack',
        },
        {
            'name': 'include_commercial_personal',
            'question': INCLUDE_COMMERCIAL_PERSONAL,
            'yes_question': 'financial_low_personal',
            'no_tier': Tier.TWO,
        },
        {
            'name': 'no_reidentify_strong',
            'question': NO_REIDENTIFY_STRONG,
            'yes_question': 'include_commercial_personal',
            'no_question': 'sophisticated_attack',
        },
        {
            'name': 'publishable',
            'question': PUBLISHABLE,
            'yes_tier': Tier.ONE,
            'no_tier': Tier.TWO,
        },
        {
            'name': 'financial_low',
            'question': FINANCIAL_LOW,
            'yes_question': 'publishable',
            'no_question': 'sophisticated_attack',
        },
        {
            'name': 'substantial_threat',
            'question': SUBSTANTIAL_THREAT,
            'yes_tier': Tier.FOUR,
            'no_tier': Tier.THREE,
        },
        {
            'name': 'open_publication',
            'question': OPEN_PUBLICATION,
            'yes_tier': Tier.ONE,
            'no_tier': Tier.ZERO,
        },
        {
            'name': 'include_commercial',
            'question': INCLUDE_COMMERCIAL,
            'yes_question': 'financial_low',
            'no_question': 'open_publication',
        },
        {
            'name': 'no_reidentify_absolute',
            'question': NO_REIDENTIFY_ABSOLUTE,
            'yes_question': 'include_commercial',
            'no_question': 'no_reidentify_strong',
        },
        {
            'name': 'no_reidentify',
            'question': NO_REIDENTIFY,
            'yes_question': 'no_reidentify_absolute',
            'no_question': 'substantial_threat',
        },
        {
            'name': 'public_and_open',
            'question': PUBLIC_AND_OPEN,
            'yes_question': 'include_commercial',
            'no_question': 'no_reidentify',
        },
        {
            'name': 'closed_personal',
            'question': CLOSED_PERSONAL,
            'yes_question': 'public_and_open',
            'no_question': 'include_commercial',
        },
        {
            'name': 'open_generate_new',
            'question': OPEN_GENERATE_NEW,
            'yes_question': 'substantial_threat',
            'no_question': 'closed_personal',
        }
    ]

    for q in questions:
        q.setdefault('yes_question', None)
        q.setdefault('no_question', None)
        q.setdefault('yes_tier', None)
        q.setdefault('no_tier', None)

    return questions

def insert_initial_questions(model_cls):
    questions = {}
    assert not model_cls.objects.exists()

    for kwargs in initial_questions():
        if kwargs['yes_question']:
            kwargs['yes_question'] = questions[kwargs['yes_question']]
        if kwargs['no_question']:
            kwargs['no_question'] = questions[kwargs['no_question']]
        q = model_cls(**kwargs)
        q.full_clean()
        q.save()
        questions[q.name] = q

    for k, q in questions.items():
        assert k == q.name


def verify_initial_questions(apps):
    ClassificationQuestion = apps.get_model('data', 'ClassificationQuestion')
    stored = ClassificationQuestion.objects.filter(hidden=False)
    initial = { q['name']: q for q in initial_questions() }
    if len(stored) != len(initial):
        raise RuntimeError(f"Expected {len(initial)} questions but there were {len(stored)}")
    for q in stored:
        q = {
            'name': q.name,
            'question': q.question,
            'yes_question': q.yes_question,
            'no_question': q.no_question,
            'yes_tier': q.yes_tier,
            'no_tier': q.no_tier,
        }
        if q['yes_question']:
            q['yes_question'] = q['yes_question'].name
        if q['no_question']:
            q['no_question'] = q['no_question'].name
        q2 = initial[q['name']]

        if q != q2:
            raise RuntimeError(f"Expected {q['name']} to be {q2} but was {q}")


# In a migration, you don't have access to the actual model class, just a historical version
# of it, which doesn't have non-field attributes. This means that
# ClassificationQuestion.history isn't set, and changes to the question aren't captured in the
# history table. This is a set of methods which allows you to write migrations that capture the
# history

def migrate_question(apps, name, kwargs):
    ClassificationQuestion = apps.get_model('data', 'ClassificationQuestion')
    q = ClassificationQuestion.objects.get(name=name)
    if kwargs['yes_question']:
        kwargs['yes_question'] = ClassificationQuestion.objects.get(name=kwargs['yes_question'])
    if kwargs['no_question']:
        kwargs['no_question'] = ClassificationQuestion.objects.get(name=kwargs['no_question'])
    q.question = kwargs['question']
    q.yes_question = kwargs['yes_question']
    q.no_question = kwargs['no_question']
    q.yes_tier = kwargs['yes_tier']
    q.no_tier = kwargs['no_tier']
    q.save()
    history = _attach_history(apps, q)
    history.post_save(q, created=False)


def insert_blank_question_if_necessary(apps, name):
    ClassificationQuestion = apps.get_model('data', 'ClassificationQuestion')
    q, created = ClassificationQuestion.objects.get_or_create(name=name)
    if created:
        history = _attach_history(apps, q)
        history.post_save(q, created=True)


def hide_question_if_present(apps, name):
    ClassificationQuestion = apps.get_model('data', 'ClassificationQuestion')
    try:
        q = ClassificationQuestion.objects.get(name=name)
        q.hidden = True
        q.save()
        history = _attach_history(apps, q)
        history.post_save(q, created=False)
    except ObjectDoesNotExist:
        pass


def _attach_history(apps, q):
    ClassificationQuestion = apps.get_model('data', 'ClassificationQuestion')
    HistoricalClassificationQuestion = apps.get_model('data', 'HistoricalClassificationQuestion')
    manager = HistoryManager(HistoricalClassificationQuestion)
    q.history = manager
    history = HistoricalRecords()
    history.manager_name = 'history'
    history.cls = ClassificationQuestion.__class__
    return history
