from model_bakery.recipe import Recipe


user = Recipe('identity.User')
project = Recipe('Project')
participant = Recipe('Participant')
researcher = participant.extend(role='researcher')
investigator = participant.extend(role='investigator')

dataset = Recipe('Dataset')
work_package = Recipe('WorkPackage')


social_auth = Recipe('UserSocialAuth')
