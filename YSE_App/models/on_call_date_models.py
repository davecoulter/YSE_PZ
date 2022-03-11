from django.db import models
from YSE_App.models.base import *
from django.contrib.auth.models import User


class OnCallDate(BaseModel):
    ### Entity relationships ###
    # Optional
    user = models.ManyToManyField(User, blank=True)

    ### Properties ###
    # Required
    on_call_date = models.DateTimeField()

    def __str__(self):
        user_str = ""
        users = self.user.all()
        for user in users:
            user_str += user.username + ", "
        return "Date: %s - On Call: %s" % (
            self.on_call_date.strftime("%m/%d/%Y"),
            user_str,
        )


class YSEOnCallDate(BaseModel):
    ### Entity relationships ###
    # Optional
    user = models.ManyToManyField(User, blank=True)

    ### Properties ###
    # Required
    on_call_date = models.DateTimeField()

    def __str__(self):
        user_str = ""
        users = self.user.all()
        for user in users:
            user_str += user.username + ", "
        return "Date: %s - On Call: %s" % (
            self.on_call_date.strftime("%m/%d/%Y"),
            user_str,
        )
