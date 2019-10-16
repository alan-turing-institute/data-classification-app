import re

import pytest
from pytest_bdd import given, scenarios, then, when
from splinter.exceptions import ElementDoesNotExist


scenarios('features')


class Page:
    def __init__(self, browser, base_url, navigate_to=False):
        url = base_url + self.path
        if navigate_to:
            browser.visit(url)
        assert re.match(f"^{url}$", browser.url)
        self.base_url = base_url
        self.browser = browser


class HomePage(Page):
    path = '/'

    @property
    def login_button(self):
        return self.browser.find_by_text('Log In').first

    @property
    def projects_button(self):
        return self.browser.find_by_text('View your projects').first


class ProjectsPage(Page):
    path = '/projects/'

    def get_project_link(self, project):
        return self.browser.find_by_text(project).first

    def click_project_link(self, project):
        self.get_project_link(project).click()
        return ProjectPage(self.browser, self.base_url)

    def click_create_project_button(self):
        self.browser.find_by_text('Create Project').first.click()
        return AddProjectPage(self.browser, self.base_url)


class AddProjectPage(Page):
    path = '/projects/new'

    def create_project(self, name, description):
        self.browser.fill('name', name)
        self.browser.fill('description', description)
        self.browser.find_by_value('Save Project').first.click()
        return ProjectsPage(self.browser, self.base_url)


class ArchiveProjectPage(Page):
    path = r'/projects/(?P<id>\d+)/archive'

    def click_confirm_button(self):
        self.browser.find_by_value('Archive Project').first.click()
        return ProjectsPage(self.browser, self.base_url)


class ProjectPage(Page):
    path = r'/projects/(?P<id>\d+)'

    @property
    def name(self):
        return self.browser.find_by_tag('h1').first.value

    @property
    def description(self):
        return self.browser.find_by_css('div[role="group"]:nth-child(1) div:nth-child(2) p').first.value

    def click_archive_button(self):
        self.browser.find_by_text('Archive Project').first.click()
        return ArchiveProjectPage(self.browser, self.base_url)


class AdminLoginPage(Page):
    path = '/admin/login/'

    def login(self, username, password):
        self.browser.fill('username', username)
        self.browser.fill('password', password)
        self.browser.find_by_value('Log in').first.click()
        return None  # Should be an AdminHomePage, but we don't need to implement all that


@pytest.fixture
def base_url():
    return 'http://127.0.0.1:43000'


@pytest.fixture
def home_page(browser, base_url):
    return HomePage(browser, base_url)


@pytest.fixture
def projects_page(browser, base_url):
    return ProjectsPage(browser, base_url)


@pytest.fixture
def add_project_page(browser, base_url):
    return AddProjectPage(browser, base_url)


@pytest.fixture
def project_page(browser, base_url):
    return ProjectPage(browser, base_url)


@given('I have logged in')
def authenticated_user(browser, base_url):
    page = AdminLoginPage(browser, base_url, navigate_to=True)
    page = page.login('haven', 'haven')


@when('I go to the home page')
def go_to_home(browser, base_url):
    return HomePage(browser, base_url, navigate_to=True)


@when('I go to the projects page')
def go_to_projects(browser, base_url):
    return ProjectsPage(browser, base_url, navigate_to=True)


@pytest.fixture
@when('I create a new project')
def create_project(browser, base_url):
    import logging
    logging.warning('Creating project')
    page = ProjectsPage(browser, base_url, navigate_to=True)
    page = page.click_create_project_button()
    yield page.create_project('Project 7', 'A description')
    logging.warning('Destroying project')
    page = ProjectsPage(browser, base_url, navigate_to=True)
    page = page.click_project_link('Project 7')
    page = page.click_archive_button()
    page = page.click_confirm_button()
    with pytest.raises(ElementDoesNotExist):
        page.get_project_link('Project 7')


@when('I go to my new project')
def go_to_project(create_project):
    return create_project.click_project_link('Project 7')


@then('I should see the login button')
def check_login_button(home_page):
    assert home_page.login_button.visible


@then('I should see the projects button')
def check_projects_button(home_page):
    assert home_page.projects_button.visible


@then('I should see a list of my projects')
def check_projects_list(projects_page):
    projects = [
        'Project 1',
        'Project 2',
        'Project 3',
        'Project 4',
        'Project 5',
        'Project 6',
    ]
    for project in projects:
        assert projects_page.get_project_link(project).visible


@then('I should see my new project in the list')
def check_new_project(create_project):
    assert create_project.get_project_link('Project 7').visible


@then('I should see my new project details')
def check_new_project_details(project_page):
    assert project_page.name == 'Project 7'
    assert project_page.description == 'A description'
