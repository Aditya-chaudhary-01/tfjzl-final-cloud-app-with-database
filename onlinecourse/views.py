from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Submission, Choice, Question
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
         # Get user and course object, then get the associated enrollment object created when the user enrolled the course
         # Create a submission object referring to the enrollment
         # Collect the selected choices from exam form
         # Add each selected choice object to the submission object
         # Redirect to show_exam_result with the submission id
#def submit(request, course_id):


# An example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
   submitted_anwsers = []
   for key in request.POST:
       if key.startswith('choice'):
           value = request.POST[key]
           choice_id = int(value)
           submitted_anwsers.append(choice_id)
   return submitted_anwsers


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
        # Get course and submission based on their ids
        # Get the selected choice ids from the submission record
        # For each selected choice, check if it is a correct answer or not
        # Calculate the total score
#def show_exam_result(request, course_id, submission_id):



def submit(request, course_id):
    # Get the current logged-in user
    user = request.user
    
    # Get the course object from the database using the course_id from the URL
    course = get_object_or_404(Course, pk=course_id)
    
    # Find this user's enrollment for this course
    # We need enrollment because Submission links to Enrollment, not directly to User
    enrollment = Enrollment.objects.get(user=user, course=course)
    
    # Create a new Submission object linked to this enrollment
    submission = Submission(enrollment=enrollment)
    submission.save()
    
    # Get all the choice IDs the user checked from the form
    # request.POST.getlist('choice') returns a list like ['3', '7']
    # because HTML forms send everything as strings
    submitted_choice_ids = request.POST.getlist('choice')
    
    # Loop through each selected choice ID
    for choice_id in submitted_choice_ids:
        # Get the actual Choice object from the database
        choice = Choice.objects.get(pk=choice_id)
        # Add it to the submission's choices (ManyToMany relationship)
        submission.choices.add(choice)
    
    # Save the submission again now that choices are added
    submission.save()
    
    # Redirect to the result page, passing both course_id and submission_id in the URL
    return HttpResponseRedirect(
        reverse('onlinecourse:show_exam_result', args=(course_id, submission.id))
    )


def show_exam_result(request, course_id, submission_id):
    # Get the course and submission objects
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    # Get all the choice IDs from this submission
    # values_list('id', flat=True) gives us a flat list of IDs like [3, 7]
    selected_ids = submission.choices.values_list('id', flat=True)
    
    # Get all questions for this course
    questions = course.question_set.all()
    
    # Calculate total score
    total_score = 0
    
    # For each question, check if the user got it right using our is_get_score method
    # We also need to pass per-question results to the template
    # So we build a list of result dicts
    question_results = []
    
    for question in questions:
        # Get only the choices the user selected FOR THIS question
        # i.e. filter selected_ids to only choices belonging to this question
        selected_for_question = submission.choices.filter(
            question=question
        ).values_list('id', flat=True)
        
        # Use the is_get_score method we wrote in models.py
        correct = question.is_get_score(selected_for_question)
        
        if correct:
            total_score += question.grade
        
        question_results.append({
            'question': question,
            'correct': correct,
            'selected_ids': selected_ids,
        })
    
    # Pass everything to the template
    return render(request, 'onlinecourse/exam_result_bootstrap.html', {
        'course': course,
        'question_results': question_results,
        'total_score': total_score,
    })