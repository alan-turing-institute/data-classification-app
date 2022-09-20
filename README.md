# Classification webapp for the Turing Data Safe Haven
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-20-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

This is a web application that can be used for data classification. It is designed for use with
the [Turing Safe Haven](https://github.com/alan-turing-institute/data-safe-haven).


## Requirements

The web application is not designed for any specific cloud platform, but currently has only been tested on Azure.
 The web framework is built on Django with Python3. It uses an external database (tested on PostgreSQL),
 OAuth2 for authentication (tested on OAuth2 for Azure Active Directory) and Graph API for group membership.

The webapp has been tested, and instructions are provided for, the following deployment scenarios:
- local development, using a locally-hosted SQL database (eg PostgreSQL)
- web deployment, using an Azure subscription



## Learn more about the Turing Safe Haven

* [Main project README](https://github.com/alan-turing-institute/data-safe-haven/blob/master/README.md)
* [Contributing guidelines](https://github.com/alan-turing-institute/data-safe-haven/blob/master/CONTRIBUTING.md)
* [Code of Conduct](https://github.com/alan-turing-institute/data-safe-haven/blob/master/CODE_OF_CONDUCT.md)

## Deploying test instances for development

* [Setting up local development](docs/development/set-up-local-development.md)
* [Creating a staging server on Azure](docs/development/create-staging-server-on-azure.md)
* [Local development notes](docs/development/local-development-notes.md)


## Deploying a production instance on Azure

* [Web deployment on Azure](docs/create-management-webapp/azure-deploy-management-webapp.md)

## Sample user guide

* [Instructions for data provider representatives](docs/user_guide/user_guide.md)

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center"><a href="https://github.com/harisood"><img src="https://avatars.githubusercontent.com/u/67151373?v=4?s=100" width="100px;" alt=""/><br /><sub><b>harisood</b></sub></a><br /><a href="#content-harisood" title="Content">🖋</a></td>
      <td align="center"><a href="https://edlowther.github.io/"><img src="https://avatars.githubusercontent.com/u/7374954?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Ed Lowther</b></sub></a><br /><a href="#ideas-edlowther" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/issues?q=author%3Aedlowther" title="Bug reports">🐛</a> <a href="#content-edlowther" title="Content">🖋</a> <a href="https://github.com/alan-turing-institute/data-classification-app/commits?author=edlowther" title="Code">💻</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Aedlowther" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/rosselton"><img src="https://avatars.githubusercontent.com/u/51399124?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Rebecca Osselton</b></sub></a><br /><a href="https://github.com/alan-turing-institute/data-classification-app/issues?q=author%3Arosselton" title="Bug reports">🐛</a> <a href="https://github.com/alan-turing-institute/data-classification-app/commits?author=rosselton" title="Code">💻</a> <a href="#content-rosselton" title="Content">🖋</a> <a href="#ideas-rosselton" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Arosselton" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://christinalast.com"><img src="https://avatars.githubusercontent.com/u/36204574?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Christina Last</b></sub></a><br /><a href="https://github.com/alan-turing-institute/data-classification-app/issues?q=author%3AChristinaLast" title="Bug reports">🐛</a> <a href="https://github.com/alan-turing-institute/data-classification-app/commits?author=ChristinaLast" title="Code">💻</a> <a href="#content-ChristinaLast" title="Content">🖋</a> <a href="#ideas-ChristinaLast" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3AChristinaLast" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/Arielle-Bennett"><img src="https://avatars.githubusercontent.com/u/74651964?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Arielle-Bennett</b></sub></a><br /><a href="#content-Arielle-Bennett" title="Content">🖋</a> <a href="#ideas-Arielle-Bennett" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3AArielle-Bennett" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/tcouch"><img src="https://avatars.githubusercontent.com/u/5113832?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Tom Couch</b></sub></a><br /><a href="https://github.com/alan-turing-institute/data-classification-app/issues?q=author%3Atcouch" title="Bug reports">🐛</a> <a href="https://github.com/alan-turing-institute/data-classification-app/commits?author=tcouch" title="Code">💻</a> <a href="#content-tcouch" title="Content">🖋</a> <a href="#ideas-tcouch" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Atcouch" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/DavidBeavan"><img src="https://avatars.githubusercontent.com/u/6524799?v=4?s=100" width="100px;" alt=""/><br /><sub><b>David Beavan</b></sub></a><br /><a href="https://github.com/alan-turing-institute/data-classification-app/commits?author=DavidBeavan" title="Code">💻</a> <a href="#content-DavidBeavan" title="Content">🖋</a> <a href="#ideas-DavidBeavan" title="Ideas, Planning, & Feedback">🤔</a> <a href="#projectManagement-DavidBeavan" title="Project Management">📆</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3ADavidBeavan" title="Reviewed Pull Requests">👀</a></td>
    </tr>
    <tr>
      <td align="center"><a href="https://github.com/martintoreilly"><img src="https://avatars.githubusercontent.com/u/21147592?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Martin O'Reilly</b></sub></a><br /><a href="#content-martintoreilly" title="Content">🖋</a> <a href="#ideas-martintoreilly" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Amartintoreilly" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/trevor-ucl"><img src="https://avatars.githubusercontent.com/u/97737012?v=4?s=100" width="100px;" alt=""/><br /><sub><b>trevor-ucl</b></sub></a><br /><a href="#content-trevor-ucl" title="Content">🖋</a> <a href="#ideas-trevor-ucl" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Atrevor-ucl" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/jamespjh"><img src="https://avatars.githubusercontent.com/u/55009?v=4?s=100" width="100px;" alt=""/><br /><sub><b>James Hetherington</b></sub></a><br /><a href="#ideas-jamespjh" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Ajamespjh" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/wojtur"><img src="https://avatars.githubusercontent.com/u/6866254?v=4?s=100" width="100px;" alt=""/><br /><sub><b>wojtur</b></sub></a><br /><a href="#ideas-wojtur" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Awojtur" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/jemrobinson"><img src="https://avatars.githubusercontent.com/u/3502751?v=4?s=100" width="100px;" alt=""/><br /><sub><b>James Robinson</b></sub></a><br /><a href="#ideas-jemrobinson" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Ajemrobinson" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="www.tomdoel.com"><img src="https://avatars.githubusercontent.com/u/4216900?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Tom Doel</b></sub></a><br /><a href="https://github.com/alan-turing-institute/data-classification-app/issues?q=author%3Atomdoel" title="Bug reports">🐛</a> <a href="https://github.com/alan-turing-institute/data-classification-app/commits?author=tomdoel" title="Code">💻</a> <a href="#content-tomdoel" title="Content">🖋</a> <a href="#ideas-tomdoel" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Atomdoel" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/steven-cd"><img src="https://avatars.githubusercontent.com/u/5108635?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Steven Carlysle-Davies</b></sub></a><br /><a href="https://github.com/alan-turing-institute/data-classification-app/issues?q=author%3Asteven-cd" title="Bug reports">🐛</a> <a href="https://github.com/alan-turing-institute/data-classification-app/commits?author=steven-cd" title="Code">💻</a> <a href="#content-steven-cd" title="Content">🖋</a> <a href="#ideas-steven-cd" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Asteven-cd" title="Reviewed Pull Requests">👀</a></td>
    </tr>
    <tr>
      <td align="center"><a href="https://github.com/jack89roberts"><img src="https://avatars.githubusercontent.com/u/16308271?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Jack Roberts</b></sub></a><br /><a href="#ideas-jack89roberts" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center"><a href="https://github.com/bw-faststream"><img src="https://avatars.githubusercontent.com/u/54804128?v=4?s=100" width="100px;" alt=""/><br /><sub><b>bw-faststream</b></sub></a><br /><a href="#content-bw-faststream" title="Content">🖋</a> <a href="#ideas-bw-faststream" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Abw-faststream" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/sysdan"><img src="https://avatars.githubusercontent.com/u/49038294?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Daniel</b></sub></a><br /><a href="#content-sysdan" title="Content">🖋</a> <a href="#ideas-sysdan" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Asysdan" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/jackgrahamhindley"><img src="https://avatars.githubusercontent.com/u/62214824?v=4?s=100" width="100px;" alt=""/><br /><sub><b>jackgrahamhindley</b></sub></a><br /><a href="#content-jackgrahamhindley" title="Content">🖋</a> <a href="#ideas-jackgrahamhindley" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Ajackgrahamhindley" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/oforrest"><img src="https://avatars.githubusercontent.com/u/49275282?v=4?s=100" width="100px;" alt=""/><br /><sub><b>oforrest</b></sub></a><br /><a href="#content-oforrest" title="Content">🖋</a> <a href="#ideas-oforrest" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/alan-turing-institute/data-classification-app/pulls?q=is%3Apr+reviewed-by%3Aoforrest" title="Reviewed Pull Requests">👀</a></td>
      <td align="center"><a href="https://github.com/JulesMarz"><img src="https://avatars.githubusercontent.com/u/40864686?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Jules M</b></sub></a><br /><a href="#ideas-JulesMarz" title="Ideas, Planning, & Feedback">🤔</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->

<table>
  <tr>
    <td align="center"><a href="https://github.com/harisood"><img src="https://avatars.githubusercontent.com/u/67151373?v=4?s=100" width="100px;" alt=""/><br /><sub><b>harisood</b></sub></a><br /><a href="#content-harisood" title="Content">🖋</a></td>
  </tr>
</table>


<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
