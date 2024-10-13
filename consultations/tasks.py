from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from rest_framework.reverse import reverse
from django.utils import timezone

from .models import User, Booked, Consultation


@shared_task
def archive_consultation(consultation_id):
    try:
        consultation = Consultation.objects.get(pk=consultation_id)
        consultation.set_archive()

        booked = Booked.objects.get(consultation=consultation, archive=False, status='Booked')
        booked.successfully()

        print(f"archive consultation {consultation.id}")
        print(f"archive consultation {booked.id}")
    except Consultation.DoesNotExist:
        ...


@shared_task
def task_send_email_booked_create(consultation):
    consultation = Consultation.objects.get(pk=consultation)

    datetime_start = consultation.datetime.lower.strftime('%Y-%m-%d %H:%M')
    datetime_end = consultation.datetime.upper.strftime('%Y-%m-%d %H:%M')

    subject = 'Новая заявка на вашу консультацию!!'
    text = (
        f'Здравствуйте, {consultation.user.username}.\n\n'
        'С радостью сообщаем вам о новой заявке на вашу консультацию, '
        f'которая пройдет в период с {datetime_start} по {datetime_end}.\n\n'
        'С уважением, команда проекта.'
    )
    html = (
        f'Здравствуйте, <b>{consultation.user.username}</b>.<br/><br/>'
        'С радостью сообщаем вам о новой заявке на вашу консультацию, '
        f'которая пройдет в период с {datetime_start} по {datetime_end}.<br/><br/>'
        'С уважением, команда проекта.'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[consultation.user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()


@shared_task
def task_send_email_booked_accept(booked):
    booked = Booked.objects.get(pk=booked)

    datetime_start = booked.consultation.datetime.lower.strftime('%Y-%m-%d %H:%M')
    datetime_end = booked.consultation.datetime.upper.strftime('%Y-%m-%d %H:%M')

    subject = 'Бронь подтвердили!!'
    text = (
        f'Здравствуйте, {booked.user.username}.\n\n'
        'С радостью сообщаем вам, что ваша бронь успешно подтверждена.\n\n'
        f'Консультация пройдет в период с {datetime_start} по {datetime_end}.\n\n'
        'С уважением, команда проекта.'
    )
    html = (
        f'Здравствуйте, <b>{booked.user.username}</b>.<br/><br/>'
        'С радостью сообщаем вам, что ваша бронь успешно подтверждена.<br/><br/>'
        f'Консультация пройдет в период с {datetime_start} по {datetime_end}.<br/><br/>'
        'С уважением, команда проекта.'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[booked.user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()


@shared_task
def task_send_email_booked_cancellation(booked):
    booked = Booked.objects.get(pk=booked)

    subject = 'Бронь отклонена.'
    text = (
        f'Здравствуйте, {booked.user.username}.\n\n'
        'С сожалением вынуждены сообщить, что ваша бронь отклонена.\n\n'
        f'Причина отмены: {booked.rejection_text}.\n\n'
        'С уважением, команда проекта.'
    )
    html = (
        f'Здравствуйте, <b>{booked.user.username}</b>.<br/><br/>'
        'С сожалением вынуждены сообщить, что ваша бронь отклонена.<br/><br/>' 
        f'Причина отмены: {booked.rejection_text}.<br/><br/>'
        'С уважением, команда проекта.'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[booked.user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()