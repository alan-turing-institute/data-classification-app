import pytest
from django.core.exceptions import ValidationError

from haven.core import recipes
from haven.data.models import ClassificationQuestion, ClassificationQuestionSet

@pytest.mark.django_db
class TestClassificationQuestion:
    def test_add_question_with_mismatched_question_set(self):
        """Test that a ValidationError is raised if someone tries to
        create a question linking to another question with a different
        question set"""
        question2 = recipes.question.make()
        wrong_question_set = recipes.alt_question_set.make()

        question1_data = {
            "name": "question1",
            "question_set": wrong_question_set,
            "yes_question": question2,
            "no_tier": 0
        }
        question1 = ClassificationQuestion.objects.create(**question1_data)

        with pytest.raises(ValidationError) as excinfo:
            question1.clean()

        assert "question cannot be from another question set" in str(excinfo.value)

    def test_add_question_with_yes_tier_and_yes_question(self):
        """Test that a ValidationError is raised with a particular message
        if a question is created with both a yes tier and a yes question"""
        question2 = recipes.question.make()
        question1_data = {
            "name": "question1",
            "question_set": question2.question_set,
            "yes_question": question2,
            "yes_tier": 0
        }
        question1 = ClassificationQuestion.objects.create(**question1_data)
        msg = "Questions must have a yes question or a yes tier, but not both."
        
        with pytest.raises(ValidationError) as excinfo:
            question1.clean()

        assert msg in str(excinfo.value)
