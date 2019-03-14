from braces.views import UserFormKwargsMixin
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
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


class UserList(LoginRequiredMixin, ListView):
    """List of users"""

    context_object_name = 'users'
    model = User

    def get_queryset(self):
        return User.objects.get_visible_users(self.request.user)


def import_users(request):

    if "GET" == request.method:
        return HttpResponseRedirect(reverse("identity:list"))

    if "POST" == request.method and request.FILES and request.FILES["upload_file"]:
        try:
            upload_file = request.FILES["upload_file"]
            if not upload_file.name.endswith('.csv'):
                messages.error(request, 'This file cannot be processed as it is not a .csv file')
                return HttpResponseRedirect(reverse("identity:list"))

            # if file is too large, return
            if upload_file.multiple_chunks():
                messages.error(request, "This file is too large to process.")
                return HttpResponseRedirect(reverse("identity:list"))

            # messages.warning(request, 'User file import has not yet been implemented.')
            fp = FileParser(upload_file)
            if not fp.ok:
                messages.error(request, "The column names were not understood.")
                return HttpResponseRedirect(reverse("identity:list"))

            while not fp.eof():
                new_user = fp.next_line()
                user_string = new_user.first_name + " " + new_user.last_name\
                              + " (" + new_user.email + ")"

                try:
                    # Determine uniqueness using first name, last name and email
                    existing_user_id = User.objects.filter(first_name=new_user.first_name, last_name=new_user.last_name, email=new_user.email)
                    if existing_user_id.exists():
                        messages.info(request, "Already exists:  " + user_string)
                    else:
                        new_user.generate_username()
                        new_user.save()
                        messages.info(request, "Created user " + user_string)
                except:
                    messages.info(request, "Error adding user " + user_string)

        except Exception as e:
            messages.error(request,"The file could not be processed. Error: " + repr(e))
    else:
        messages.error(request, "The file could not be processed.")

    return HttpResponseRedirect(reverse("identity:list"))


class FileParser:
    def __init__(self, upload_file):
        file_data = upload_file.read().decode("utf-8")
        self.lines = file_data.split("\n")
        self.line_index = 1
        titles = self.lines[0].split(",")
        try:
            self.first_name_index = find_index(titles, "First Name")
            self.last_name_index = find_index(titles, "Last Name")
            self.email_index = find_index(titles, "Email")
            self.mobile_index = find_index(titles, "Mobile Phone")
            self.ok = True
        except ValueError:
            self.ok = False

    def eof(self):
        return self.line_index >= len(self.lines)

    def next_line(self):
        fields = self.lines[self.line_index].split(",")
        self.line_index += 1
        first_name = fields[self.first_name_index]
        last_name = fields[self.last_name_index]
        email = fields[self.email_index]
        mobile = PhoneNumber.from_string(fields[self.mobile_index], region='GB')
        new_user = User(first_name=first_name, last_name=last_name,
                        mobile=mobile, email=email)
        return new_user


def find_index(fields, name):
    return [item.lower() for item in fields].index(name.lower())