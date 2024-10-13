from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from rest_framework.reverse import reverse

from .models import User


@shared_task
def task_send_email_verify_email_user(user):
    user = User.objects.get(pk=user)
    token = user.token()
    absurl = f'http://127.0.0.1:8000{reverse("email_verify")}?token={token}'

    subject = 'Рады приветствовать вас в нашем сервисе консультаций!!'
    text = (
        f'Уважаемый {user.username}, поздравляю вас с успешной регистрацией на нашем сайте!\n\n'
        f'Пожалуйста, воспользуйтесь приведенной ниже ссылкой, чтобы подтвердить свой адрес электронной почты.\n\n'
        f'{absurl}'
    )
    html = (
        f'Уважаемый <b>{user.username}</b>, поздравляю вас с успешной регистрацией на нашем сайте!<br/><br/>'
        f'Пожалуйста, воспользуйтесь приведенной ниже ссылкой, чтобы подтвердить свой адрес электронной почты.<br/><br/>'
        f'<a href="{absurl}">Ссылка</a>'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()


@shared_task
def task_send_email_verify_email_user_success(user):
    user = User.objects.get(pk=user)

    subject = 'Поздравляю с успешным подтверждением почты!!!'
    text = (
        f'{user.username}, поздравляю вас с успешным подтверждением почты!\n\n'
        f'С уважением, команда проекта.\n\n'
    )
    html = (
        f'<b>{user.username}</b>, поздравляю вас с успешным подтверждением почты!<br/><br/>'
        f'С уважением, команда проекта.<br/><br/>'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()


@shared_task
def task_send_email_user_block(user):
    user = User.objects.get(pk=user)

    subject = 'Ваш аккаунт был заблокирован.'
    text = (
        f'{user.username}, ваш аккаунт был заблокирован из-за нарушения правил платформы.\n\n'
        f'С уважением, команда проекта.\n\n'
    )
    html = (
        f'<b>{user.username}</b>, ваш аккаунт был заблокирован из-за нарушения правил платформы.<br/><br/>'
        f'С уважением, команда проекта.<br/><br/>'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()


@shared_task
def task_send_email_user_unblock(user):
    user = User.objects.get(pk=user)

    subject = 'Ваш аккаунт был разблокирован!'
    text = (
        f'{user.username}, с радостью сообщаем вам, что ваш аккаунт был разблокирован!\n\n'
        f'С уважением, команда проекта.\n\n'
    )
    html = (
        f'<b>{user.username}</b>, с радостью сообщаем вам, что ваш аккаунт был разблокирован!<br/><br/>'
        f'С уважением, команда проекта.<br/><br/>'
    )
    msg = EmailMultiAlternatives(
        subject=subject, body=text, from_email=None, to=[user.email]
    )
    msg.attach_alternative(html, "text/html")
    msg.send()