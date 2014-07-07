import re
import logging

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import forms as auth_forms
from django.utils.translation import ugettext as _

from captcha import fields as captcha_fields
from taggit.forms import TagField
from taggit.utils import edit_string_for_tags

from users.blacklist import passwords as blacklisted_passwords
from users.models import UserProfile, TaggedProfile
from users.fields import UsernameField
from users import drupal
from links.models import Link


log = logging.getLogger(__name__)


class AuthenticationForm(auth_forms.AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'tabindex': '1'}))
    password = forms.CharField(
        max_length=255,
        widget=forms.PasswordInput(attrs={'tabindex': '2'},
                                   render_value=False))
    remember_me = forms.BooleanField(required=False,
                                     widget=forms.CheckboxInput(
                                         attrs={'tabindex': '3'}))


def check_password_complexity(password):
    message = _('Password must be at least 8 characters long ')
    message += _('and contain both numbers and letters.')
    if len(password) < 8 or not (
        re.search('[A-Za-z]', password) and re.search('[0-9]', password)):
        return message
    if password in blacklisted_passwords:
        return _('That password is too common. Please choose another.')
    return None


class SetPasswordForm(auth_forms.SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super(SetPasswordForm, self).__init__(*args, **kwargs)

        # make sure to set the password in the user profile
        # FIXME: this probably breaks more stuff, but it definately breaks password reset tokens!!
        if isinstance(self.user, User):
            self.user = self.user.get_profile()

    def clean_new_password1(self):
        password = self.cleaned_data['new_password1']
        message = check_password_complexity(password)
        if message:
            self._errors['new_password1'] = forms.util.ErrorList([message])
        return password


class OpenIDForm(forms.Form):
    openid_identifier = forms.URLField()

    def clean_openid_identifier(self):
        msg = _('This Google OpenID is not supported. ')
        msg += _('Please use your Google profile OpenID.')
        openid = self.cleaned_data['openid_identifier']
        if drupal.GOOGLE_OPENID in openid:
            raise forms.ValidationError(msg)
        return openid


def validate_user_identity(form, data):
    msg = _('Your account was migrated from the old P2PU website.')
    username_provided = ('username' in data and data['username'])
    if username_provided and drupal.get_user(data['username']):
        form._errors['username'] = forms.util.ErrorList([msg])
    email_provided = ('email' in data and data['email'])
    if email_provided and drupal.get_user(data['email']):
        form._errors['email'] = forms.util.ErrorList([msg])


class CreateProfileForm(forms.ModelForm):
    recaptcha = captcha_fields.ReCaptchaField()
    email_confirm = forms.EmailField(max_length=75)

    class Meta:
        model = UserProfile
        fields = ('username', 'full_name', 'email', 'preflang')
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        super(CreateProfileForm, self).__init__(*args, **kwargs)

        if not settings.RECAPTCHA_PRIVATE_KEY:
            del self.fields['recaptcha']

    def clean(self):
        super(CreateProfileForm, self).clean()
        data = self.cleaned_data
        validate_user_identity(self, data)
        if 'full_name' in data:
            data['full_name'] = data['full_name'].strip()
        if 'email' in data and 'email_confirm' in data:
            if data['email'] != data['email_confirm']:
                self._errors['email_confirm'] = forms.util.ErrorList([
                    _('Email addresses do not match.')])
        return data


class RegisterForm(forms.ModelForm):
    username = UsernameField()
    full_name = forms.CharField(max_length=255, required=False)
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(render_value=False))
    password_confirm = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(render_value=False))
    preflang = forms.CharField(max_length=5,
            widget=forms.Select(choices=settings.SUPPORTED_LANGUAGES),
            initial=settings.LANGUAGE_CODE)
    recaptcha = captcha_fields.ReCaptchaField()
    email_confirm = forms.EmailField(max_length=75)

    class Meta:
        model = User
        fields = ('username', 'email', 'preflang')
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

        if not settings.RECAPTCHA_PRIVATE_KEY:
            del self.fields['recaptcha']

    def clean_password(self):
        password = self.cleaned_data['password']
        message = check_password_complexity(password)
        if message:
            self._errors['password'] = forms.util.ErrorList([message])
        return password

    def clean_username(self):
        username = self.cleaned_data['username']
        if UserProfile.objects.filter(username=username).exists():
            raise forms.ValidationError(
                _('User profile with this Username already exists.'))
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if not email or not email.strip():
            raise forms.ValidationError(_('This field is required.'))
        if UserProfile.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _('User profile with this Email already exists.'))
        return email

    def clean(self):
        super(RegisterForm, self).clean()
        data = self.cleaned_data
        validate_user_identity(self, data)
        if 'password' in data and 'password_confirm' in data:
            if data['password'] != data['password_confirm']:
                self._errors['password_confirm'] = forms.util.ErrorList([
                    _('Passwords do not match.')])
        if 'email' in data and 'email_confirm' in data:
            if data['email'] != data['email_confirm']:
                self._errors['email_confirm'] = forms.util.ErrorList([
                    _('Email addresses do not match.')])
        if 'full_name' in data:
            data['full_name'] = data['full_name'].strip()
        return data


class CategoryTagWidget(forms.TextInput):
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category', None)
        super(CategoryTagWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        if value is not None and not isinstance(value, basestring):
            objs = value.select_related("tag").filter(
                tag__category=self.category)
            value = edit_string_for_tags([o.tag for o in objs])
        return super(CategoryTagWidget, self).render(name, value, attrs)


class CategoryTagField(TagField):
    def __init__(self, **kwargs):
        category = kwargs.pop('category', None)
        self.widget = CategoryTagWidget(category=category)
        super(CategoryTagField, self).__init__(**kwargs)

    def clean(self, value):
        value = super(CategoryTagField, self).clean(value)
        value = [i.lower() for i in value]
        return value


class ProfileEditForm(forms.ModelForm):
    interest = CategoryTagField(category='interest', required=False)
    skill = CategoryTagField(category='skill', required=False)
    desired_topic = CategoryTagField(category='desired_topic', required=False)

    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)

        if 'instance' in kwargs:
            instance = kwargs['instance']
            self.initial['interest'] = TaggedProfile.objects.filter(
                object_id=instance.id)
            self.initial['skill'] = TaggedProfile.objects.filter(
                object_id=instance.id)
            self.initial['desired_topic'] = TaggedProfile.objects.filter(
                object_id=instance.id)

    def save(self, commit=True):
        model = super(ProfileEditForm, self).save(commit=False)
        model.tags.set('interest', *self.cleaned_data['interest'])
        model.tags.set('skill', *self.cleaned_data['skill'])
        model.tags.set('desired_topic', *self.cleaned_data['desired_topic'])
        if commit:
            model.save()
        return model

    class Meta:
        model = UserProfile
        fields = ('full_name', 'location', 'bio', 'preflang', 'interest')
        widgets = {
            'interest': CategoryTagWidget(category='interest')
        }

    def clean(self):
        super(ProfileEditForm, self).clean()
        data = self.cleaned_data
        if 'full_name' in data:
            data['full_name'] = data['full_name'].strip()
        return data


class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('image',)

    def clean_image(self):
        if not self.cleaned_data['image']:
            return self.cleaned_data['image']
        if self.cleaned_data['image'].size > settings.MAX_IMAGE_SIZE:
            max_size = settings.MAX_IMAGE_SIZE / 1024
            raise forms.ValidationError(
                _("Image exceeds max image size: %(max)dk") % dict(
                    max=max_size))
        return self.cleaned_data['image']


class ProfileLinksForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ('name', 'url', 'subscribe',)


class PasswordResetForm(auth_forms.PasswordResetForm):
    email = forms.CharField(
        widget=forms.TextInput(attrs={'tabindex': '1'}))

    def clean_email(self):
        email = self.cleaned_data["email"]
        is_email = "@" in email
        if is_email:
            self.users_cache = User.objects.filter(
                                email__iexact=email,
                                is_active=True
                            )
        else:
            self.users_cache = User.objects.filter(
                    username__iexact=email,
                    is_active=True
                )
        profile = None
        for user in self.users_cache:
            try:
                profile = user.get_profile()
            except UserProfile.DoesNotExist:
                user.delete()
        if not profile and not drupal.migrate(email):
            msg = _("That e-mail address isn't associated to a user account. ")
            msg2 = _("You didn't finish registering the last time. ")
            msg2 += _("Please register a new account.")
            if len(self.users_cache) == 0:
                if not is_email:
                    msg = _("Username not found. ")
                msg += _("Are you sure you've registered?")
                raise forms.ValidationError(msg)
            else:
                raise forms.ValidationError(msg2)
        return email
