Feature: Projects List

Scenario: View projects list
    Given I have logged in
    When I go to the projects page
    Then I should see a list of my projects

Scenario: Create new project
    Given I have logged in
    When I create a new project
    And I go to my new project
    Then I should see my new project details

Scenario: Add new project to list
    Given I have logged in
    When I create a new project
    And I go to the projects page
    Then I should see my new project in the list
