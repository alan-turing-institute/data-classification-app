from model_bakery.recipe import Recipe, foreign_key


user = Recipe("identity.User")
project = Recipe("Project")
participant = Recipe("Participant")
researcher = participant.extend(role="researcher")
investigator = participant.extend(role="investigator")

dataset = Recipe("Dataset")
work_package = Recipe("WorkPackage")


social_auth = Recipe("UserSocialAuth")


question_set = Recipe("ClassificationQuestionSet", name="qset1")
question = Recipe("ClassificationQuestion", question_set=foreign_key(question_set))
alt_question_set = question_set.extend(name="qset2")
