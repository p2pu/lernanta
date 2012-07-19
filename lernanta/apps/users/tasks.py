import datetime

from celery.task import Task

from messages.models import Message

class SendPrivateMessages(Task):
    """
    Send a private message to multiple users. ``messages`` should be a sequence
    containing tuples of sender, recipient, subject, body, parent.
    """
    name = 'users.tasks.SendPrivateMessages'

    def run(self, form, messages, **kwargs):
        log = self.get_logger(**kwargs)
        log.debug("Sending email to %d user(s)." % (len(messages),))
        for message in messages:
            (sender, recipient, subject, body, parent) = message
            msg = Message(sender=sender, recipient=recipient,
                          subject=subject, body=body)
            if parent is not None:
                msg.parent_msg = parent
                parent.replied_at = datetime.datetime.now()
                parent.save()
            msg.save()
