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


COMMERCIAL_DATA = 'commercial_data'
LIVING_INDIVIDUAL = 'living_individual'
PERSONAL_DATA = 'personal_data'
PSEUDONYMIZED_DATA = 'pseudonymized_data'

CLOSED_PERSONAL = 'closed_personal'
FINANCIAL_LOW = 'financial_low'
FINANCIAL_LOW_PERSONAL = 'financial_low_personal'
INCLUDE_COMMERCIAL = 'include_commercial'
INCLUDE_COMMERCIAL_PERSONAL = 'include_commercial_personal'
NO_REIDENTIFY = 'no_reidentify'
NO_REIDENTIFY_ABSOLUTE = 'no_reidentify_absolute'
NO_REIDENTIFY_STRONG = 'no_reidentify_strong'
OPEN_GENERATE_NEW = 'open_generate_new'
OPEN_PUBLICATION = 'open_publication'
PUBLIC_AND_OPEN = 'public_and_open'
PUBLISHABLE = 'publishable'
SOPHISTICATED_ATTACK = 'sophisticated_attack'
SUBSTANTIAL_THREAT = 'substantial_threat'

CLOSED_PERSONAL_TEXT = 'Will any project input be <a href="#personal_data">personal data</a>?'
FINANCIAL_LOW_TEXT = (
    'Do you have high confidence that the commercial, legal, '
    'reputational or political consequences of unauthorised '
    'disclosure of this data will be low?')
FINANCIAL_LOW_PERSONAL_TEXT = (
    'Do you have high confidence that the commercial, legal, '
    'reputational or political consequences of unauthorised '
    'disclosure of this data will be low?')
INCLUDE_COMMERCIAL_TEXT = (
    'Will you be working with <a href="#commercial_data">commercial-in-confidence '
    'information</a> or private third-party intellectual property, '
    'or legally or politically sensitive data?')
INCLUDE_COMMERCIAL_PERSONAL_TEXT = (
    'Will you also be working with <a href="#commercial_data">commercial-in-confidence '
    'information</a> or private third-party intellectual property, '
    'or legally or politically sensitive data?')
NO_REIDENTIFY_TEXT = ('Is that <a href="#personal_data">personal data</a> '
                      '<a href="#pseudonymized_data">pseudonymized</a>?')
NO_REIDENTIFY_ABSOLUTE_TEXT = (
    'Do you have absolute confidence that it is not possible '
    'to identify individuals from the data, either at the '
    'point of entry or as a result of any analysis that may '
    'be carried out?')
NO_REIDENTIFY_STRONG_TEXT = (
    'Do you have strong confidence that it is not possible to '
    'identify individuals from the data, either at the point of '
    'entry or as a result of any analysis that may be carried '
    'out?')
OPEN_GENERATE_NEW_TEXT = (
    'Will the research generate (including by selecting, or '
    'sorting or combining) any <a href="#personal_data">personal data</a>?')
OPEN_PUBLICATION_TEXT = (
    'Will releasing any of the datasets or results impact on '
    'the competitive advantage of the research team?')
PUBLIC_AND_OPEN_TEXT = (
    'Is that <a href="#personal_data">personal data</a> legally accessible by the general '
    'public with no restrictions on use?')
PUBLISHABLE_TEXT = (
    'Do you have high confidence that the commercial, legal, '
    'reputational or political consequences of unauthorised '
    'disclosure of this data will be so low as to be trivial?')
SOPHISTICATED_ATTACK_TEXT = (
    'Do likely attackers include sophisticated, '
    'well-resourced and determined threats, such as highly '
    'capable serious organised crime groups and state '
    'actors?')
SUBSTANTIAL_THREAT_TEXT = (
    'Would disclosure pose a substantial threat to the '
    'personal safety, health or security of the data '
    'subjects?')


COMMERCIAL_DATA_TEXT = (
    '<p><strong>Commercial-in-confidence data</strong> is information which, if disclosed, may '
    'result in damage to a '
    'party’s commercial interest, intellectual property, or trade secrets.</p>')
PERSONAL_DATA_TEXT = (
    '<p><strong>Personal data</strong> is any information relating to an identified or '
    'identifiable <a href="#living_individual">living individual</a>; an \'identifiable\' living '
    'individual is one who can be identified, directly '
    'or indirectly, in particular by reference to an identifier such as a name, an '
    'identification number, location data, an online identifier or to one or more factors '
    'specific to the physical, physiological, genetic, mental, economic, cultural or social '
    'identity of that natural person.</p>'
    '<p>The term \'indirectly\' here indicates that this includes '
    'data where identification is made possible by combining one or more sets of data, including '
    'synthetic data or trained models.</p>')
PSEUDONYMIZED_DATA_TEXT = (
    '<p><strong>Pseudonymised data</strong> is personal data that has been processed in such a '
    'manner that it can '
    'no longer be attributed to a specific living individual without the use of additional '
    'information, which is kept separately and subject to technical and organisational measures '
    'that ensure that the personal data are not attributed to an identified or identifiable '
    'living individual.</p>'
    '<p>Two important things to note are that pseudonymised data:'
    '<ul><li> is still '
    'personal data - it becomes anonymised data, and is no longer personal data, only if '
    '<em>both</em> the key data connecting pseudonyms to real numbers is securely destroyed, '
    '<em>and</em> no other data '
    'exists in the world which could be used statistically to re-identify individuals from the '
    'data</li> <li>depending on the method used, it normally includes synthetic data and models '
    'that '
    'have been trained on personal data. Expert review is needed to determine the degree to which '
    'such datasets could allow individuals to be identified.</li></ul>'
    '<p> It is important that both '
    'researchers and Dataset Providers consider the level of confidence they have in the '
    'likelihood of identifying individuals from data. Anonymised data is data which under no '
    'circumstances can be used to identify an individual, and this is less common than many '
    'realise (<a href="https://doi.org/10.1038/s41467-019-10933-3">Rocher et al., 2019</a>).</p>'
    '<p>Our model specifies three levels of confidence that classifiers can have about '
    'the likelihood of reidentification, with each pointing to a different tier - absolute '
    'confidence, where no doubt is involved, strong confidence, or weak confidence. Classifiers '
    'should give sufficient thought to this question to ensure they are classifying data to the '
    'appropriate sensitivity.</p>')
LIVING_INDIVIDUAL_TEXT = (
    '<p>A <strong>living individual</strong> is an individual for whom you do not have reasonable '
    'evidence that they '
    'are deceased. If you’re unsure if the data subject is alive or dead, assume they have a '
    'lifespan of 100 years and act accordingly. If you’re unsure of their age, assume 16 for any '
    'adult and 0 for any child, unless you have contextual evidence that allows you to make a '
    'reasonable assumption otherwise '
    '(<a href="https://www.nationalarchives.gov.uk/documents/information-management/'
    'guide-to-archiving-personal-data.pdf">National Archives, 2018</a>).</p>')


def initial_guidance():
    guidance = [
        {
            'name': COMMERCIAL_DATA,
            'guidance': COMMERCIAL_DATA_TEXT,
        },
        {
            'name': PERSONAL_DATA,
            'guidance': PERSONAL_DATA_TEXT,
        },
        {
            'name': LIVING_INDIVIDUAL,
            'guidance': LIVING_INDIVIDUAL_TEXT,
        },
        {
            'name': PSEUDONYMIZED_DATA,
            'guidance': PSEUDONYMIZED_DATA_TEXT,
        },
    ]
    return guidance


def initial_questions():
    # The order of this list is important, as the database is populated in order
    # Values for 'yes_question' and 'no_question' should always refer to entries earlier in the
    # list
    questions = [
        {
            'name': SOPHISTICATED_ATTACK,
            'question': SOPHISTICATED_ATTACK_TEXT,
            'yes_tier': Tier.FOUR,
            'no_tier': Tier.THREE,
        },
        {
            'name': FINANCIAL_LOW_PERSONAL,
            'question': FINANCIAL_LOW_PERSONAL_TEXT,
            'yes_tier': Tier.TWO,
            'no_question': SOPHISTICATED_ATTACK,
        },
        {
            'name': INCLUDE_COMMERCIAL_PERSONAL,
            'question': INCLUDE_COMMERCIAL_PERSONAL_TEXT,
            'yes_question': FINANCIAL_LOW_PERSONAL,
            'no_tier': Tier.TWO,
        },
        {
            'name': NO_REIDENTIFY_STRONG,
            'question': NO_REIDENTIFY_STRONG_TEXT,
            'yes_question': INCLUDE_COMMERCIAL_PERSONAL,
            'no_question': SOPHISTICATED_ATTACK,
        },
        {
            'name': PUBLISHABLE,
            'question': PUBLISHABLE_TEXT,
            'yes_tier': Tier.ONE,
            'no_tier': Tier.TWO,
        },
        {
            'name': FINANCIAL_LOW,
            'question': FINANCIAL_LOW_TEXT,
            'yes_question': PUBLISHABLE,
            'no_question': SOPHISTICATED_ATTACK,
        },
        {
            'name': SUBSTANTIAL_THREAT,
            'question': SUBSTANTIAL_THREAT_TEXT,
            'yes_tier': Tier.FOUR,
            'no_tier': Tier.THREE,
        },
        {
            'name': OPEN_PUBLICATION,
            'question': OPEN_PUBLICATION_TEXT,
            'yes_tier': Tier.ONE,
            'no_tier': Tier.ZERO,
        },
        {
            'name': INCLUDE_COMMERCIAL,
            'question': INCLUDE_COMMERCIAL_TEXT,
            'yes_question': FINANCIAL_LOW,
            'no_question': OPEN_PUBLICATION,
        },
        {
            'name': NO_REIDENTIFY_ABSOLUTE,
            'question': NO_REIDENTIFY_ABSOLUTE_TEXT,
            'yes_question': INCLUDE_COMMERCIAL,
            'no_question': NO_REIDENTIFY_STRONG,
        },
        {
            'name': NO_REIDENTIFY,
            'question': NO_REIDENTIFY_TEXT,
            'yes_question': NO_REIDENTIFY_ABSOLUTE,
            'no_question': SUBSTANTIAL_THREAT,
        },
        {
            'name': PUBLIC_AND_OPEN,
            'question': PUBLIC_AND_OPEN_TEXT,
            'yes_question': INCLUDE_COMMERCIAL,
            'no_question': NO_REIDENTIFY,
        },
        {
            'name': CLOSED_PERSONAL,
            'question': CLOSED_PERSONAL_TEXT,
            'yes_question': PUBLIC_AND_OPEN,
            'no_question': INCLUDE_COMMERCIAL,
        },
        {
            'name': OPEN_GENERATE_NEW,
            'question': OPEN_GENERATE_NEW_TEXT,
            'yes_question': SUBSTANTIAL_THREAT,
            'no_question': CLOSED_PERSONAL,
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
    # insert_blank_guidance_if_necessary(apps, GUIDANCE2)

    # Update any guidance that need to change (including any new guidance)
    # guidance = {g['name']: g for g in initial_guidance()}
    # migrate_guidance(apps, GUIDANCE1, guidance[GUIDANCE1])
    # migrate_guidance(apps, GUIDANCE2, guidance[GUIDANCE2])

    # Hide any no longer used questions
    # hide_question_if_present(apps, QUESTION1)
    # hide_question_if_present(apps, QUESTION2)

    # Add any brand-new questions
    # insert_blank_question_if_necessary(apps, QUESTION8)
    # insert_blank_question_if_necessary(apps, QUESTION9)

    # Update any questions that need to change (including any new questions)
    # questions = {q['name']: q for q in initial_questions()}
    # migrate_question(apps, QUESTION1, questions[QUESTION1])
    # migrate_question(apps, QUESTION2, questions[QUESTION2])
    # migrate_question(apps, QUESTION8, questions[QUESTION8])
    # migrate_question(apps, QUESTION9, questions[QUESTION9])

    # Check the database looks as expected
    verify_initial_questions(apps)


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
