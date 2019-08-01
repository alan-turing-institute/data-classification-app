from django.core.exceptions import ObjectDoesNotExist
from simple_history.manager import HistoryManager
from simple_history.models import HistoricalRecords

from data.tiers import Tier


# Classification questions are stored in the database, but since they are important we want them
# to be a) managed through migrations, b) tested and c) versioned
# The combination of these three things turns out be quite tricky, since in a migration,
# you don't have access to the actual model class, just a historical version of it, which
# doesn't have non-field attributes. This means that ClassificationQuestion.history isn't set,
# and changes to the question aren't captured in the history table.
# In addition, you can't share code with a migration, since the migration may not be run until a
# later time, at which point the code may have diverged. You also have to account for the fact that
# different databases may not be in the same state.
#
# The best way to make changes to the flowchart is therefore:
# * Update various tests to match how you expect the flowchart to work
# * Change the constants, initial_guidance and initial_questions to match the new flowchart
# * Once you're happy with the tests, create the migrations
# * Run `haven/manage.py makemigrations --empty data`
# * Copy the contents of this module into the migration
# * Add `migrations.RunPython(migrate_questions)` into the list of operations
# * Update the migrate_questions method accordingly
# * Run and test the migration
#
# For more complicated changes, you may need to adapt these instructions.
#
# If you've had to change the schema
# * Run `haven/manage.py makemigrations` before creating your empty migration (so that you have
#   two separate migrations, one schema & one data)
#
# If you have to change anything in this module other than the question definitions (e.g. because
# you changed the schema):
# * Initially copy only the imports, constants, initial_guidance, initial_questions and
#   migrate_questions into the new migration
# * Edit the migrate_questions as above
# * Add a `from data import classification`, and change all method calls in migrate_questions to
#   reference this module, e.g. change `do_something()` to `classification.do_something()`
# * Run and test the migration
# * Once you're happy with the migration, copy the remaining methods from this class into the
#   migration
# * Delete the references to this class, e.g. delete `from data import classification` and change
#   `classification.do_something()` to just `do_something()`
# * Fake rollback of the migration: `haven/manage.py migrate --fake data <previous_migration_name>`
# * Rerun your migration
# * This process is convoluted, but is designed to ensure you don't make a change only in the
#   migration, and not this module, which would cause problems next time we try to write another
#   migration


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


COMMERCIAL_DATA = (
    'Commercial-in-confidence data is information which, if disclosed, may result in damage to a '
    'party’s commercial interest, intellectual property, or trade secrets.')
PERSONAL_DATA = (
    'Personal data is any information relating to an identified or identifiable living individual '
    '(see below); an \'identifiable\' living individual is one who can be identified, directly '
    'or indirectly, in particular by reference to an identifier such as a name, an '
    'identification number, location data, an online identifier or to one or more factors '
    'specific to the physical, physiological, genetic, mental, economic, cultural or social '
    'identity of that natural person. The term \'indirectly\' here indicates that this includes '
    'data where identification is made possible by combining one or more sets of data, including '
    'synthetic data or trained models.')
PSEUDONYMIZED_DATA = (
    'Pseudonymised data is personal data that has been processed in such a manner that it can '
    'no longer be attributed to a specific living individual without the use of additional '
    'information, which is kept separately and subject to technical and organisational measures '
    'that ensure that the personal data are not attributed to an identified or identifiable '
    'living individual. Two important things to note are that pseudonymised data: is still '
    'personal data - it becomes anonymised data, and is no longer personal data, only if both '
    'the key data connecting pseudonyms to real numbers is securely destroyed, and no other data '
    'exists in the world which could be used statistically to re-identify individuals from the '
    'data; and depending on the method used, it normally includes synthetic data and models that '
    'have been trained on personal data. Expert review is needed to determine the degree to which '
    'such datasets could allow individuals to be identified. It is important that both '
    'researchers and Dataset Providers consider the level of confidence they have in the '
    'likelihood of identifying individuals from data. Anonymised data is data which under no '
    'circumstances can be used to identify an individual, and this is less common than many '
    'realise. Our model specifies three levels of confidence that classifiers can have about '
    'the likelihood of reidentification, with each pointing to a different tier - absolute '
    'confidence, where no doubt is involved, strong confidence, or weak confidence. Classifiers '
    'should give sufficient thought to this question to ensure they are classifying data to the '
    'appropriate sensitivity.')
LIVING_INDIVIDUAL = (
    'A Living individual is an individual for whom you do not have reasonable evidence that they '
    'are deceased. If you’re unsure if the data subject is alive or dead, assume they have a '
    'lifespan of 100 years and act accordingly. If you’re unsure of their age, assume 16 for any '
    'adult and 0 for any child, unless you have contextual evidence that allows you to make a '
    'reasonable assumption otherwise.')


def initial_guidance():
    guidance = [
        {
            'name': 'commercial_data',
            'guidance': COMMERCIAL_DATA,
        },
        {
            'name': 'personal_data',
            'guidance': PERSONAL_DATA,
        },
        {
            'name': 'living_individual',
            'guidance': LIVING_INDIVIDUAL,
        },
        {
            'name': 'pseudonymized_data',
            'guidance': PSEUDONYMIZED_DATA,
        },
    ]
    return guidance


def initial_questions():
    # The order of this list is important, as the database is populated in order
    # Values for 'yes_question' and 'no_question' should always refer to entries earlier in the
    # list
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

def insert_initial_questions(ClassificationQuestion, ClassificationGuidance):
    assert not ClassificationGuidance.objects.exists()
    assert not ClassificationQuestion.objects.exists()

    guidance = {}
    questions = {}

    for kwargs in initial_guidance():
        g = ClassificationGuidance(**kwargs)
        g.full_clean()
        g.save()
        guidance[g.name] = g

    for kwargs in initial_questions():
        if kwargs['yes_question']:
            kwargs['yes_question'] = questions[kwargs['yes_question']]
        if kwargs['no_question']:
            kwargs['no_question'] = questions[kwargs['no_question']]
        q = ClassificationQuestion(**kwargs)
        q.full_clean()
        q.save()
        questions[q.name] = q


def migrate_questions(apps, schema_editor):
    # Template method for use in migrations

    # Add any brand-new guidance
    # insert_blank_guidance_if_necessary(apps, 'guidance2')

    # Update any guidance that need to change (including any new guidance)
    # guidance = {g['name']: g for g in classification.initial_guidance()}
    # migrate_guidance(apps, 'guidance1', guidance['guidance1'])
    # migrate_guidance(apps, 'guidance2', guidance['guidance2'])

    # Hide any no longer used questions
    # hide_question_if_present(apps, 'question1')
    # hide_question_if_present(apps, 'question2')

    # Add any brand-new questions
    # insert_blank_question_if_necessary(apps, 'question8')
    # insert_blank_question_if_necessary(apps, 'question9')

    # Update any questions that need to change (including any new questions)
    # questions = {q['name']: q for q in classification.initial_questions()}
    # migrate_question(apps, 'question1', questions['question1'])
    # migrate_question(apps, 'question2', questions['question2'])
    # migrate_question(apps, 'question8', questions['question8'])
    # migrate_question(apps, 'question9', questions['question9'])

    # Check the database looks as expected
    # verify_initial_questions(apps)
    pass


def verify_initial_questions(apps):
    ClassificationQuestion = apps.get_model('data', 'ClassificationQuestion')
    stored = ClassificationQuestion.objects.filter(hidden=False)
    initial = {q['name']: q for q in initial_questions()}
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

    ClassificationGuidance = apps.get_model('data', 'ClassificationGuidance')
    stored = ClassificationGuidance.objects.filter()
    initial = {g['name']: g for g in initial_guidance()}
    if len(stored) != len(initial):
        raise RuntimeError(f"Expected {len(initial)} guidance but there were {len(stored)}")
    for g in stored:
        g = {
            'name': g.name,
            'guidance': g.guidance,
        }
        g2 = initial[g['name']]

        if g != g2:
            raise RuntimeError(f"Expected {g['name']} to be {g2} but was {g}")


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


def migrate_guidance(apps, name, kwargs):
    ClassificationGuidance = apps.get_model('data', 'ClassificationGuidance')
    g = ClassificationGuidance.objects.get(name=name)
    g.guidance = kwargs['guidance']
    g.save()


def insert_blank_guidance_if_necessary(apps, name):
    ClassificationGuidance = apps.get_model('data', 'ClassificationGuidance')
    g, created = ClassificationGuidance.objects.get_or_create(name=name)
