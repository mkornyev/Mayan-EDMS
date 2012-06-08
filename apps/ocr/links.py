from __future__ import absolute_import

from django.utils.translation import ugettext_lazy as _

from navigation.api import Link

from .permissions import (PERMISSION_OCR_DOCUMENT,
    PERMISSION_OCR_DOCUMENT_DELETE, PERMISSION_OCR_QUEUE_ENABLE_DISABLE,
    PERMISSION_OCR_CLEAN_ALL_PAGES)

submit_document = Link(text=_('submit to OCR queue'), view='submit_document', args='object.id', sprite='hourglass_add', permissions=[PERMISSION_OCR_DOCUMENT])
submit_document_multiple = Link(text=_('submit to OCR queue'), view='submit_document_multiple', sprite='hourglass_add', permissions=[PERMISSION_OCR_DOCUMENT])
re_queue_document = Link(text=_('re-queue'), view='re_queue_document', args='object.id', sprite='hourglass_add', permissions=[PERMISSION_OCR_DOCUMENT])
re_queue_multiple_document = Link(text=_('re-queue'), view='re_queue_multiple_document', sprite='hourglass_add', permissions=[PERMISSION_OCR_DOCUMENT])
queue_document_delete = Link(text=_(u'delete'), view='queue_document_delete', args='object.id', sprite='hourglass_delete', permissions=[PERMISSION_OCR_DOCUMENT_DELETE])
queue_document_multiple_delete = Link(text=_(u'delete'), view='queue_document_multiple_delete', sprite='hourglass_delete', permissions=[PERMISSION_OCR_DOCUMENT_DELETE])

document_queue_disable = Link(text=_(u'stop queue'), view='document_queue_disable', args='queue.id', sprite='control_stop_blue', permissions=[PERMISSION_OCR_QUEUE_ENABLE_DISABLE])
document_queue_enable = Link(text=_(u'activate queue'), view='document_queue_enable', args='queue.id', sprite='control_play_blue', permissions=[PERMISSION_OCR_QUEUE_ENABLE_DISABLE])

all_document_ocr_cleanup = Link(text=_(u'clean up pages content'), view='all_document_ocr_cleanup', sprite='text_strikethrough', permissions=[PERMISSION_OCR_CLEAN_ALL_PAGES], description=_(u'Runs a language filter to remove common OCR mistakes from document pages content.'))

queue_document_list = Link(text=_(u'queue document list'), view='queue_document_list', sprite='hourglass', permissions=[PERMISSION_OCR_DOCUMENT])
ocr_tool_link = Link(text=_(u'OCR'), view='queue_document_list', sprite='hourglass', icon='text.png', permissions=[PERMISSION_OCR_DOCUMENT], children_view_regex=[r'queue_', r'document_queue'])

setup_queue_transformation_list = Link(text=_(u'transformations'), view='setup_queue_transformation_list', args='queue.pk', sprite='shape_move_front')
setup_queue_transformation_create = Link(text=_(u'add transformation'), view='setup_queue_transformation_create', args='queue.pk', sprite='shape_square_add')
setup_queue_transformation_edit = Link(text=_(u'edit'), view='setup_queue_transformation_edit', args='transformation.pk', sprite='shape_square_edit')
setup_queue_transformation_delete = Link(text=_(u'delete'), view='setup_queue_transformation_delete', args='transformation.pk', sprite='shape_square_delete')
