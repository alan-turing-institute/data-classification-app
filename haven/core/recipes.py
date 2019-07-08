from model_mommy.recipe import Recipe


project = Recipe('Project')
participant = Recipe('Participant')
researcher = participant.extend(role='researcher')
investigator = participant.extend(role='investigator')

dataset = Recipe('Dataset')
work_package = Recipe('WorkPackage')


social_auth = Recipe('UserSocialAuth')
