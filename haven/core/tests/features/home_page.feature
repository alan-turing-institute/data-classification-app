Feature: Home Page

Scenario: Load Home Page
    When I go to the home page
    Then I should see the login button

Scenario: Load Home Page as logged-in user
    Given I have logged in
    When I go to the home page
    Then I should see the projects button
