<Note, will be a subpage of <https://www.turing.ac.uk/research/research-projects/data-safe-havens-cloud>>

# Information Governance Collaboration Project Webpage

## Project title

(Aim for 6 words or fewer. A clear description of the project, can be different to official academic
name of the project, please avoid acronyms/initialisms) *

App-based Information Governance for Trustworthy Research Environments

## Organisers

**Project leader 1**
James Hetherington

**Organisation/University affiliation 1** UCL Advanced Research Computing

**Project leader 2** Martin O'Reilly

**Organisation/University affiliation 2** The Alan Turing Institute

**Project leader 3** Kirstie Whitaker

**Organisation/University affiliation 3** The Alan Turing Institute

**Project leader 4** Paul Calleja

**Organisation/University affiliation 4** University of Cambridge

## Details

### Project page main contact

**Contact name** Arielle Bennett
**Contact email address** abennett@turing.ac.uk

**Project start date**
01/01/2022
**Project end date**
30/06/2022

## Page content

### 1 sentence summary/sub-heading

(1 sentence, present tense, e.g. Using…, Developing…, Investigating…)

Delivering an open source "information governance system in a box" to support data protection in trustworthy research environments.

### Brief description

(Clear, concise, ~3 sentences – e.g. 1st sentence: the problem being addressed, 2nd sentence: the potential solution/method, 3rd sentence: applications, output) *

How can researchers be confident that a trustworthy research environment is configured with the right level of protections for the data analysed within it, in line with data protection standards?
Developed alongside the Turing's Data Safe Haven, the purpose of the Turing’s information governance app is to bring stakeholders with diverse perspectives on data protection - investigators, data protection experts, and other researchers - to assess datasets and arrive at a sensitivity classification for the data and the technical recommendations for the protections needed.
This project is looking to make the app implementable at other institutions and organisations as an open source tool.

### Aims/expected outcomes

(What is the work hoping to achieve? What would define success? Why is this work worth doing?)
100-300 words *

This project is building towards an open-source version of the Turing Information Governance app that can be deployed by other research organisations to support their data management and trustworthy research environment infrastructure.
We're preparing this release through a combination of technical work, user testing, and a deep understanding of the existing information governance processes and needs at different institutions.
It also aims to provide a record of decision-making around information governance and data protection to comply with audit requirements.
In the first phase, funded by Turing 2.0, the project team are seeking to set up the potential deployment of the app across the Turing, UCL, and Cambridge.

### Explaining the science

(Is there theory or methods that would be good to explain to understand the project’s work better? Use plain English where possible)
100-300 words *

The app aims to keep a record of datasets used throughout the entire lifecycle of a research project, from data collection (ingress) through to publication or destruction (egress).
Projects are split into multiple work packages, each with their own participants and datasets, and these work packages can be categorised as belonging to one of five tiers (numbered from 0 to 4) according to the sensitivity of the data being processed.
To classify the data, two people independently answer a series of questions about the nature of the data and the potential risks, which results in the work package being given one of the five data classification tiers.
If the answers provided by each person do not agree with one another, a third person can be invited to act as a referee.

The app is built using Django, a python web development framework, Docker which allows for containerisation and automated deployment, Authelia, which enables single-sign on features, CSS and JavaScript libraries including Bootstrap.

### Real world applications

(Where is this work being applied, what area/industry could it benefit?)
100-300 words *

There are growing numbers of trustworthy research environments being deployed across academia and other research intensive fields to offer increased data security and comply with data protection legislation.
One major growth area for this type of digital infrastructure is the NHS, where secure environments to analyse data in reproducible ways are urgently needed, as highlighted in the recent Goldacre review ["Better, broader, safer: using health data for research and analysis"](https://www.gov.uk/government/publications/better-broader-safer-using-health-data-for-research-and-analysis).
However, deciding what level of protection a particular dataset needs is not always straightforward, since it depends on the type of data, how it has been processed, and how it will be used in the analysis.
Typically, assessing these aspects of datasets requires a form or meeting, which can often feel unconnected to the rest of the research process.
The process can also vary between departments and institutions, making it difficult to come to a consensus on how trustworthy research environments should be configured for interdisciplinary projects.

### Recent updates

(Achievements/project milestones reached since project started, with month/year)
March 2022 - Becky Ossleton presented at the [UKRI Cloud Workshop](https://cloud.ac.uk/2022/02/27/programme-for-ukri-cloud-workshop-2022/7), titled "Data Safe Haven Classification and Trusted environments in the cloud: extending a Turing Django based application across multiple institutions"

#### Are there likely to be any sensitivities within or around this project? (For example it deals with highly sensitive subject matter such as abuse, violence, grief, etc)

No, there aren't any sensitivities

### Participating researchers

(Please include titles and affiliations for all participants)

* Oz Parchment (University of Cambridge)
* Paul Browne (University of Cambridge)
* Jonathan Steel (University of Cambridge)
* Nels Swanepoel (UCL)
* Christina Last (Turing)
* David Beavan (Turing)
* Ed Lowther (UCL)
* Tom Crouch (UCL)
* Rebecca Osselton (University of Newcastle)

#### Collaborating organisations/universities

UCL Advanced Research Computing Centre (Collaborator)
University of Cambridge (Collaborator)
Universityof Newcastle (Collaborator)

(Please include their roles as part of the project, e.g. funder, collaborator, data supplier etc)

#### Additional content

#### If this project is part of a programme(s) please tick below

Research Engineering

Tools, practices and systems

#### Is this project funded by the Strategic Priorities Fund?

No

### Research areas (required)

(Please tick the research areas that are most applicable, up to max 10)


Data Structures

Operations Research

Knowledge Representation

Human Computer Interface

Differential Privacy
Identity Management
Verification

Data Science of Government & Politics

Research Methods
