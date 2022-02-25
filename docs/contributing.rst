Contributing
************

This page walks you through how to contribute to the development of YSE_PZ.

General workflow
----------------

The normal develop workflow of YSE_PZ is to branch off develop, commit and push
changes, and then merge to the develop branch with a pull request. Finally, after
the pull request has been approved and your changes have been merged you can delete
your branch.

Starting from scratch, the typical development workflow would be the following.
Clone the YSE_PZ git repository

.. code:: none

    git clone https://github.com/davecoulter/YSE_PZ.git

Once in the YSE_PZ directory, checkout the develop branch.

.. code:: none

    git checkout develop

Create your own branch with the following naming convention.

.. code:: none

    git checkout -b develop-<your first name>-<one or two word description of what you are doing>

For example, if you were called Joe and wanted to contribute to documentation on
YSE_PZ your branch might be called develop-joe-docs. Then set the remote of your
new branch to github.

.. code:: none

    git push --set-upstream origin <your branch name>

This means you can push changes to github where they can be saved before you
are ready for a pull request. Now you can make your changes and additions to the
code and push changes to github.

Next go to to the YSE_PZ github repository page and go to the pull requests tab.

.. image:: _static/contributing_pull_request_tab.png

Then open a new draft pull request.

.. image:: _static/contributing_new_pull_request.png

Create a pull request with your branch and develop.

.. image:: _static/contributing_create_pull_request.png

.. image:: _static/contributing_new_draft_pull_request.png

Now as your commit and push changes to your branch on master they will show up
in the draft pull request. When you are a happy for you changes to be reviewed
and then eventually merged into develop, click request review.

.. image:: _static/contributing_ready_for_review.png

After your branch has been merged, delete the branch from your local repository.

.. code:: none

    git branch -d <your branch name>

Then delete the branch from Github.

.. code:: none

    git push -d origin <your branch name>


