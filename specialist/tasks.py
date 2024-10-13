from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from rest_framework.reverse import reverse

from .models import User, Candidates, Specialist


@shared_task
def task_send_email_candidates_accept(candidates):
    candidates = Candidates.objects.get(pk=candidates)

    subject = 'Рады приветствовать вас в рядах специалистов.!!'
    text = (
        f'Здравствуйте, {candidates.user.username}.\n\n'
        'С радостью сообщаем вам, что ваша регистрация на роль специалиста прошла успешно. '
        'Теперь вы можете проводить консультации.\n\n'
        'С уважением, команда проекта.'
    )
    html = (
        f'Здравствуйте, <b>{candidates.user.username}</b>.<br/><br/>'
        'С радостью сообщаем вам, что ваша регистрация на роль специалиста прошла успешно. '
        'Теперь вы можете проводить консультации.<br/><br/>'
        'С уважением, команда проекта.'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[candidates.user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()


@shared_task
def task_send_email_candidates_cancel(candidates):
    candidates = Candidates.objects.get(pk=candidates)

    subject = 'Вашу регистрацию отклонили.'
    text = (
        f'Здравствуйте, {candidates.user.username}.\n\n'
        'Вашу регистрацию на специалиста отклонили.\n'
        'Вы можете отправить заявку повторно.\n\n'
        f'Ответ: {candidates.rejection_text}.\n\n'
        'С уважением, команда проекта.'
    )
    html = (
        f'Здравствуйте, <b>{candidates.user.username}</b>.<br/><br/>'
        'Вашу регистрацию на специалиста отклонили.<br/>'
        'Вы можете отправить заявку повторно.<br/><br/>'
        f'Ответ: {candidates.rejection_text}.<br/><br/>'
        'С уважением, команда проекта.'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[candidates.user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()


@shared_task
def task_send_email_specialist_block(specialist):
    specialist = Specialist.objects.get(pk=specialist)

    subject = 'Вы больше не являетесь специалистом.'
    text = (
        f'Здравствуйте, {specialist.user.username}.\n\n'
        'К сожалению, в связи с нарушением правил сообщества, ваша роль специалиста была аннулирована.\n\n'
        'С уважением, команда проекта.'
    )
    html = (
        f'Здравствуйте, <b>{specialist.user.username}</b>.<br/><br/>'
        'К сожалению, в связи с нарушением правил сообщества, ваша роль специалиста была аннулирована.<br/><br/>'
        'С уважением, команда проекта.'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[specialist.user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()


@shared_task
def task_send_email_specialist_unblock(specialist):
    specialist = Specialist.objects.get(pk=specialist)

    subject = 'Вы больше не являетесь специалистом.'
    text = (
        f'Здравствуйте, {specialist.user.username}.\n\n'
        'С радостью хотим сообщить, что вам вернули роль специалиста!\n'
        'Теперь вы вновь сможете проводить консультации.\n\n'
        'С уважением, команда проекта.'
    )
    html = (
        f'Здравствуйте, <b>{specialist.user.username}</b>.<br/><br/>'
        'С радостью хотим сообщить, что вам вернули роль специалиста!<br/>'
        'Теперь вы вновь сможете проводить консультации.<br/><br/>'
        'С уважением, команда проекта.'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[specialist.user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()