from django.core.exceptions import ObjectDoesNotExist
from simple_history.manager import HistoryManager
from simple_history.models import HistoricalRecords

from haven.data.tiers import Tier


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
# * Run `manage.py makemigrations --empty data`
# * Copy the contents of this module into the migration
# * Add `migrations.RunPython(migrate_questions)` into the list of operations
# * Update the migrate_questions method accordingly
# * Run and test the migration
#
# For more complicated changes, you may need to adapt these instructions.
#
# If you've had to change the schema
# * Run `manage.py makemigrations` before creating your empty migration (so that you have
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
# * Fake rollback of the migration: `manage.py migrate --fake data <previous_migration_name>`
# * Rerun your migration
# * This process is convoluted, but is designed to ensure you don't make a change only in the
#   migration, and not this module, which would cause problems next time we try to write another
#   migration


COMMERCIAL_DATA = "commercial_data"
LIVING_INDIVIDUAL = "living_individual"
PERSONAL_DATA = "personal_data"
PSEUDONYMIZED_DATA = "pseudonymized_data"

CLOSED_PERSONAL = "closed_personal"
FINANCIAL_LOW = "financial_low"
FINANCIAL_LOW_PERSONAL = "financial_low_personal"
INCLUDE_COMMERCIAL = "include_commercial"
INCLUDE_COMMERCIAL_PERSONAL = "include_commercial_personal"
NO_REIDENTIFY = "no_reidentify"
NO_REIDENTIFY_ABSOLUTE = "no_reidentify_absolute"
NO_REIDENTIFY_STRONG = "no_reidentify_strong"
OPEN_GENERATE_NEW = "open_generate_new"
OPEN_PUBLICATION = "open_publication"
PUBLIC_AND_OPEN = "public_and_open"
PUBLISHABLE = "publishable"
SOPHISTICATED_ATTACK = "sophisticated_attack"
SUBSTANTIAL_THREAT = "substantial_threat"

CLOSED_PERSONAL_TEXT = (
    'Will any project input be <a href="#personal_data">personal data</a>?'
)
FINANCIAL_LOW_TEXT = (
    "Do you have high confidence that the commercial, legal, "
    "reputational or political consequences of unauthorised "
    "disclosure of this data will be low?"
)
FINANCIAL_LOW_PERSONAL_TEXT = (
    "Do you have high confidence that the commercial, legal, "
    "reputational or political consequences of unauthorised "
    "disclosure of this data will be low?"
)
INCLUDE_COMMERCIAL_TEXT = (
    'Will you be working with <a href="#commercial_data">commercial-in-confidence '
    "information</a> or private third-party intellectual property, "
    "or legally or politically sensitive data?"
)
INCLUDE_COMMERCIAL_PERSONAL_TEXT = (
    'Will you also be working with <a href="#commercial_data">commercial-in-confidence '
    "information</a> or private third-party intellectual property, "
    "or legally or politically sensitive data?"
)
NO_REIDENTIFY_TEXT = (
    'Is that <a href="#personal_data">personal data</a> '
    '<a href="#pseudonymized_data">pseudonymized</a>?'
)
NO_REIDENTIFY_ABSOLUTE_TEXT = (
    "Do you have absolute confidence that it is not possible "
    "to identify individuals from the data, either at the "
    "point of entry or as a result of any analysis that may "
    "be carried out?"
)
NO_REIDENTIFY_STRONG_TEXT = (
    "Do you have strong confidence that it is not possible to "
    "identify individuals from the data, either at the point of "
    "entry or as a result of any analysis that may be carried "
    "out?"
)
OPEN_GENERATE_NEW_TEXT = (
    "Will the research generate (including by selecting, or "
    'sorting or combining) any <a href="#personal_data">personal data</a>?'
)
OPEN_PUBLICATION_TEXT = (
    "Will releasing any of the datasets or results impact on "
    "the competitive advantage of the research team?"
)
PUBLIC_AND_OPEN_TEXT = (
    'Is that <a href="#personal_data">personal data</a> legally accessible by the general '
    "public with no restrictions on use?"
)
PUBLISHABLE_TEXT = (
    "Do you have high confidence that the commercial, legal, "
    "reputational or political consequences of unauthorised "
    "disclosure of this data will be so low as to be trivial?"
)
SOPHISTICATED_ATTACK_TEXT = (
    "Do likely attackers include sophisticated, "
    "well-resourced and determined threats, such as highly "
    "capable serious organised crime groups and state "
    "actors?"
)
SUBSTANTIAL_THREAT_TEXT = (
    "Would disclosure pose a substantial threat to the "
    "personal safety, health or security of the data "
    "subjects?"
)


COMMERCIAL_DATA_TEXT = (
    "<p><strong>Commercial-in-confidence data</strong> is information which, if disclosed, may "
    "result in damage to a "
    "party’s commercial interest, intellectual property, or trade secrets.</p>"
)
PERSONAL_DATA_TEXT = (
    "<p><strong>Personal data</strong> is any information relating to an identified or "
    "identifiable <a href=\"#living_individual\">living individual</a>; an 'identifiable' living "
    "individual is one who can be identified, directly "
    "or indirectly, in particular by reference to an identifier such as a name, an "
    "identification number, location data, an online identifier or to one or more factors "
    "specific to the physical, physiological, genetic, mental, economic, cultural or social "
    "identity of that natural person.</p>"
    "<p>The term 'indirectly' here indicates that this includes "
    "data where identification is made possible by combining one or more sets of data, including "
    "synthetic data or trained models.</p>"
)
PSEUDONYMIZED_DATA_TEXT = (
    "<p><strong>Pseudonymised data</strong> is personal data that has been processed in such a "
    "manner that it can "
    "no longer be attributed to a specific living individual without the use of additional "
    "information, which is kept separately and subject to technical and organisational measures "
    "that ensure that the personal data are not attributed to an identified or identifiable "
    "living individual.</p>"
    "<p>Two important things to note are that pseudonymised data:"
    "<ul><li> is still "
    "personal data - it becomes anonymised data, and is no longer personal data, only if "
    "<em>both</em> the key data connecting pseudonyms to real numbers is securely destroyed, "
    "<em>and</em> no other data "
    "exists in the world which could be used statistically to re-identify individuals from the "
    "data</li> <li>depending on the method used, it normally includes synthetic data and models "
    "that "
    "have been trained on personal data. Expert review is needed to determine the degree to which "
    "such datasets could allow individuals to be identified.</li></ul>"
    "<p> It is important that both "
    "researchers and Dataset Providers consider the level of confidence they have in the "
    "likelihood of identifying individuals from data. Anonymised data is data which under no "
    "circumstances can be used to identify an individual, and this is less common than many "
    'realise (<a href="https://doi.org/10.1038/s41467-019-10933-3">Rocher et al., 2019</a>).</p>'
    "<p>Our model specifies three levels of confidence that classifiers can have about "
    "the likelihood of reidentification, with each pointing to a different tier - absolute "
    "confidence, where no doubt is involved, strong confidence, or weak confidence. Classifiers "
    "should give sufficient thought to this question to ensure they are classifying data to the "
    "appropriate sensitivity.</p>"
)
LIVING_INDIVIDUAL_TEXT = (
    "<p>A <strong>living individual</strong> is an individual for whom you do not have reasonable "
    "evidence that they "
    "are deceased. If you’re unsure if the data subject is alive or dead, assume they have a "
    "lifespan of 100 years and act accordingly. If you’re unsure of their age, assume 16 for any "
    "adult and 0 for any child, unless you have contextual evidence that allows you to make a "
    "reasonable assumption otherwise "
    '(<a href="https://www.nationalarchives.gov.uk/documents/information-management/'
    'guide-to-archiving-personal-data.pdf">National Archives, 2018</a>).</p>'
)


CLOSED_PERSONAL_GUIDANCE_TEXT = (
    "<p>Will you be using any personal data at all throughout the research, even if it's publicly "
    "available? For example:</p><ul><li>Personal data such as newspaper articles on celebrities, "
    "or details of patients in a medical trial</li><li>Facebook or twitter posts</li></ul>"
)
FINANCIAL_LOW_GUIDANCE_TEXT = (
    "<p>Is there <strong>no risk</strong> that the reputation of the researcher or data provider "
    "will be damaged "
    "by this data being made public, or that legal action can be taken as a result? For example:"
    "</p><ul><li>Financial reports that an organisation sells to businesses for commercial "
    "profit</li><li>Anonymised non-controversial user research</li></ul>"
)
FINANCIAL_LOW_PERSONAL_GUIDANCE_TEXT = (
    "<p>Is there <strong>no risk</strong> that the reputation of the researcher or data provider "
    "will be damaged "
    "by this data being made public, or that legal action can be taken as a result? For example:"
    "</p><ul><li>Financial reports that an organisation sells to businesses for commercial "
    "profit</li><li>Anonymised non-controversial user research</li></ul>"
)
INCLUDE_COMMERCIAL_GUIDANCE_TEXT = (
    "<p>This is any information that the data provider would not be comfortable with you "
    "publishing, including purchased or requested data. For example:</p><ul><li>Pay to view news "
    "articles are private third-party intellectual property</li><li>Plans for marketing "
    "campaigns, or purchasing strategies, for companies, are commercial in-confidence data</li>"
    "</ul>"
)
INCLUDE_COMMERCIAL_PERSONAL_GUIDANCE_TEXT = (
    "<p>This is any information that the data provider would not be comfortable with you "
    "publishing, including purchased or requested data. For example:</p><ul><li>Pay to view news "
    "articles are private third-party intellectual property </li><li>Plans for marketing "
    "campaigns, or purchasing strategies, for companies, are commercial in-confidence data</li>"
    "</ul>"
)
NO_REIDENTIFY_GUIDANCE_TEXT = (
    "<p>Have steps been taken so that information can no longer be directly linked to a particular "
    "individual, without additional information? For example:</p><ul><li>Replacing names of "
    "patients with patient ID numbers</li><li>Customer records with all name and address details "
    "removed</li></ul>"
)
NO_REIDENTIFY_ABSOLUTE_GUIDANCE_TEXT = (
    "<p>Any data pseudonymised to this degree cannot be connected back to individuals through "
    "analysis, even in combination with other datasets. For example:</p><ul><li>Research results "
    "with generated fake names, where the pseudonymisation key is deleted, never to be used again "
    "</li><li>Anonymous responses to a public survey without any identifying information</li></ul>"
)
NO_REIDENTIFY_STRONG_GUIDANCE_TEXT = (
    "<p>Any data pseudonymised to this degree cannot be connected with individuals, unless "
    "combined with data not publicly available, <strong>or</strong> the effort required to "
    "de-pseudonymise would be "
    "too high to be feasible for a person acting on their own. For example:</p><ul><li>Medical "
    "test results with generated fake names, where only the pseudonymisation key be used to "
    "identify the patients in this one study</li><li>Anonymous responses to a public survey, "
    "where questions may lead to identifying information in combination with purchasable IP "
    "address data</li></ul>"
)
OPEN_GENERATE_NEW_GUIDANCE_TEXT = (
    "<p>Generating personal data means creating any <strong>new</strong> personal data, regardless "
    "of what data "
    "you're starting with. For example:</p><ul><li>Linking diseases to particular patients</li>"
    "<li>Spotting trends in tweets mentioning a particular individual</li></ul>"
)
OPEN_PUBLICATION_GUIDANCE_TEXT = (
    "<p>This includes data that may be planned for publication in the future, or could be "
    "published without any issue, but is not yet publicly available. For example:</p><ul><li>"
    "Results from a study, that a research team hopes to submit to Nature.</li><li>Visualisations "
    "of existing publicly available data</li></ul>"
)
PUBLIC_AND_OPEN_GUIDANCE_TEXT = (
    "<p>Data is legally accessible if it is <strong>not</strong> behind a paywall, can be accessed "
    "without having "
    "to request it, and has <strong>no</strong> conditions on its use. For example:</p><ul><li>"
    "Voter registration "
    "records are <strong>not</strong> available, as they have restrictions on access and use</li>"
    "<li>Academic "
    "articles that are not open source require subscription to a journal, or a request for access "
    "from the author, are <strong>not</strong> legally accessible</li></ul>"
)
PUBLISHABLE_GUIDANCE_TEXT = (
    "<p>Would the data providers be prepared to release their data (accidentally or deliberately)? "
    "For example:</p><ul><li>Results that a data provider has indicated they are happy to go into "
    "a research publication</li><li>Fully anonymised data on trends not linked to a company or "
    "commercial interests</li></ul>"
)
SOPHISTICATED_ATTACK_GUIDANCE_TEXT = (
    "<p>Could this data be used to blackmail, target or persecute individuals? For example:</p> "
    "<ul><li>Linking location data to members of a controversial group</li><li>Information on the "
    "sexuality of individuals in a region where this may lead to arrest or abuse</li></ul>"
)
SUBSTANTIAL_THREAT_GUIDANCE_TEXT = (
    "<p>Could this data be used to blackmail, target or persecute individuals? Is it likely that "
    "motivated teams might try to access this data illegally? For example:</p><ul><li>Linking "
    "location data to members of a controversial group</li><li>Information on the sexuality of "
    "individuals in a region where this may lead to arrest or abuse</li></ul>"
)


def initial_guidance():
    guidance = [
        {
            "name": COMMERCIAL_DATA,
            "guidance": COMMERCIAL_DATA_TEXT,
        },
        {
            "name": PERSONAL_DATA,
            "guidance": PERSONAL_DATA_TEXT,
        },
        {
            "name": LIVING_INDIVIDUAL,
            "guidance": LIVING_INDIVIDUAL_TEXT,
        },
        {
            "name": PSEUDONYMIZED_DATA,
            "guidance": PSEUDONYMIZED_DATA_TEXT,
        },
        {
            "name": CLOSED_PERSONAL,
            "guidance": CLOSED_PERSONAL_GUIDANCE_TEXT,
        },
        {
            "name": FINANCIAL_LOW,
            "guidance": FINANCIAL_LOW_GUIDANCE_TEXT,
        },
        {
            "name": FINANCIAL_LOW_PERSONAL,
            "guidance": FINANCIAL_LOW_PERSONAL_GUIDANCE_TEXT,
        },
        {
            "name": INCLUDE_COMMERCIAL,
            "guidance": INCLUDE_COMMERCIAL_GUIDANCE_TEXT,
        },
        {
            "name": INCLUDE_COMMERCIAL_PERSONAL,
            "guidance": INCLUDE_COMMERCIAL_PERSONAL_GUIDANCE_TEXT,
        },
        {
            "name": NO_REIDENTIFY,
            "guidance": NO_REIDENTIFY_GUIDANCE_TEXT,
        },
        {
            "name": NO_REIDENTIFY_ABSOLUTE,
            "guidance": NO_REIDENTIFY_ABSOLUTE_GUIDANCE_TEXT,
        },
        {
            "name": NO_REIDENTIFY_STRONG,
            "guidance": NO_REIDENTIFY_STRONG_GUIDANCE_TEXT,
        },
        {
            "name": OPEN_GENERATE_NEW,
            "guidance": OPEN_GENERATE_NEW_GUIDANCE_TEXT,
        },
        {
            "name": OPEN_PUBLICATION,
            "guidance": OPEN_PUBLICATION_GUIDANCE_TEXT,
        },
        {
            "name": PUBLIC_AND_OPEN,
            "guidance": PUBLIC_AND_OPEN_GUIDANCE_TEXT,
        },
        {
            "name": PUBLISHABLE,
            "guidance": PUBLISHABLE_GUIDANCE_TEXT,
        },
        {
            "name": SOPHISTICATED_ATTACK,
            "guidance": SOPHISTICATED_ATTACK_GUIDANCE_TEXT,
        },
        {
            "name": SUBSTANTIAL_THREAT,
            "guidance": SUBSTANTIAL_THREAT_GUIDANCE_TEXT,
        },
    ]
    return guidance


def initial_questions():
    # The order of this list is important, as the database is populated in order
    # Values for 'yes_question' and 'no_question' should always refer to entries earlier in the
    # list
    questions = [
        {
            "name": SOPHISTICATED_ATTACK,
            "question": SOPHISTICATED_ATTACK_TEXT,
            "yes_tier": Tier.FOUR,
            "no_tier": Tier.THREE,
        },
        {
            "name": FINANCIAL_LOW_PERSONAL,
            "question": FINANCIAL_LOW_PERSONAL_TEXT,
            "yes_tier": Tier.TWO,
            "no_question": SOPHISTICATED_ATTACK,
        },
        {
            "name": INCLUDE_COMMERCIAL_PERSONAL,
            "question": INCLUDE_COMMERCIAL_PERSONAL_TEXT,
            "yes_question": FINANCIAL_LOW_PERSONAL,
            "no_tier": Tier.TWO,
        },
        {
            "name": NO_REIDENTIFY_STRONG,
            "question": NO_REIDENTIFY_STRONG_TEXT,
            "yes_question": INCLUDE_COMMERCIAL_PERSONAL,
            "no_question": SOPHISTICATED_ATTACK,
        },
        {
            "name": PUBLISHABLE,
            "question": PUBLISHABLE_TEXT,
            "yes_tier": Tier.ONE,
            "no_tier": Tier.TWO,
        },
        {
            "name": FINANCIAL_LOW,
            "question": FINANCIAL_LOW_TEXT,
            "yes_question": PUBLISHABLE,
            "no_question": SOPHISTICATED_ATTACK,
        },
        {
            "name": SUBSTANTIAL_THREAT,
            "question": SUBSTANTIAL_THREAT_TEXT,
            "yes_tier": Tier.FOUR,
            "no_tier": Tier.THREE,
        },
        {
            "name": OPEN_PUBLICATION,
            "question": OPEN_PUBLICATION_TEXT,
            "yes_tier": Tier.ONE,
            "no_tier": Tier.ZERO,
        },
        {
            "name": INCLUDE_COMMERCIAL,
            "question": INCLUDE_COMMERCIAL_TEXT,
            "yes_question": FINANCIAL_LOW,
            "no_question": OPEN_PUBLICATION,
        },
        {
            "name": NO_REIDENTIFY_ABSOLUTE,
            "question": NO_REIDENTIFY_ABSOLUTE_TEXT,
            "yes_question": INCLUDE_COMMERCIAL,
            "no_question": NO_REIDENTIFY_STRONG,
        },
        {
            "name": NO_REIDENTIFY,
            "question": NO_REIDENTIFY_TEXT,
            "yes_question": NO_REIDENTIFY_ABSOLUTE,
            "no_question": SUBSTANTIAL_THREAT,
        },
        {
            "name": PUBLIC_AND_OPEN,
            "question": PUBLIC_AND_OPEN_TEXT,
            "yes_question": INCLUDE_COMMERCIAL,
            "no_question": NO_REIDENTIFY,
        },
        {
            "name": CLOSED_PERSONAL,
            "question": CLOSED_PERSONAL_TEXT,
            "yes_question": PUBLIC_AND_OPEN,
            "no_question": INCLUDE_COMMERCIAL,
        },
        {
            "name": OPEN_GENERATE_NEW,
            "question": OPEN_GENERATE_NEW_TEXT,
            "yes_question": SUBSTANTIAL_THREAT,
            "no_question": CLOSED_PERSONAL,
        },
    ]

    for q in questions:
        q.setdefault("yes_question", None)
        q.setdefault("no_question", None)
        q.setdefault("yes_tier", None)
        q.setdefault("no_tier", None)

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
        if kwargs["yes_question"]:
            kwargs["yes_question"] = questions[kwargs["yes_question"]]
        if kwargs["no_question"]:
            kwargs["no_question"] = questions[kwargs["no_question"]]
        q = ClassificationQuestion(**kwargs)
        q.full_clean()
        q.save()
        questions[q.name] = q


def migrate_questions(apps, schema_editor):
    # Template method for use in migrations
    # You should add/remove calls to insert_*/migrate_*/hide_* functions as appropriate,
    # using the constants defined at the start of this module e.g. COMMERCIAL_DATA,
    # CLOSED_PERSONAL etc.

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
    ClassificationQuestion = apps.get_model("data", "ClassificationQuestion")
    stored = ClassificationQuestion.objects.filter(hidden=False)
    initial = {q["name"]: q for q in initial_questions()}
    if len(stored) != len(initial):
        raise RuntimeError(
            f"Expected {len(initial)} questions but there were {len(stored)}"
        )
    for q in stored:
        q = {
            "name": q.name,
            "question": q.question,
            "yes_question": q.yes_question,
            "no_question": q.no_question,
            "yes_tier": q.yes_tier,
            "no_tier": q.no_tier,
        }
        if q["yes_question"]:
            q["yes_question"] = q["yes_question"].name
        if q["no_question"]:
            q["no_question"] = q["no_question"].name
        q2 = initial[q["name"]]

        if q != q2:
            raise RuntimeError(f"Expected {q['name']} to be {q2} but was {q}")

    ClassificationGuidance = apps.get_model("data", "ClassificationGuidance")
    stored = ClassificationGuidance.objects.filter()
    initial = {g["name"]: g for g in initial_guidance()}
    if len(stored) != len(initial):
        raise RuntimeError(
            f"Expected {len(initial)} guidance but there were {len(stored)}"
        )
    for g in stored:
        g = {
            "name": g.name,
            "guidance": g.guidance,
        }
        g2 = initial[g["name"]]

        if g != g2:
            raise RuntimeError(f"Expected {g['name']} to be {g2} but was {g}")


def migrate_question(apps, name, kwargs):
    ClassificationQuestion = apps.get_model("data", "ClassificationQuestion")
    q = ClassificationQuestion.objects.get(name=name)
    if kwargs["yes_question"]:
        kwargs["yes_question"] = ClassificationQuestion.objects.get(
            name=kwargs["yes_question"]
        )
    if kwargs["no_question"]:
        kwargs["no_question"] = ClassificationQuestion.objects.get(
            name=kwargs["no_question"]
        )
    q.question = kwargs["question"]
    q.yes_question = kwargs["yes_question"]
    q.no_question = kwargs["no_question"]
    q.yes_tier = kwargs["yes_tier"]
    q.no_tier = kwargs["no_tier"]
    q.save()
    history = _attach_history(apps, q)
    history.post_save(q, created=False)


def insert_blank_question_if_necessary(apps, name):
    ClassificationQuestion = apps.get_model("data", "ClassificationQuestion")
    q, created = ClassificationQuestion.objects.get_or_create(name=name)
    if created:
        history = _attach_history(apps, q)
        history.post_save(q, created=True)


def hide_question_if_present(apps, name):
    ClassificationQuestion = apps.get_model("data", "ClassificationQuestion")
    try:
        q = ClassificationQuestion.objects.get(name=name)
        q.hidden = True
        q.save()
        history = _attach_history(apps, q)
        history.post_save(q, created=False)
    except ObjectDoesNotExist:
        pass


def _attach_history(apps, q):
    ClassificationQuestion = apps.get_model("data", "ClassificationQuestion")
    HistoricalClassificationQuestion = apps.get_model(
        "data", "HistoricalClassificationQuestion"
    )
    manager = HistoryManager(HistoricalClassificationQuestion)
    q.history = manager
    history = HistoricalRecords()
    history.manager_name = "history"
    history.cls = ClassificationQuestion.__class__
    return history


def migrate_guidance(apps, name, kwargs):
    ClassificationGuidance = apps.get_model("data", "ClassificationGuidance")
    g = ClassificationGuidance.objects.get(name=name)
    g.guidance = kwargs["guidance"]
    g.save()


def insert_blank_guidance_if_necessary(apps, name):
    ClassificationGuidance = apps.get_model("data", "ClassificationGuidance")
    g, created = ClassificationGuidance.objects.get_or_create(name=name)
