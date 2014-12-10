from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from projects.models import Project
from builds.models import Version


class DocumentNodeManager(models.Manager):

    def create(self, *args, **kwargs):

        try:
            hash = kwargs.pop('hash')
        except KeyError:
            raise TypeError("You must provide a hash for the initial NodeSnapshot.")

        node = super(DocumentNodeManager, self).create(*args, **kwargs)
        NodeSnapshot.objects.create(hash=hash, node=node)

        return node


class DocumentNode(models.Model):

    objects = DocumentNodeManager()

    project = models.ForeignKey(Project, verbose_name=_('Project'),
                                related_name='nodes', null=True)
    version = models.ForeignKey(Version, verbose_name=_('Version'),
                                related_name='nodes', null=True)
    commit = models.CharField(max_length=255)
    page = models.CharField(_('Path'), max_length=255)

    def __unicode__(self):
        return "node %s on %s for %s" % (self.id, self.page, self.project)

    def save(self, *args, **kwargs):
        pass
        super(DocumentNode, self).save(*args, **kwargs)

    def latest_hash(self):
        return self.snapshots.latest().hash


class NodeSnapshot(models.Model):
    date = models.DateTimeField('Publication date', auto_now_add=True)
    hash = models.CharField(_('Hash'), max_length=255)
    node = models.ForeignKey(DocumentNode, related_name="snapshots")

    class Meta:
        get_latest_by = 'date'


class DocumentComment(models.Model):
    date = models.DateTimeField(_('Date'), auto_now_add=True)
    rating = models.IntegerField(_('Rating'), default=0)
    text = models.TextField(_('Text'))
    user = models.ForeignKey(User)
    node = models.ForeignKey(DocumentNode, related_name='comments')

    def __unicode__(self):
        return "%s - %s" % (self.text, self.node)

    def moderate(self, user, approved):
        self.moderation_actions.create(user=user, approved=approved)

    def has_been_approved_since_most_recent_node_change(self):
        try:
            latest_moderation_action = self.moderation_actions.latest()
        except ModerationAction.DoesNotExist:
            # If we have no moderation actions, obviously we're not approved.
            return False

        most_recent_node_change = self.node.snapshots.latest().date

        if latest_moderation_action.date > most_recent_node_change:
            # If we do have an approval action which is newer than the most recent change,
            # we'll return True or False commensurate with its "approved" attribute.
            return latest_moderation_action.approved
        else:
            return False


class ModerationAction(models.Model):
    user = models.ForeignKey(User)
    comment = models.ForeignKey(DocumentComment, related_name="moderation_actions")
    approved = models.BooleanField(default=True)
    date = models.DateTimeField(_('Date'), auto_now_add=True)

    class Meta:
        get_latest_by = 'date'