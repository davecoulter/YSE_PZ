from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class BaseModel(models.Model):
    """
	Base model to track and audit changes to data models in YSE_PZ.


	Attributes:
		created_by (models.ForeignKey): YSE_PZ User that created the data model.
		created_date (model.DateTimeField): Date the YSE_PZ User created the data model.
		modified_by (models.ForeignKey): The last YSE_PZ User to modify the data model.
		modified_date (models.DateTimeField): The last time a YSE_PZ User mofified the data model.
	"""

    class Meta:
        abstract = True

        # Audit fields

    created_by = models.ForeignKey(
        User, related_name="%(class)s_created_by", on_delete=models.PROTECT
    )
    created_date = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(
        User, related_name="%(class)s_modified_by", on_delete=models.PROTECT
    )
    modified_date = models.DateTimeField(auto_now=True)
