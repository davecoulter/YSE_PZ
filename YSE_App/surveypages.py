from django.shortcuts import render, get_object_or_404, render_to_response

def survey(request):
	return render(request, 'YSE_App/survey/survey.html')

def news(request):
	return render(request, 'YSE_App/survey/news.html')

def contact(request):
	return render(request, 'YSE_App/survey/contact.html')

def team(request):
	return render(request, 'YSE_App/survey/team.html')
