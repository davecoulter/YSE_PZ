from rest_framework import mixins
from rest_framework.generics import GenericAPIView

from YSE_App.common import custom_mixins

class RetrieveUpdateAPIView(mixins.RetrieveModelMixin,
							custom_mixins.UpdateModelMixin,
							GenericAPIView):
	"""
	Concrete view for retrieving, updating a model instance.
	"""
	def get(self, request, *args, **kwargs):
		return self.retrieve(request, *args, **kwargs)

	def put(self, request, *args, **kwargs):
		return self.update(request, *args, **kwargs)

	def patch(self, request, *args, **kwargs):
		return self.partial_update(request, *args, **kwargs)