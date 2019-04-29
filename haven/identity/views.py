import csv

import openpyxl
from braces.views import UserFormKwargsMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView
from phonenumber_field.phonenumber import PhoneNumber

from core.forms import InlineFormSetHelper
from projects.forms import ProjectsForUserInlineFormSet

from .forms import CreateUserForm
from .mixins import UserRoleRequiredMixin
from .models import User
from .roles import UserRole

class UserCreate(LoginRequiredMixin,
                 UserFormKwargsMixin,
                 UserRoleRequiredMixin,
                 CreateView):
    form_class = CreateUserForm
    model = User
    success_url = '/'

    user_roles = [UserRole.SYSTEM_CONTROLLER]

    def get_context_data(self, **kwargs):
        kwargs['helper'] = InlineFormSetHelper()
        kwargs['formset'] = self.get_formset()
        kwargs['editing'] = False
        return super().get_context_data(**kwargs)

    def get_formset(self, **kwargs):
        form_kwargs = {'user': self.request.user}
        if self.request.method == 'POST':
            return ProjectsForUserInlineFormSet(self.request.POST, form_kwargs=form_kwargs)
        else:
            return ProjectsForUserInlineFormSet(form_kwargs=form_kwargs)

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        form = self.get_form()
        self.object = None
        if form.is_valid() and formset.is_valid():
            response = self.form_valid(form)
            formset.instance = self.object
            formset.save()
            return response
        else:
            return self.form_invalid(form)


class UserEdit(LoginRequiredMixin,
               UserRoleRequiredMixin,
               DetailView):
    model = User
    template_name = 'identity/user_form.html'

    user_roles = [UserRole.SYSTEM_CONTROLLER]

    def get_success_url(self):
        return reverse('identity:edit_user', args=[self.get_object().id])

    def get_context_data(self, **kwargs):
        kwargs['helper'] = InlineFormSetHelper()
        if 'formset' not in kwargs:
            kwargs['formset'] = self.get_formset()
        kwargs['subject_user'] = self.get_object()
        kwargs['editing'] = True
        return super().get_context_data(**kwargs)

    def get_formset(self, **kwargs):
        form_kwargs = {'user': self.request.user}
        if self.request.method == 'POST':
            return ProjectsForUserInlineFormSet(
                self.request.POST,
                instance=self.get_object(),
                form_kwargs=form_kwargs
            )
        else:
            return ProjectsForUserInlineFormSet(
                instance=self.get_object(),
                form_kwargs=form_kwargs
            )

    def post(self, request, *args, **kwargs):
        formset = self.get_formset()
        self.object = self.get_object()
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(formset=formset))


class UserList(LoginRequiredMixin, UserRoleRequiredMixin, ListView):
    """List of users"""

    context_object_name = 'users'
    model = User

    user_roles = [UserRole.SYSTEM_CONTROLLER, UserRole.RESEARCH_COORDINATOR]

    def get_queryset(self):
        return User.objects.get_visible_users(self.request.user)


def export_users(request):
    """Export list of users as a UserCreate.csv file"""

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="UserCreate.csv"'

    writer = csv.writer(response)

    writer.writerow([
        'SamAccountName',
        'GivenName',
        'Surname',
        'Mobile',
        'SecondaryEmail'
    ])

    # Write out all users visible to the current user
    for user in User.objects.get_visible_users(request.user):

        # Remove the domain from the username
        username = user.username.split('@')[0]

        writer.writerow([
            username,
            user.first_name,
            user.last_name,
            user.mobile,
            user.email
        ])

    return response


def import_users(request):
    """Import list of users from an uploaded file"""

    if "POST" == request.method and request.FILES and request.FILES["upload_file"]:
        try:
            upload_file = request.FILES["upload_file"]

            if upload_file.name.endswith('.xlsx'):
                users = xlsx_users(upload_file)

            elif upload_file.name.endswith('.csv'):
                users = csv_users(upload_file.read().decode("utf-8"))

            else:
                messages.error(request, 'Can only import .csv or .xlsx files')
                return HttpResponseRedirect(reverse("identity:list"))

            for new_user in users:

                # Construct a string for displaying as a message
                user_string = new_user.first_name + " " + new_user.last_name \
                              + " (" + new_user.email + ")"

                # Check whether a user with this name and email already exists
                if User.objects.filter(
                    email=new_user.email
                ).exists():
                    messages.info(request, "Email already exists:  " + user_string)
                else:
                    # Save the new user to the database
                    new_user.generate_username()
                    new_user.created_by = request.user
                    new_user.save()
                    messages.info(request, "Created user " + user_string)

        except Exception as e:
            messages.error(request,
                           "The file could not be processed. Error: " + repr(e))

    return HttpResponseRedirect(reverse("identity:list"))


def csv_users(lines):
    """Generator for users from a CSV file"""

    reader = csv.DictReader(lines.split("\n"))
    for row in reader:
        yield User(
            first_name=row['First Name'],
            last_name=row['Last Name'],
            mobile=PhoneNumber.from_string(row['Mobile Phone'],
                                           region='GB'),
            email=row['Email']
        )

def xlsx_users(upload_file):
    """Generator for users from an xlsx file"""

    workbook = openpyxl.load_workbook(upload_file)
    for worksheet in workbook.worksheets:

        row_iter = worksheet.iter_rows()

        column_names = next(row_iter)
        for row in row_iter:
            row_dict = {}
            for title, entry in zip(column_names, row):
                row_dict[title.value] = entry.value

            yield User(
                first_name=row_dict['First Name'],
                last_name=row_dict['Last Name'],
                mobile=PhoneNumber.from_string(row_dict['Mobile Phone'],
                                               region='GB'),
                email=row_dict['Email']
            )
