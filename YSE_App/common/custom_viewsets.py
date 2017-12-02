from rest_framework import mixins
from rest_framework import viewsets

from YSE_App.common import custom_mixins

class ListCreateRetrieveUpdateViewSet(mixins.CreateModelMixin,
						mixins.RetrieveModelMixin,
						mixins.UpdateModelMixin,
						mixins.ListModelMixin,
						custom_mixins.UpdateModelMixin,
						viewsets.GenericViewSet):
	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user, modified_by=self.request.user)

	def perform_update(self, serializer):
		serializer.save(modified_by=self.request.user.id)

	def perform_partial_update(self, serializer):
		serializer.save(modified_by=self.request.user.id)