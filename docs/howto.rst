Using the web interface
***********************

This page contains some general how-to's on using the :code:`YSE_PZ`
web interface.

Using the Admin interface
--------------------------

When changing or adding a field, make sure your username is selected in the
‘modified_by’ fields.  This will allow us to keep track of changes and ask
you questions if we’re confused by something.

Changing transient statuses
---------------------------
There is a ‘change transient status’ link in the status section of the detail
page for each object.

If you click, it will take you to the admin page for
that transient.  Remember to select your user name in the modified_by section
before saving

If you changed the transient status to FollowupRequested or
Following, be sure to communicate with the slack channel to make sure everyone
knows what they should be doing to follow the object.
See Adding Followup Requests below.

Adding Followup Requests
------------------------
If you’ve labeled a transient as FollowupRequested, please click the
‘Add Followup Request’ button in the followup section of the transient detail
page.  This will take you to the followup admin page, where you can add a
followup request by selecting the classical or ToO resource that you want to
use for the object followup.

If you want to add further instructions, you can
select the add observation task link, which will take you to an admin page that
lets you specify configurations, exposure times, requested dates, etc.
Select ‘Requested’ as the status.

Recording Observations
----------------------

If you’ve recently observed something:

If no observation task exists, you can create an observation task using the
links in the followup section of the transient detail page.

If an observation task with status ‘requested’ exists, you can use the link in
the followup table to change the status to ‘successful’ and adjust the date
and other fields so that they’re an accurate record of the observation.

After recording the observation, make sure the transient status has been set to
Following using the link near the top of the detail page.
