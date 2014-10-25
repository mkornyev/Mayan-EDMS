from __future__ import absolute_import

import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from acls.models import AccessEntry
from acls.utils import apply_default_acls
from acls.views import acl_list_for
from common.utils import encapsulate
from common.widgets import two_state_template
from documents.models import Document
from documents.permissions import PERMISSION_DOCUMENT_VIEW
from documents.views import document_list
from permissions.models import Permission

from .forms import (SmartLinkConditionForm, SmartLinkInstanceForm,
                    SmartLinkForm)
from .links import smart_link_instance_view_link
from .models import SmartLink, SmartLinkCondition
from .permissions import (PERMISSION_SMART_LINK_CREATE,
                          PERMISSION_SMART_LINK_DELETE,
                          PERMISSION_SMART_LINK_EDIT,
                          PERMISSION_SMART_LINK_VIEW)
from .settings import SHOW_EMPTY_SMART_LINKS

logger = logging.getLogger(__name__)


def smart_link_action(request):
    action = request.GET.get('action', None)

    if not action:
        messages.error(request, _(u'No action selected.'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('main:home')))

    return HttpResponseRedirect(action)


def smart_link_instance_view(request, document_id, smart_link_pk):
    document = get_object_or_404(Document, pk=document_id)
    smart_link = get_object_or_404(SmartLink, pk=smart_link_pk)

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_VIEW])
    except PermissionDenied:
        AccessEntry.objects.check_access(PERMISSION_SMART_LINK_VIEW, request.user, smart_link)

    object_list, errors = SmartLink.objects.get_smart_link_instances_for(document, smart_link)

    return document_list(
        request,
        title=_(u'Documents in smart link: %(group)s') % {
            'group': object_list['title']
        },
        object_list=object_list['documents'],
        extra_context={
            'object': document
        }
    )


def smart_link_instances_for_document(request, document_id):
    subtemplates_list = []
    document = get_object_or_404(Document, pk=document_id)
    smart_link_instances, errors = SmartLink.objects.get_smart_link_instances_for(document)
    if (request.user.is_staff or request.user.is_superuser) and errors:
        for error in errors:
            messages.warning(request, _(u'Smart link query error: %s' % error))

    if not SHOW_EMPTY_SMART_LINKS:
        # If SHOW_EMPTY_SMART_LINKS is False, remove empty groups from
        # dictionary
        smart_link_instances = dict([(group, data) for group, data in smart_link_instances.items() if data['documents']])

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_VIEW])
    except PermissionDenied:
        smart_link_instances_keys_filtered = AccessEntry.objects.filter_objects_by_access(PERMISSION_SMART_LINK_VIEW, request.user, smart_link_instances.keys())
        # Remove smart link instances not found in the new filtered key list
        for key, value in smart_link_instances.items():
            if key not in smart_link_instances_keys_filtered:
                smart_link_instances.pop(key)

            value['documents'] = AccessEntry.objects.filter_objects_by_access(PERMISSION_DOCUMENT_VIEW, request.user, value['documents'])

    if smart_link_instances:
        subtemplates_list = [{
            'name': 'main/generic_form_subtemplate.html',
            'context': {
                'title': _(u'Smart links (%s)') % len(smart_link_instances.keys()),
                'form': SmartLinkInstanceForm(
                    smart_link_instances=smart_link_instances, current_document=document,
                    links=[smart_link_instance_view_link]
                ),
                'form_action': reverse('linking:smart_link_action'),
                'submit_method': 'GET',
            }
        }]
    else:
        # If there are not group display a placeholder messages saying so
        subtemplates_list = [{
            'name': 'main/generic_subtemplate.html',
            'context': {
                'content': _(u'There are no defined smart links for the current document.'),
            }
        }]

    return render_to_response('main/generic_detail.html', {
        'object': document,
        'document': document,
        'subtemplates_list': subtemplates_list,
    }, context_instance=RequestContext(request))


def smart_link_list(request):
    qs = SmartLink.objects.all()

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_VIEW])
    except PermissionDenied:
        qs = AccessEntry.objects.filter_objects_by_access(PERMISSION_SMART_LINK_VIEW, request.user, qs)

    return render_to_response('main/generic_list.html', {
        'title': _(u'Smart links'),
        'object_list': qs,
        'extra_columns': [
            {'name': _(u'Dynamic title'), 'attribute': 'dynamic_title'},
            {'name': _(u'Enabled'), 'attribute': encapsulate(lambda x: two_state_template(x.enabled))},
        ],
        'hide_link': True,
        'list_object_variable_name': 'smart_link',

    }, context_instance=RequestContext(request))


def smart_link_create(request):
    Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_CREATE])

    if request.method == 'POST':
        form = SmartLinkForm(request.POST)
        if form.is_valid():
            document_group = form.save()
            apply_default_acls(document_group, request.user)
            messages.success(request, _(u'Smart link: %s created successfully.') % document_group)
            return HttpResponseRedirect(reverse('linking:smart_link_list'))
    else:
        form = SmartLinkForm()

    return render_to_response('main/generic_form.html', {
        'form': form,
        'title': _(u'Create new smart link')
    }, context_instance=RequestContext(request))


def smart_link_edit(request, smart_link_pk):
    smart_link = get_object_or_404(SmartLink, pk=smart_link_pk)

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_EDIT])
    except PermissionDenied:
        AccessEntry.objects.check_access(PERMISSION_SMART_LINK_EDIT, request.user, smart_link)

    if request.method == 'POST':
        form = SmartLinkForm(request.POST, instance=smart_link)
        if form.is_valid():
            smart_link = form.save()
            messages.success(request, _(u'Smart link: %s edited successfully.') % smart_link)
            return HttpResponseRedirect(reverse('linking:smart_link_list'))
    else:
        form = SmartLinkForm(instance=smart_link)

    return render_to_response('main/generic_form.html', {
        'object': smart_link,
        'form': form,
        'title': _(u'Edit smart link: %s') % smart_link
    }, context_instance=RequestContext(request))


def smart_link_delete(request, smart_link_pk):
    smart_link = get_object_or_404(SmartLink, pk=smart_link_pk)

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_DELETE])
    except PermissionDenied:
        AccessEntry.objects.check_access(PERMISSION_SMART_LINK_DELETE, request.user, smart_link)

    next = request.POST.get('next', request.GET.get('next', request.META.get('HTTP_REFERER', reverse('main:home'))))
    previous = request.POST.get('previous', request.GET.get('previous', request.META.get('HTTP_REFERER', reverse('main:home'))))

    if request.method == 'POST':
        try:
            smart_link.delete()
            messages.success(request, _(u'Smart link: %s deleted successfully.') % smart_link)
        except Exception as exception:
            messages.error(request, _(u'Error deleting smart link: %(smart_link)s; %(exception)s.') % {
                'smart_link': smart_link,
                'exception': exception
            })
        return HttpResponseRedirect(next)

    return render_to_response('main/generic_confirm.html', {
        'delete_view': True,
        'object': smart_link,
        'title': _(u'Are you sure you wish to delete smart link: %s?') % smart_link,
        'next': next,
        'previous': previous,
    }, context_instance=RequestContext(request))


def smart_link_condition_list(request, smart_link_pk):
    smart_link = get_object_or_404(SmartLink, pk=smart_link_pk)

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_CREATE, PERMISSION_SMART_LINK_EDIT])
    except PermissionDenied:
        AccessEntry.objects.check_accesses([PERMISSION_SMART_LINK_CREATE, PERMISSION_SMART_LINK_EDIT], request.user, smart_link)

    return render_to_response('main/generic_list.html', {
        'title': _(u'Conditions for smart link: %s') % smart_link,
        'object_list': smart_link.smartlinkcondition_set.all(),
        'extra_columns': [
            {'name': _(u'Enabled'), 'attribute': encapsulate(lambda x: two_state_template(x.enabled))},
        ],
        'hide_link': True,
        'object': smart_link,
        'list_object_variable_name': 'condition',
    }, context_instance=RequestContext(request))


def smart_link_condition_create(request, smart_link_pk):
    smart_link = get_object_or_404(SmartLink, pk=smart_link_pk)

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_CREATE, PERMISSION_SMART_LINK_EDIT])
    except PermissionDenied:
        AccessEntry.objects.check_accesses([PERMISSION_SMART_LINK_CREATE, PERMISSION_SMART_LINK_EDIT], request.user, smart_link)

    if request.method == 'POST':
        form = SmartLinkConditionForm(request.POST)
        if form.is_valid():
            new_smart_link_condition = form.save(commit=False)
            new_smart_link_condition.smart_link = smart_link
            new_smart_link_condition.save()
            messages.success(request, _(u'Smart link condition: "%s" created successfully.') % new_smart_link_condition)
            return HttpResponseRedirect(reverse('linking:smart_link_condition_list', args=[smart_link.pk]))
    else:
        form = SmartLinkConditionForm(initial={'smart_link': smart_link})

    return render_to_response('main/generic_form.html', {
        'form': form,
        'title': _(u'Add new conditions to smart link: "%s"') % smart_link,
        'object': smart_link,
    }, context_instance=RequestContext(request))


def smart_link_condition_edit(request, smart_link_condition_pk):
    smart_link_condition = get_object_or_404(SmartLinkCondition, pk=smart_link_condition_pk)

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_CREATE, PERMISSION_SMART_LINK_EDIT])
    except PermissionDenied:
        AccessEntry.objects.check_accesses([PERMISSION_SMART_LINK_CREATE, PERMISSION_SMART_LINK_EDIT], request.user, smart_link_condition.smart_link)

    next = request.POST.get('next', request.GET.get('next', request.META.get('HTTP_REFERER', reverse('main:home'))))
    previous = request.POST.get('previous', request.GET.get('previous', request.META.get('HTTP_REFERER', reverse('main:home'))))

    if request.method == 'POST':
        form = SmartLinkConditionForm(request.POST, instance=smart_link_condition)
        if form.is_valid():
            new_smart_link_condition = form.save(commit=False)
            new_smart_link_condition.smart_link = smart_link_condition.smart_link
            new_smart_link_condition.save()
            messages.success(request, _(u'Smart link condition: "%s" edited successfully.') % new_smart_link_condition)
            return HttpResponseRedirect(next)
    else:
        form = SmartLinkConditionForm(instance=smart_link_condition)

    return render_to_response('main/generic_form.html', {
        'form': form,
        'title': _(u'Edit smart link condition'),
        'next': next,
        'previous': previous,
        'condition': smart_link_condition,
        'object': smart_link_condition.smart_link,
        'navigation_object_list': [
            {'object': 'object', 'name': _(u'Smart link')},
            {'object': 'condition', 'name': _(u'Condition')}
        ],

    }, context_instance=RequestContext(request))


def smart_link_condition_delete(request, smart_link_condition_pk):
    smart_link_condition = get_object_or_404(SmartLinkCondition, pk=smart_link_condition_pk)

    try:
        Permission.objects.check_permissions(request.user, [PERMISSION_SMART_LINK_CREATE, PERMISSION_SMART_LINK_EDIT])
    except PermissionDenied:
        AccessEntry.objects.check_accesses([PERMISSION_SMART_LINK_CREATE, PERMISSION_SMART_LINK_EDIT], request.user, smart_link_condition.smart_link)

    next = request.POST.get('next', request.GET.get('next', request.META.get('HTTP_REFERER', reverse('main:home'))))
    previous = request.POST.get('previous', request.GET.get('previous', request.META.get('HTTP_REFERER', reverse('main:home'))))

    if request.method == 'POST':
        try:
            smart_link_condition.delete()
            messages.success(request, _(u'Smart link condition: "%s" deleted successfully.') % smart_link_condition)
        except Exception as exception:
            messages.error(request, _(u'Error deleting smart link condition: %(smart_link_condition)s; %(exception)s.') % {
                'smart_link_condition': smart_link_condition,
                'exception': exception
            })
        return HttpResponseRedirect(next)

    return render_to_response('main/generic_confirm.html', {
        'delete_view': True,
        'condition': smart_link_condition,
        'object': smart_link_condition.smart_link,
        'navigation_object_list': [
            {'object': 'object', 'name': _(u'Smart link')},
            {'object': 'condition', 'name': _(u'Condition')}
        ],
        'title': _(u'Are you sure you wish to delete smart link condition: "%s"?') % smart_link_condition,
        'next': next,
        'previous': previous,
    }, context_instance=RequestContext(request))


def smart_link_acl_list(request, smart_link_pk):
    smart_link = get_object_or_404(SmartLink, pk=smart_link_pk)
    logger.debug('smart_link: %s' % smart_link)

    return acl_list_for(
        request,
        smart_link,
        extra_context={
            'object': smart_link,
            'smart_link': smart_link,
        }
    )
