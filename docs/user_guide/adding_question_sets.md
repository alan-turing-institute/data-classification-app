# Alternative data classification question sets
The data classification app comes with a pre-loaded set of questions for classifying work packages known as the turing question set. However, organisations can add their own question sets to the app via the admin interface.

## Adding a new question set

Create a new classification question set container:
1. Login to the admin interface (`https://your.domain.com/admin`)
2. From the Data section of the left hand menu, select the Add button next to classification question sets
3. Enter a name and description, then click save

Add questions to the question set. 

**Note** questions should be added in reverse order as their yes and no question fields need to reference existing questions. 

To add a new question:
1. From the data section of the left hand menu, select the Add button next to classification question
2. Complete the fields as follows:
   
   **name**: a short identifier (must be unique within the question set)
   
   **question set**: choose your newly created question set from the drop down
   
   **question**: the text of the question to be displayed (can include html tags)
   
   **yes question**: the question to show next if the answer is yes (must not also specify yes tier)
   
   **no question**: the question to show next if the answer is no (must not also specify no tier)
   
   **yes tier**: the data classification tier if the answer is yes (must not also specify yes question)
   
   **no tier**: the data classification tier if the answer is no (must not also specify no question)
3. Click save and add the next question

Once all questions have been added, the new question set should be ready to use. When creating a new project, selecting the new question set will result in those questions being used for data classification instead of the default turing questions.

## Changing the default question set
The default question set for projects is the "turing" question set, but this can be changed at deployment time by specifying a new value for `DEFAULT_QUESTION_SET_NAME` in the .env file.

