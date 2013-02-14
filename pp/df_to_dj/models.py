from django.db import models

# Create your models here.
class MyModel(models.Model):
    name1 = models.CharField(max_length=128, default='LEX')
    name2 = models.CharField(max_length=128)
    name3 = models.CharField(max_length=128, null=True)
    foobar = models.IntegerField()

    def __unicode__(self):
        return "%s, %s, %s => %s" % (self.name1, self.name2, self.name3, self.foobar)

    def save(self, *args, **kwargs):
        print 'SAVE CALLED', '^' * 22
        super(MyModel, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('name1', 'name2',)
