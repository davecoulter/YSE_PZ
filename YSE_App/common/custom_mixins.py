"""
Basic building blocks for generic class based views.
We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""
from __future__ import unicode_literals
from rest_framework.response import Response


class UpdateModelMixin(object):
    """
	Update a model instance.
	"""

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        self.perform_update(serializer)

        # Hack - for some reason after TransientSerializer performs
        # an update, it's `data` property contains object representations
        # of PrimaryKeyRelatedField members. These cannot be serialized
        # in the Response. Instead, I "re-serialize" the data :(
        serializer = self.get_serializer(serializer.data)
        print(serializer.data)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
